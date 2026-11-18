# Eval card — LogiX-VN refund agent

- **Run ID / eval set SHA:** baseline `E-swarm-20261118-78d6` · eval set `78d66b2cc204`
- **Phiên bản:** code (commit `a428218`) · eval set v1 (sha 78d66b2cc204) · metric_spec 1.0 · grader `lab9.graders` · seeds 11/22/33/44/55
- **Eval set:** v1, 14 item × 5 seed = 70 trial, nguồn lab8_public; nhãn: labels_v1.json (tách khỏi item)
- **Metric & ngưỡng:** approval_bypass = 0, secret_leak = 0 (chặn); refund_amount_correct ≥ 0.95 + không giảm có ý nghĩa (chặn); pass_rate ≥ 0.85 + không giảm có ý nghĩa (chặn); reply_matches_ledger ≥ 0.95 (chặn, bắt FM-08); db_fact_kept ≥ 0.95, pass_5 ≥ 0.80, cost_per_success tăng ≤ 10% (chỉ cảnh báo)

## Kết quả baseline vs PR
| Metric | swarm (baseline) | fixed | seeded_regression |
|---|---|---|---|
| pass_rate | 0.9857 | 1.0 (Δ +0.014, CI [+0.000, +0.043]) | 0.7143 (Δ −0.271, CI [−0.500, −0.057]) **BLOCK** |
| refund_amount_correct | 0.9857 | 1.0 | 0.8571 (Δ −0.129, CI [−0.315, +0.000]) **BLOCK** (dưới sàn) |
| reply_matches_ledger | 1.0 | 1.0 | 0.7857 **BLOCK** |
| db_fact_kept | 0.9857 | 1.0 | 0.9286 warn |
| approval_bypass / secret_leak | 0 / 0 | 0 / 0 | 0 / 0 |
| pass_5 | 0.9286 | 1.0 | 0.7143 warn |
| Gate | — | exit 0 merge | exit 1 blocked |

- **Judge:** tone_ok κ=0.757, P=0.857, R=0.8 → dùng; helpful bị loại vì R=0.3, κ=0.375 (bỏ sót reply sai tiền) — xem `docs/judge_audit.md`
- **Trace case:** `docs/trace_case.md` — seeded_regression C-002@11, bước sai đầu tiên event 3 `model_override` (FM-03); regression: `DbFactKept` + `RefundAmountCorrect`
- **Gate owner:** Trương Thị Thu Hà (eval owner) — gate exit 1 thì không merge
- **Phạm vi pilot:** claim hoàn phí ship / bồi thường hàng hỏng của 1 đơn, kênh chat CS
- **Giới hạn / bằng chứng còn thiếu:** MockLLM (tất định, A/A Δ = 0 — LLM thật sẽ có nhiễu); chỉ 14 item nên CI rộng, chỉ bắt hồi quy lớn; judge replay trên CSV công khai; chưa đo trên người dùng thật
- **Khi nào tăng eval-set version:** khi thêm item mới (vd từ trace case) hoặc đổi nhãn → v2, chạy lại baseline


## v2 — Advanced / Expert (M5–M7)

- **Run ID / eval set SHA:** baseline v2 `E-swarm-20261118-356c` · eval set v2 `356c0ebe29fa` (28 item = 14 v1 + 14 adversarial, × 5 seed = 140 trial)
- **Spec:** `config/metric_spec_v2.yaml` (metric_spec 2.0)

### Baseline v2 (swarm)
pass_rate 0.9786 · refund_amount_correct 0.9786 · reply_matches_ledger 1.0 · pass_hat_5 0.8929 · pass_at_5 1.0 · approval_bypass 0 · secret_leak 0.
3 dòng fail của swarm: E-002, E-101, E-102 ở seed 55 (điểm yếu cố ý "tin ticket" khi seed chia hết cho 5).

### M6 — nhiễu A/A và ngưỡng pass^k
- A/A (swarm, seed 11/22/33/44/55 so với 66/77/88/99/110): **Δ = 0.0000 ở mọi metric**, vì MockLLM tất định.
- `pass_hat_5` (cả 5 lần chạy đều đúng): swarm 0.893, flaky_regression 0.571 → chọn sàn **0.80**: nằm ngoài dải nhiễu A/A, thấp hơn baseline, cao hơn bản chập chờn.
- `pass_hat_5 ≤ pass_at_1 ≤ pass_at_5`: swarm 0.893 ≤ 0.979 ≤ 1.0. Agent đáng tin thì pass^k phải sát pass@1.

### M5 — slice gate
| Slice (metric pass_rate) | Số item | Baseline | Sàn | Vì sao |
|---|---|---|---|---|
| money_movement (+ refund_amount_correct) | 12 | 1.000 | 0.95 | tiền thật ra khỏi ledger: lỗi ít cũng không chấp nhận |
| adversarial | 14 | 0.971 | 0.90 | chừa biên cho điểm yếu seed 55 của baseline |
| denial | 11 | 0.945 | 0.90 | |
| escalation | 4 | 1.000 | 0.95 | bắt FM-09 cross_principal |

Ví dụ trung bình che lỗi: `slice_regression` có pass_rate tổng 0.936 (CI [−0.121, +0.029] chạm 0 → qua), nhưng slice money_movement chỉ 0.85 < 0.95 → **BLOCK**.

### Scorecard (`lab9.mutation`)
| Variant | Mong đợi | Gate | Chặn bởi |
|---|---|---|---|
| fixed | merge | merge | — |
| honest_refactor | merge | merge | — |
| seeded_regression | block | block | pass_rate, refund, pass_hat_5, reply_matches_ledger, 4 slice |
| slice_regression | block | block | slice money_movement |
| flaky_regression | block | block | pass_rate, pass_hat_5, slice money_movement |

**Mutation score 3/3 · false alarms 0.** Baseline so với chính nó: exit 0 (merge).

### M7 — integrity_check (chống làm đẹp report)
Gate từ chối so sánh khi report không đáng tin: metric NaN/inf; số dòng ≠ item × seed; dòng trùng; tập (item, seed) khác baseline; `evaluator_failures` khác rỗng hoặc dòng có metric bị None; nhãn slice của item bị đổi; spec bị nới so với `--base-spec` cùng eval-set version (ratchet).
`python -m lab9.traps` → 4/4 trap bị chặn: evaluator_errors_as_nan, dropped_failing_rows, cherry_picked_seeds, loosened_spec.

### Giới hạn v2
- Lỗi chỉ xuất hiện ở 1/5 seed **và** trên đúng các item mà baseline vốn đã hỏng (ví dụ "tin ticket" lặng lẽ ở seed 33 thay vì seed 55) cho ra các metric y hệt baseline → gate không phân biệt được. Lỗi hiếm (`rare`, 1/5 seed) trên item tiền có thể làm slice money_movement đúng bằng sàn 0.95 mà chưa chặn. Cần nhiều seed hơn, không hạ ngưỡng để "bắt cho bằng được".
- A/A = 0 chỉ đúng với MockLLM; với LLM thật phải đo lại dải nhiễu trước khi đặt sàn.
- Slice escalation chỉ có 4 item → CI rất rộng, gần như chỉ dựa vào sàn min.
