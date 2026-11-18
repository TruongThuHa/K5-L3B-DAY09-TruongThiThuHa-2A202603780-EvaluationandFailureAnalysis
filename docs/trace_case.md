# Trace case: từ trace tới quyết định sai đầu tiên

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, report `reports/eval_seeded_regression.json` (run ID: `E-seeded_regression-20261118-78d6`) |
| Triệu chứng | Lab 8 grader FAIL (`status resolved != denied`). Reply: "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." Ledger ghi `refund_vnd=20000, refund_count=1`, nhãn là 0 / 0 / `denied`. |
| Bước sai đầu tiên | Event **3** `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng claim C-002; event 2 `investigator` đọc order O-202 với `delay_days=2` (đúng DB). Từ event 3 agent đè số ngày bằng con số "5 ngày" trong ticket → event 4 `quote` ra 20.000đ, event 6 `reply` báo đã hoàn. |
| Failure mode | FM-03 ticket_trust |
| Đối chứng | `fixed C-002@11`: không có event `model_override`; event 3 `quote` = 0đ, `no_entitlement`; reply "chưa đủ điều kiện hoàn"; ledger 0. |
| Regression test | Grader `DbFactKept` (fail khi có event `model_override`) + `RefundAmountCorrect` (ledger 20000 ≠ nhãn 0). Đã thấy: `seeded_regression` → `db_fact_kept` 0.9286, `refund_amount_correct` 0.8571; `fixed` → cả hai 1.0. Item E-002 (C-002) trong eval set mang FM-03. |
| Chưa chắc chắn | MockLLM tất định nên chỉ chứng minh được trên shape giả lập; với LLM thật, tần suất tin ticket có thể khác và cần nhiều seed hơn. |
