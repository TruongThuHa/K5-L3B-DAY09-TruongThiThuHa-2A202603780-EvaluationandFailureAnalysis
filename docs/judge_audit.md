# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có | **dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không (κ và R dưới sàn) | **loại** |

Ma trận nhầm lẫn (FAIL = dương tính):
- tone_ok: tp=24, fp=4, fn=6, tn=66. Tỉ lệ fail quan sát 0.28 → hiệu chỉnh Rogan-Gladen 0.30.
- helpful: tp=9, fp=0, fn=21, tn=70. Tỉ lệ fail quan sát 0.09 → hiệu chỉnh 0.30.

## ≥5 case audit thủ công (tone_ok)
| # | Case | Judge nói | Người nói | Ai đúng? | Sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha…" | PASS | FAIL | Người | Thêm: xưng "em/anh", "nha" với khách là quá suồng sã → FAIL |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn…" | PASS | FAIL | Người | Thêm: luôn xưng "anh/chị", không gọi "bạn" |
| 3 | H-029 "…không cần nhắn thêm." | PASS | FAIL | Người | Thêm: câu mệnh lệnh/cắt ngang khách → FAIL dù có "Dạ, vui lòng" |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ…" | FAIL | PASS | Người | Ghi rõ: KHÔNG bắt buộc xin lỗi khi đã giải quyết xong |
| 5 | H-051 "…đã refund 90.000đ…" | FAIL | PASS | Người | Ghi rõ: từ "refund" được CS LogiX cho phép |
| 6 | H-063 "…sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người | Thêm: hứa hẹn ngoài kết quả hệ thống → FAIL |

## Kết luận
- **helpful bị loại**: recall chỉ 0.3 (bỏ sót 21/30 reply lỗi) và κ = 0.375 < 0.6. Hầu hết case bị bỏ sót là reply **nói sai số tiền** (vd HL-015 nói 55.000đ, ledger 40.000đ) — judge chỉ đọc chữ, không thấy ledger. Precision 1.0 không cứu được vì gate dùng judge này sẽ để lọt lỗi tiền. Lỗi tiền phải chấm bằng code (`reply_matches_ledger`, `refund_amount_correct`).
- **tone_ok được dùng** nhưng chỉ cho giọng văn, không cho tiền/approval.
- Rủi ro còn lại: judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật.
