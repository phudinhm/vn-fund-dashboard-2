# Báo cáo ETF Toàn cầu
*So sánh toàn diện ETF và quỹ mở trên mọi thị trường, đối chiếu với chỉ số tham chiếu*

- Dữ liệu cập nhật đến: **29.08.2026**
- Khung thời gian: **3Y** (29.08.2023 → 29.08.2026)
- Đơn vị tiền tệ hiển thị: **USD** · Chỉ số tham chiếu: **VNINDEX**
- Số công cụ: **6** · Số thị trường: **32** · Số đồng tiền: **20**

## 🤖 Nhận định tự động

Trong khung thời gian đang xem (29.08.2023 → 29.08.2026, quy đổi về USD), **SPY** dẫn đầu với CAGR 21.2%, trong khi **FUEVFVND** ở cuối bảng với 7.0%. Có 3/6 công cụ vượt chỉ số tham chiếu **VNINDEX** (12.0%). Hiệu quả điều chỉnh rủi ro tốt nhất thuộc về **EUNL.DE** (Sharpe 1.41), còn **VNM** chịu mức sụt giảm sâu nhất -31.6%. Tương quan trung bình giữa các lựa chọn là 0.41, đủ để mang lại lợi ích đa dạng hóa.

## Bảng xếp hạng tổng hợp

| Ticker | Xếp hạng | Tên | CAGR (kép/năm) | Biến động năm | Sụt giảm tối đa | Sharpe | Sortino | Calmar | Beta | Alpha (năm) | Sai số bám (TE) | Điểm tổng hợp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **EUNL.DE** | 1 | iShares Core MSCI World UCITS ETF | 20.66% | 14.70% | -17.78% | 1.41 | 1.93 | 1.16 | 0.27 | 7.15% | 19.29% | 0.96 |
| **SPY** | 2 | SPDR S&P 500 ETF Trust | 21.16% | 15.31% | -18.76% | 1.38 | 1.83 | 1.13 | 0.06 | 12.82% | 23.13% | 0.93 |
| **E1VFVN30** | 3 | DCVFM VN30 ETF | 16.40% | 18.06% | -18.12% | 0.91 | 1.16 | 0.91 | 0.81 | 8.68% | 10.01% | 0.29 |
| **VNINDEX** | 4 | VN-Index | 12.01% | 19.19% | -20.01% | 0.63 | 0.75 | 0.60 | n/a | n/a | n/a | -0.19 |
| **FUEVFVND** | 5 | DCVFM VN Diamond ETF | 6.97% | 21.52% | -28.27% | 0.32 | 0.43 | 0.25 | 0.86 | 10.10% | 13.78% | -0.94 |
| **VNM** | 6 | VanEck Vietnam ETF | 8.78% | 25.91% | -31.60% | 0.34 | 0.47 | 0.28 | 0.95 | -4.29% | 19.25% | -1.05 |

## Lợi nhuận theo khung thời gian

| Ticker | 1M | 3M | 6M | YTD | 1Y | 3Y | 5Y | 10Y | MAX |
|---|---|---|---|---|---|---|---|---|---|
| **VNINDEX** | 8.5% | -0.7% | -0.9% | 3.3% | 10.1% | 12.0% | 3.8% | 8.3% | 8.3% |
| **E1VFVN30** | 8.2% | 0.8% | -0.2% | -0.1% | 9.6% | 16.4% | 5.4% | 11.0% | 8.8% |
| **FUEVFVND** | 12.2% | -1.7% | -13.3% | -7.9% | -12.1% | 7.0% | 4.2% | n/a | 19.0% |
| **SPY** | 5.5% | 2.0% | 12.7% | 13.2% | 20.6% | 21.2% | 12.7% | 15.3% | 14.2% |
| **EUNL.DE** | 4.6% | 3.0% | 10.6% | 13.3% | 21.3% | 20.7% | 11.3% | 13.1% | 11.0% |
| **VNM** | 9.9% | -2.8% | -2.4% | -4.9% | -0.4% | 8.8% | -0.4% | 3.1% | -0.8% |

## Lợi nhuận theo năm

| Ticker | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| **VNINDEX** | 7.7% | 15.3% | 37.7% | -35.2% | 9.3% | 6.7% | 36.8% | 3.3% |
| **E1VFVN30** | 3.2% | 22.4% | 45.5% | -35.3% | 9.2% | 15.0% | 49.3% | -0.6% |
| **FUEVFVND** | n/a | 66.0% | 65.4% | -23.0% | 14.9% | 20.6% | 11.0% | -8.1% |
| **SPY** | 31.2% | 18.3% | 28.7% | -18.2% | 26.2% | 24.9% | 17.7% | 13.4% |
| **EUNL.DE** | 28.5% | 15.6% | 23.0% | -18.9% | 24.7% | 18.7% | 21.8% | 12.6% |
| **VNM** | 9.2% | 9.8% | 22.0% | -43.7% | 15.0% | -11.1% | 66.5% | -4.7% |

## Phương pháp luận

- Dữ liệu Việt Nam lấy từ VNDIRECT (ETF, chỉ số) và fmarket.vn (quỹ mở), dữ liệu thế giới từ Yahoo Finance với Stooq dự phòng.
- Giá thế giới đã điều chỉnh cổ tức và chia tách; NAV quỹ mở là giá trị ròng do quỹ công bố.
- Tỷ giá lấy theo ngày để quy đổi mọi tài sản về cùng một đồng tiền.

> Báo cáo tự động — chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.