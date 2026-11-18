# Hướng dẫn Lab 9 — Advanced + Expert (M5–M7) · VS Code trên Mac

> Mục tiêu: thêm **40 điểm** (Advanced 25 + Expert 15). Thời gian khoảng 45–60 phút, phần lớn là chờ máy chạy.
> Mở file này trong VS Code, bấm **Cmd + Shift + V** để xem dạng đẹp.

---

## PHẦN 0 · Hiểu bài trong 3 phút

Gate ở Core chỉ chặn được **lỗi rõ ràng**. Ngoài đời có 3 kiểu khó hơn:

| Bài | Tình huống thật | Cách gate xử lý |
|---|---|---|
| **M5 — Slice** | Lỗi chỉ xảy ra ở **nhóm nhỏ** (ví dụ các claim có hoàn tiền). Tính trung bình cả bài vẫn đẹp. | Chấm riêng từng nhóm (slice): `money_movement`, `adversarial`, `denial`, `escalation`. Nhóm nào dưới sàn thì chặn. |
| **M5 — Eval set v2** | Khách cố lừa agent: chèn lệnh vào ticket, giả làm admin, hỏi đơn của người khác. | Thêm 14 câu "tấn công" của giảng viên. Mỗi câu dùng một **cơ chế**, bạn ánh xạ cơ chế đó sang mã FM của bạn (`fm_map.yaml`). |
| **M6 — Chập chờn** | Agent đúng 4/5 lần, sai 1/5 lần. | Đo **pass^k** (pass_hat_k) = xác suất **cả k lần** chạy đều đúng. Đặt sàn `pass_hat_5 ≥ 0.80`, chọn sàn sau khi đo nhiễu **A/A** (cùng agent, 2 bộ seed khác nhau). |
| **M7 — Gian lận report** | Người viết PR "làm đẹp" report: xóa dòng fail, chỉ giữ seed đẹp, biến lỗi thành NaN, hạ ngưỡng. | `integrity_check`: không tin report có dấu hiệu bị sửa, chặn luôn. |

Ví dụ thật từ bài của bạn: `slice_regression` có pass_rate tổng 0.936 nên **qua** gate cũ. Nhưng riêng nhóm `money_movement` chỉ 0.85, thấp hơn sàn 0.95, nên gate mới **chặn**.

**File mình gửi kèm** (tải hết về Downloads, giữ nguyên tên):
- Code: `stats.py`, `gate.py`, `fm_map.yaml`, `metric_spec_v2.yaml` (đã chạy qua test và scorecard)
- Docs để nối vào cuối file cũ: `taxonomy_v2_them.md`, `eval_card_v2_them.md`

⚠️ `stats.py` lần này là bản **mới** (thêm M6). Nếu Downloads còn `stats.py` cũ từ phần Core, xóa file cũ trước rồi mới tải, để Mac không đổi tên thành `stats (1).py`.

---

## PHẦN 1 · Chuẩn bị

### Bước 1.1 — Kiểm tra đã tải đủ 6 file
Mở VS Code → **Terminal → New Terminal**, dán:
```bash
ls -la ~/Downloads | grep -E " (stats\.py|gate\.py|fm_map\.yaml|metric_spec_v2\.yaml|taxonomy_v2_them\.md|eval_card_v2_them\.md)$"
```
✅ Đủ khi in ra **6 dòng**. Dòng `stats.py` phải có giờ tải là **hôm nay, vừa xong** (cột thời gian), không phải bản tải lúc sáng.

### Bước 1.2 — Tạo nhánh mới từ main
Bài Core đã merge vào `main`, nên làm Advanced trên một nhánh mới:
```bash
cd ~/AI20K/day9/lab9
git switch main
git pull
git switch -c advanced/d09
cd src && source .venv/bin/activate
```
✅ Dòng lệnh có `(.venv)` ở đầu, và lệnh `git branch` (gõ thử) có dấu `*` ở `advanced/d09`.
> Nếu `git pull` báo lỗi `File exists` / `.lock`: chạy `ls ../.git/*.lock` rồi chụp màn hình gửi mình.

---

## PHẦN 2 · M6 + M7 code — pass^k và integrity_check

### Bước 2.1 — Chép 2 file code
```bash
cp ~/Downloads/stats.py lab9/stats.py
cp ~/Downloads/gate.py lab9/gate.py
```
Mở xem để hiểu (Cmd + P, gõ tên file):
- `stats.py` → cuối file: `pass_at_k` = "**ít nhất 1** trong k lần đúng", `pass_hat_k` = "**cả k** lần đều đúng". `_check_nck` từ chối đầu vào vô lý (k > n, c > n…) bằng lỗi rõ ràng.
- `gate.py` → `integrity_check`: 6 kiểu kiểm tra (NaN, thiếu/trùng dòng, seed bị chọn lọc, grader crash, ngưỡng bị nới, nhãn slice bị đổi). `slice_check`: chấm từng nhóm.

### Bước 2.2 — Chạy test Advanced
```bash
python -m pytest -q -m student -o addopts= -k advanced
```
✅ Mong đợi: `12 passed`

---

## PHẦN 3 · M5 — Eval set v2

### Bước 3.1 — Ánh xạ cơ chế tấn công → mã FM
```bash
cp ~/Downloads/fm_map.yaml config/fm_map.yaml
python -m lab9.evalset --v2 --build
```
✅ Mong đợi:
```
wrote data/eval/eval_set_v2.jsonl (28 items) and data/eval/labels_v2.json (28 labels)
eval set v2 356c0ebe29fa: 0 problem(s)
```
Mở `config/fm_map.yaml`: 8 cơ chế, mỗi cơ chế ứng với một FM. Cơ chế `cross_principal` (khách hỏi đơn của người khác) chưa có trong taxonomy v1, nên mình thêm **FM-09** mới. Luật v2: mỗi FM bị tấn công phải có **≥ 3 item**.

### Bước 3.2 — Spec v2 + baseline v2
```bash
cp ~/Downloads/metric_spec_v2.yaml config/metric_spec_v2.yaml
python -m lab9.eval --shape swarm --spec config/metric_spec_v2.yaml --out reports/baseline_v2.json
```
✅ Mong đợi (chờ khoảng 1 phút): dòng đầu `E-swarm-2026xxxx-356c · … 28 item × 5 seed`, có `pass_hat_5 0.8929` và dòng cuối `wrote reports/baseline_v2.json`.
Mở `config/metric_spec_v2.yaml`, kéo xuống cuối để xem: metric mới `pass_hat_5` (sàn 0.80), `reply_matches_ledger` (FM-08), và 5 slice.

---

## PHẦN 4 · M6 — Đo nhiễu A/A
Chạy cùng agent `swarm` trên 2 bộ seed khác nhau. Độ chênh giữa hai lần chạy chính là "nhiễu tự nhiên". Sàn phải đặt **ngoài** dải nhiễu, nếu không gate sẽ chặn nhầm PR tốt một cách ngẫu nhiên.
```bash
python -m lab9.mutation --spec config/metric_spec_v2.yaml --aa 66,77,88,99,110
```
✅ Mong đợi: cột `delta` toàn là `+0.0000` (MockLLM tất định, không có nhiễu). Swarm `pass_hat_5` = 0.8929, bản chập chờn `flaky_regression` = 0.5714, nên sàn **0.80** nằm giữa hai số này.

---

## PHẦN 5 · Scorecard — chạy mọi variant qua gate của bạn (mất 3–5 phút)
```bash
python -m lab9.mutation --spec config/metric_spec_v2.yaml --baseline reports/baseline_v2.json
```
✅ Mong đợi:
```
  fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok   ...
  slice_regression     expect block got block ok   slice:money_movement/pass_rate, ...
  flaky_regression     expect block got block ok   pass_rate, pass_hat_5, ...
mutation score 3/3 · false alarms 0
```
"3/3" nghĩa là chặn hết 3 bản lỗi, "false alarms 0" nghĩa là không chặn nhầm 2 bản tốt.

---

## PHẦN 6 · M7 — Bẫy gian lận report

### Bước 6.1 — Sinh report của bản lỗi slice
```bash
python -m lab9.eval --shape slice_regression --spec config/metric_spec_v2.yaml --out reports/eval_slice_regression.json
```

### Bước 6.2 — Thử 4 cách "làm đẹp" report
```bash
python -m lab9.traps --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```
✅ Mong đợi: 4 dòng `trap … blocked` và dòng cuối `exit 0 — the gate blocked every public trap`.

### Bước 6.3 — Xem tận mắt slice gate (để demo)
```bash
python -m lab9.gate --pr reports/eval_slice_regression.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml
```
Đọc kết quả: dòng `pass_rate` tổng ghi **ok**, nhưng `slice:money_movement/pass_rate 0.85` ghi **BLOCK**. Đây chính là ý nghĩa của M5.

---

## PHẦN 7 · Cập nhật docs
Nối 2 phần mới vào **cuối** file docs cũ (không xóa nội dung cũ):
```bash
cat ~/Downloads/taxonomy_v2_them.md >> ../docs/failure_taxonomy.md
cat ~/Downloads/eval_card_v2_them.md >> ../docs/eval_card.md
```
Mở 2 file đó, kéo xuống cuối để đọc phần mới. Trong `eval_card.md`, nếu run ID ở Bước 3.2 **khác ngày** `20261118` thì sửa lại dòng `E-swarm-20261118-356c` cho đúng.

---

## PHẦN 8 · Commit, push, mở PR, merge

### Bước 8.1 — Commit và push
```bash
git add -A
git add -f reports/*.json
git commit -m "feat: M5-M7 eval set v2, slice gate, pass^k, integrity check"
git push -u origin advanced/d09
```

### Bước 8.2 — Mở PR
Dán link này vào Chrome:
```
https://github.com/TruongThuHa/K5-L3B-DAY09-TruongThiThuHa-2A202603780-EvaluationandFailureAnalysis/compare/main...advanced/d09
```
Kiểm tra dòng trên cùng: `base: main ← compare: advanced/d09`, repo là của bạn. Bấm **Create pull request**, điền Title `Lab 9: M5-M7 advanced + expert`, ô mô tả dán output của Phần 5 (scorecard), rồi bấm **Create pull request**.

### Bước 8.3 — Chờ CI rồi merge
Lần này Actions đã bật sẵn, nên tab **Checks** sẽ chạy ngay. Có **2 job** cần xanh ✅:
- **eval-gate** (Core, như lần trước)
- **eval-gate-v2** (lần này **phải chạy**, không còn *skipped*, vì đã có `baseline_v2.json`). Job này mất 5–10 phút.

Cả hai xanh thì bấm **Merge pull request**, rồi **Confirm merge**. Có job đỏ thì bấm **Details** và chụp màn hình gửi mình.

Link nộp LMS vẫn là link repo cũ, không cần nộp lại nếu LMS đã có link.

---

## PHẦN 9 · Tự chấm điểm

| Hạng mục | Điểm | Tự kiểm: đạt khi thấy | Ước tính |
|---|---|---|---|
| M6 pass_at_k / pass_hat_k | 5 | `12 passed` (test công khai) | 5 (bộ chấm còn dùng vector ẩn) |
| M5 fm_map + `evalset --v2` sạch | 6 | `0 problem(s)` | 6 |
| Spec v2: pass_hat_5 + slice money_movement, adversarial chặn | 4 | có trong `metric_spec_v2.yaml`, đều `blocking: true` | 4 |
| Chặn slice_regression + 1 slice regression ẩn | 6 | scorecard chặn slice_regression | 4–6 |
| Chặn lỗi FM-08 ẩn | 2 | `reply_matches_ledger` có trong spec v2 | 2 |
| Không báo nhầm (fixed, honest_refactor + 1 ẩn) | 2 | `false alarms 0` | 2 |
| **Advanced** | **25** | | **~23–25** |
| M7 chặn 4 trap công khai + 2 trap ẩn | 9 | traps `exit 0` | 6–9 |
| Chặn flaky + variant ẩn không để lại event override; baseline tự so vẫn merge; A/A = 0; sàn pass_hat_5 ≥ 0.8 | 6 | scorecard 3/3, baseline tự so merge, A/A delta 0 | 3–6 |
| **Expert** | **15** | | **~9–15** |

Cộng với Core (~54–60), tổng dự kiến **khoảng 86–100**.

Lệnh tự kiểm tra một lượt (đứng ở thư mục `src`):
```bash
python -m pytest -q -m student -o addopts= -k advanced
python -m lab9.evalset --v2
python -m lab9.gate --pr reports/baseline_v2.json --baseline reports/baseline_v2.json --spec config/metric_spec_v2.yaml --base-spec config/metric_spec_v2.yaml
```
✅ Lần lượt: `12 passed` · `0 problem(s)` · `exit 0 — merge` (baseline so với chính nó phải được merge).

---

## Câu hỏi giảng viên hay hỏi
- *Vì sao cần slice gate?* → slice_regression làm pass_rate tổng 0.936 (vẫn qua), riêng nhóm có hoàn tiền tụt còn 0.85. Trung bình che mất lỗi.
- *Sàn pass_hat_5 = 0.80 lấy từ đâu?* → A/A cho Δ = 0, swarm đạt 0.893, flaky 0.571. Sàn nằm giữa hai số và ngoài dải nhiễu.
- *pass@k khác pass^k thế nào?* → pass@k = "thử k lần, **có ít nhất 1** lần đúng" (lạc quan). pass^k = "**cả k** lần đều đúng" (đo độ tin cậy). Với khách hàng thật, pass^k mới là con số quan trọng.
- *Vì sao gate từ chối report có NaN?* → So sánh `nan < 0.85` luôn trả về False, nên gate ngây thơ sẽ cho qua. Report có lỗ hổng thì không được dùng để quyết định merge.
- *Giới hạn?* → Lỗi chỉ ở 1/5 seed, hoặc hỏng đúng y như baseline vốn đã hỏng, thì không bắt ổn định được với 5 seed. A/A = 0 chỉ đúng với MockLLM.
