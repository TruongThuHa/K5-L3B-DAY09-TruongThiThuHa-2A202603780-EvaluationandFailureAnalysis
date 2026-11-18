"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def _is_bad_number(v) -> bool:
    return isinstance(v, float) and (math.isnan(v) or math.isinf(v))


def _pairs(rep: dict) -> list[tuple[str, int]]:
    return [(r.get("item_id"), r.get("seed")) for r in rep.get("rows", [])]


def _graded_ids(spec: dict, base: dict) -> list[str]:
    """Spec metrics that are scored per row (the baseline's rows carry a column for them)."""
    cols = set().union(*(r.keys() for r in base.get("rows", []))) if base.get("rows") else set()
    return [m["id"] for m in spec.get("metrics", []) if m["id"] in cols]


def _ratchet(spec: dict, base_spec: dict) -> list[str]:
    """Same eval-set version => every threshold may only get stricter."""
    if spec.get("eval_set_version") != base_spec.get("eval_set_version"):
        return []                                   # new eval set: new baseline, thresholds start over
    problems: list[str] = []

    def compare(where: str, old: dict, new: dict | None) -> None:
        if new is None:
            problems.append(f"ratchet: {where} was removed")
            return
        if old.get("blocking") and not new.get("blocking"):
            problems.append(f"ratchet: {where} is no longer blocking")
        ot, nt = old.get("threshold", old), new.get("threshold", new)
        if "min" in ot and ("min" not in nt or nt["min"] < ot["min"]):
            problems.append(f"ratchet: {where} min {ot['min']} -> {nt.get('min')}")
        for key in ("max", "max_increase"):
            if key in ot and (key not in nt or nt[key] > ot[key]):
                problems.append(f"ratchet: {where} {key} {ot[key]} -> {nt.get(key)}")
        if ot.get("no_significant_drop") and not nt.get("no_significant_drop"):
            problems.append(f"ratchet: {where} dropped no_significant_drop")

    new_metrics = {m["id"]: m for m in spec.get("metrics", [])}
    for m in base_spec.get("metrics", []):
        compare(f"metric {m['id']}", m, new_metrics.get(m["id"]))
    new_slices = {(s["name"], s["metric"]): s for s in spec.get("slices") or []}
    for s in base_spec.get("slices") or []:
        compare(f"slice {s['name']}/{s['metric']}", s, new_slices.get((s["name"], s["metric"])))
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate."""
    problems: list[str] = []
    # 1. NaN / inf: "nan < min" is False, so a naive gate lets it through.
    for k, v in (pr.get("metrics") or {}).items():
        if _is_bad_number(v):
            problems.append(f"metric {k} is {v}")
    # 2. Row count must equal items x seeds (dropped or duplicated rows).
    man = pr.get("manifest", {})
    want = man.get("items", 0) * len(man.get("seeds") or [])
    rows = pr.get("rows", [])
    if len(rows) != want:
        problems.append(f"{len(rows)} rows, manifest says {man.get('items')} items x {len(man.get('seeds') or [])} seeds = {want}")
    pairs = _pairs(pr)
    if len(set(pairs)) != len(pairs):
        problems.append("duplicated (item_id, seed) rows")
    # 3. Same (item, seed) set as the baseline: no cherry-picked seeds or items.
    if set(pairs) != set(_pairs(base)):
        missing, extra = set(_pairs(base)) - set(pairs), set(pairs) - set(_pairs(base))
        problems.append(f"(item, seed) set differs from baseline: {len(missing)} missing, {len(extra)} extra")
    if man.get("items") != base.get("manifest", {}).get("items") or \
            sorted(man.get("seeds") or []) != sorted(base.get("manifest", {}).get("seeds") or []):
        problems.append("manifest items/seeds differ from the baseline's")
    # 4. Crashed graders: reported failures, or a graded value that silently became None.
    if pr.get("evaluator_failures"):
        problems.append(f"{len(pr['evaluator_failures'])} evaluator failure(s)")
    for mid in _graded_ids(spec, base):
        n_none = sum(1 for r in rows if r.get(mid) is None)
        if n_none:
            problems.append(f"{n_none} row(s) have no value for graded metric {mid}")
    # 5. Ratchet: the PR may not loosen the spec it is judged by.
    if base_spec is not None:
        problems += _ratchet(spec, base_spec)
    # 6. Slice tags come from labels, so an item's tags may not change between baseline and PR.
    base_tags = {r["item_id"]: sorted(r.get("slices") or []) for r in base.get("rows", [])}
    relabelled = sorted({r["item_id"] for r in rows
                         if r.get("item_id") in base_tags and sorted(r.get("slices") or []) != base_tags[r["item_id"]]})
    if relabelled:
        problems.append(f"slice tags changed for {', '.join(relabelled[:5])}")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for s in spec.get("slices") or []:
        name, metric = s["name"], s["metric"]
        sid = f"slice:{name}/{metric}"
        a = per_item(pr, metric, slice_name=name)
        b = per_item(base, metric, slice_name=name)
        verdict, note, val = "ok", "", None
        if not a:
            verdict = "missing"                 # an empty slice proves nothing: never a silent pass
        else:
            val = round(sum(a.values()) / len(a), 4)
            if "min" in s and val < s["min"]:
                verdict = "fail"
            if s.get("no_significant_drop"):
                keys = sorted(set(a) & set(b))
                if not keys:
                    verdict = "missing"
                else:
                    d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                                       n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
                    note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                    if hi < 0:
                        verdict = "fail"
        if verdict != "ok" and s.get("blocking"):
            blocked.append(sid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if s.get("blocking") else "warn")
        th = {k: s[k] for k in ("min", "no_significant_drop") if k in s}
        lines.append(f"  {sid:<34} {val!s:<8} {json.dumps(th):<30} {note:<28} {label}  ({len(a)} items)")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
