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
