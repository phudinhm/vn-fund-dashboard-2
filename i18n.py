# -*- coding: utf-8 -*-
"""
Trilingual layer of the report: Vietnamese, English, German.

Two things live here:

* ``STRINGS`` — every literal the UI shows, in all three languages. The test
  suite asserts that the three dictionaries have exactly the same keys, so a
  missing translation fails CI instead of silently falling back to English.
* ``narrative`` helpers — sentences that are *generated from the data* at
  render time (best performer, breadth, drawdown state, tracking quality...).
  They are what makes the commentary automatic: no text is hand-maintained per
  fund, it is written from the numbers each time the report runs.
"""

from __future__ import annotations

import math

LANGUAGES = {"VI": "Tiếng Việt", "EN": "English", "DE": "Deutsch"}
FLAGS = {"VI": "🇻🇳", "EN": "🇬🇧", "DE": "🇩🇪"}

STRINGS: dict[str, dict[str, str]] = {}

STRINGS["VI"] = {
    "h_excess": "Lợi nhuận vượt trội trượt (1 năm)",
    "m_coverage": "Độ phủ kỳ",
    # --- v4: coverage, liquidity, column presets ---
    "m_adv": "Thanh khoản (giá trị/ngày)",
    "m_tuw": "Thời gian dưới đỉnh (ngày)",
    "m_td": "Chênh lệch bám (năm)",
    "screener_min_adv": "Thanh khoản tối thiểu (triệu/ngày)",
    "h_coverage": "Độ phủ thị trường",
    "coverage_tracked": "Đang theo dõi",
    "coverage_listed": "Đang niêm yết",
    "coverage_note": "Toàn bộ ETF niêm yết tại Mỹ được lấy tự động từ danh bạ mã của Nasdaq Trader. Những mã thanh khoản nhất được tải lịch sử đầy đủ; phần còn lại vẫn được liệt kê ở đây.",
    "catalogue": "Danh bạ ETF",
    "price_index_caveat": "Lưu ý: giá ETF đã điều chỉnh cổ tức, còn điểm chỉ số là giá thuần (chưa cộng cổ tức). Vì vậy chênh lệch bám dương so với một chỉ số thường chính là phần cổ tức, không phải quỹ vượt trội.",
    "cols_essential": "Cột chính",
    "cols_full": "Toàn bộ cột",
    "columns": "Cột hiển thị",
    "sorted_by": "sắp xếp theo",
    "edit_selection": "Sửa danh sách",
    # --- v3 UI: dock, scope filters, readouts ---
    "group_sections": "Phần",
    "group_scope": "Phạm vi dữ liệu",
    "group_params": "Tham số",
    "brand_sub": "Báo cáo tự động · cập nhật hàng ngày",
    "filter_country": "Quốc gia / Thị trường",
    "filter_reset": "Bỏ mọi bộ lọc",
    "universe_size": "Sau bộ lọc",
    "filter_note": "Bộ lọc áp dụng cho toàn bộ báo cáo: bảng xếp hạng, bộ lọc quỹ, thị trường và danh sách chọn.",
    "fresh_today": "Mới hôm nay",
    "fresh_days": "Trễ {n} ngày",
    "fresh_stale": "Cũ {n} ngày",
    "auto_daily": "Dữ liệu tự cập nhật mỗi ngày sau phiên đóng cửa Việt Nam và Mỹ.",
    "h_growth_heatmap": "Bản đồ nhiệt tăng trưởng (năm × tháng)",
    "month": "Tháng",
    "year": "Năm",
    "positive_months": "Tháng tăng",
    "readout_label": "Kết quả đọc được",
    "ccy": "Tiền tệ",
    # --- navigation & interaction (v2 UI) ---
    "nav_overview": "Tổng quan",
    "nav_screener": "Bộ lọc quỹ",
    "nav_compare": "So sánh",
    "nav_markets": "Thị trường",
    "nav_profile": "Hồ sơ quỹ",
    "nav_lab": "Phòng thí nghiệm",
    "nav_data": "Dữ liệu",
    "nav_overview_help": "Bức tranh tổng thể của danh sách đang so sánh",
    "nav_screener_help": "Lọc và xếp hạng toàn bộ vũ trụ đầu tư theo chỉ số",
    "nav_compare_help": "Hiệu suất, rủi ro và tương quan giữa các lựa chọn",
    "nav_markets_help": "So sánh chéo khu vực, quốc gia và tác động tỷ giá",
    "nav_profile_help": "Phân tích sâu một quỹ duy nhất",
    "nav_lab_help": "Mô phỏng chiến lược đầu tư và chi phí",
    "nav_data_help": "Chất lượng dữ liệu, vũ trụ đầu tư và phương pháp",
    "selection": "Đang so sánh",
    "selection_count": "công cụ",
    "clear_selection": "Xóa hết",
    "add_to_compare": "Thêm vào so sánh",
    "added": "Đã thêm",
    "remove": "Bỏ chọn",
    "focus_fund": "Quỹ đang xem",
    "open_profile": "Mở hồ sơ quỹ",
    "share_link": "Đường dẫn chia sẻ",
    "share_help": "Sao chép URL để mở lại đúng cấu hình này",
    "screener_title": "Bộ lọc toàn vũ trụ đầu tư",
    "screener_help": "Lọc {n} công cụ theo chỉ số thực tế, chọn dòng rồi thêm vào danh sách so sánh.",
    "screener_min_cagr": "CAGR tối thiểu (%)",
    "screener_max_vol": "Biến động tối đa (%)",
    "screener_min_sharpe": "Sharpe tối thiểu",
    "screener_max_dd": "Sụt giảm tối đa cho phép (%)",
    "screener_max_ter": "Phí tối đa (%)",
    "screener_min_history": "Lịch sử tối thiểu (năm)",
    "screener_results": "Kết quả",
    "screener_no_results": "Không có công cụ nào thỏa bộ lọc.",
    "screener_reset": "Đặt lại bộ lọc",
    "screener_sort": "Sắp xếp theo",
    "screener_computing": "Đang tính chỉ số cho toàn bộ vũ trụ...",
    "screener_hint": "Tick vào ô đầu dòng rồi bấm nút để thêm vào so sánh.",
    "sparkline": "1 năm gần nhất",
    "chart_options": "Tùy chọn biểu đồ",
    "opt_log": "Thang logarit",
    "opt_relative": "Tương đối so với chỉ số",
    "opt_show_dd": "Hiện vùng sụt giảm",
    "opt_normalize": "Quy về 100",
    "profile_facts": "Thông tin cơ bản",
    "profile_vs_peers": "So với nhóm cùng loại",
    "peer_group": "Nhóm so sánh",
    "profile_pick": "Chọn quỹ để phân tích sâu",
    "percentile": "Thứ hạng phần trăm",
    "inception": "Ngày bắt đầu dữ liệu",
    "profile_metrics": "Toàn bộ chỉ số",
    "lab_dca": "Tích lũy định kỳ",
    "lab_lsdca": "Một lần vs định kỳ",
    "lab_portfolio": "Xây dựng danh mục",
    "lab_costs": "Chi phí",
    "weights": "Tỷ trọng (%)",
    "normalize_weights": "Chuẩn hóa về 100%",
    "risk_contribution": "Đóng góp rủi ro",
    "equal_weight": "Chia đều",
    "portfolio_vs": "Danh mục so với",
    "add_all_selected": "Dùng toàn bộ lựa chọn",
    "no_focus": "Chưa chọn quỹ nào.",
    "compare_tabs": "Nhóm phân tích",
    "click_hint": "Bấm vào một điểm trên biểu đồ để mở hồ sơ quỹ đó.",
    "top_n": "Số dòng hiển thị",
    "all": "Tất cả",
    # --- chrome -----------------------------------------------------------
    "app_title": "Báo cáo ETF Toàn cầu",
    "app_subtitle": "So sánh toàn diện ETF và quỹ mở trên mọi thị trường, đối chiếu với chỉ số tham chiếu",
    "language": "Ngôn ngữ",
    "settings": "Cấu hình",
    "filters": "Bộ lọc vũ trụ đầu tư",
    "data_updated": "Dữ liệu cập nhật đến",
    "data_source": "Nguồn dữ liệu",
    "auto_note": "Toàn bộ số liệu được cập nhật tự động hàng ngày qua GitHub Actions",
    "update_btn": "Cập nhật dữ liệu ngay",
    "updating": "Đang tải dữ liệu từ các nguồn...",
    "update_done": "Cập nhật xong. Tải lại trang để xem số liệu mới.",
    "update_failed": "Cập nhật thất bại",
    "no_data": "Chưa có dữ liệu. Chạy `python update_data.py` hoặc kích hoạt GitHub Action.",
    "loading": "Đang tính toán...",
    "footer": "Báo cáo tự động — chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.",
    # --- selectors --------------------------------------------------------
    "region": "Khu vực",
    "market": "Thị trường",
    "asset_class": "Loại tài sản",
    "kind": "Loại hình",
    "issuer": "Nhà quản lý",
    "category": "Phân nhóm",
    "currency": "Đơn vị tiền tệ hiển thị",
    "currency_help": "Mọi mức giá được quy đổi về đồng tiền này theo tỷ giá từng ngày, để so sánh công bằng giữa các thị trường.",
    "select_funds": "Chọn quỹ / chỉ số để so sánh",
    "benchmark": "Chỉ số tham chiếu",
    "time_range": "Khung thời gian",
    "risk_free": "Lãi suất phi rủi ro (%/năm)",
    "quick_pick": "Chọn nhanh",
    "preset_vn": "ETF Việt Nam",
    "preset_global": "ETF toàn cầu",
    "preset_us": "ETF Mỹ",
    "preset_europe": "ETF châu Âu",
    "preset_asia": "ETF châu Á",
    "preset_index": "Chỉ số thị trường",
    "preset_bond": "Trái phiếu & vàng",
    "preset_mutual": "Quỹ mở Việt Nam",
    "scope": "Phạm vi phân tích",
    "apply": "Áp dụng",
    "search_ticker": "Tìm mã",
    # --- tabs -------------------------------------------------------------
    "tab_summary": "Tổng quan",
    "tab_performance": "Hiệu suất",
    "tab_risk": "Rủi ro",
    "tab_riskreturn": "Rủi ro – Lợi nhuận",
    "tab_benchmark": "So với chỉ số",
    "tab_markets": "Thị trường toàn cầu",
    "tab_correlation": "Tương quan",
    "tab_costs": "Chi phí & Cấu trúc",
    "tab_cycles": "Chu kỳ & Mùa vụ",
    "tab_strategy": "Chiến lược",
    "tab_forecast": "Dự báo",
    "tab_data": "Dữ liệu & Phương pháp",
    # --- metric labels ----------------------------------------------------
    "m_total_return": "Lợi nhuận toàn kỳ",
    "m_cagr": "CAGR (kép/năm)",
    "m_volatility": "Biến động năm",
    "m_downside": "Độ lệch giảm giá",
    "m_maxdd": "Sụt giảm tối đa",
    "m_sharpe": "Sharpe",
    "m_sortino": "Sortino",
    "m_calmar": "Calmar",
    "m_omega": "Omega",
    "m_ulcer": "Ulcer Index",
    "m_martin": "Martin Ratio",
    "m_stability": "Độ ổn định xu hướng",
    "m_var": "VaR 95% (ngày)",
    "m_cvar": "CVaR 95% (ngày)",
    "m_skew": "Độ lệch (Skew)",
    "m_kurtosis": "Độ nhọn (Kurtosis)",
    "m_tail": "Tỷ lệ đuôi",
    "m_hit": "Tỷ lệ ngày tăng",
    "m_beta": "Beta",
    "m_alpha": "Alpha (năm)",
    "m_r2": "R²",
    "m_te": "Sai số bám (TE)",
    "m_ir": "Information Ratio",
    "m_up": "Bắt sóng tăng",
    "m_down": "Bắt sóng giảm",
    "m_capture_spread": "Chênh lệch bắt sóng",
    "m_batting": "Tỷ lệ thắng chỉ số",
    "m_ter": "Phí quản lý (TER)",
    "m_score": "Điểm tổng hợp",
    "m_rank": "Xếp hạng",
    "m_obs": "Số phiên",
    "m_first": "Từ ngày",
    "m_last": "Đến ngày",
    "m_name": "Tên",
    "m_best_day": "Phiên tốt nhất",
    "m_worst_day": "Phiên xấu nhất",
    # --- section headings -------------------------------------------------
    "h_kpi": "Chỉ số chính",
    "h_leaderboard": "Bảng xếp hạng tổng hợp",
    "h_growth": "Tăng trưởng tài sản (quy về 100)",
    "h_period_returns": "Lợi nhuận theo khung thời gian",
    "h_calendar": "Lợi nhuận theo năm",
    "h_rolling": "Lợi nhuận trượt",
    "h_drawdown": "Sụt giảm từ đỉnh",
    "h_dd_table": "Các đợt sụt giảm sâu nhất",
    "h_riskmetrics": "Bảng chỉ số rủi ro",
    "h_scatter": "Bản đồ rủi ro – lợi nhuận",
    "h_frontier": "Đường biên hiệu quả",
    "h_alpha": "Alpha, Beta và sai số bám",
    "h_capture": "Bắt sóng tăng / giảm",
    "h_te": "Sai số bám theo thời gian",
    "h_region": "Hiệu suất theo khu vực",
    "h_market_matrix": "Ma trận thị trường",
    "h_currency_effect": "Tác động tỷ giá",
    "h_corr": "Ma trận tương quan",
    "h_corr_rolling": "Tương quan trượt với chỉ số",
    "h_fees": "Phí và bào mòn lợi nhuận",
    "h_liquidity": "Thanh khoản",
    "h_ter_vs_perf": "Phí so với hiệu suất",
    "h_monthly": "Bản đồ nhiệt lợi nhuận theo tháng",
    "h_bullbear": "Hiệu suất trong thị trường tăng / giảm",
    "h_seasonality": "Tính mùa vụ",
    "h_dca": "Tích lũy định kỳ (DCA)",
    "h_lsdca": "Đầu tư một lần so với DCA",
    "h_portfolio": "Danh mục tái cân bằng",
    "h_forecast": "Dự báo xu hướng",
    "h_montecarlo": "Mô phỏng Monte Carlo",
    "h_quality": "Chất lượng dữ liệu",
    "h_method": "Phương pháp luận",
    "h_universe": "Vũ trụ đầu tư",
    "h_export": "Xuất báo cáo",
    # --- controls ---------------------------------------------------------
    "c_window_years": "Độ dài cửa sổ (năm)",
    "c_contribution": "Số tiền mỗi kỳ",
    "c_frequency": "Tần suất",
    "c_monthly": "Hàng tháng",
    "c_weekly": "Hàng tuần",
    "c_hold_years": "Thời gian nắm giữ (năm)",
    "c_spread_months": "Số tháng rải vốn",
    "c_horizon": "Số phiên dự báo",
    "c_gross_return": "Lợi nhuận gộp giả định (%/năm)",
    "c_years": "Số năm",
    "c_initial": "Vốn ban đầu",
    "c_pick_one": "Chọn một mã",
    "c_show_table": "Hiện bảng số liệu",
    "c_rebalance": "Tần suất tái cân bằng",
    "c_quarterly": "Hàng quý",
    "c_annually": "Hàng năm",
    "c_download_csv": "Tải bảng chỉ số (CSV)",
    "c_download_report": "Tải báo cáo (Markdown)",
    # --- axis / misc ------------------------------------------------------
    "x_date": "Ngày",
    "x_vol": "Biến động năm (%)",
    "y_return": "Lợi nhuận (%)",
    "y_cagr": "CAGR (%)",
    "y_dd": "Sụt giảm (%)",
    "y_value": "Giá trị",
    "y_te": "Sai số bám (%)",
    "y_volume": "Khối lượng",
    "n_funds": "Số quỹ",
    "n_instruments": "Số công cụ",
    "n_markets": "Số thị trường",
    "n_currencies": "Số đồng tiền",
    "insight": "Cách đọc",
    "auto_commentary": "Nhận định",
    "bull": "Thị trường tăng",
    "bear": "Thị trường giảm",
    "best": "Tốt nhất",
    "worst": "Kém nhất",
    "median": "Trung vị",
    "average": "Trung bình",
    "win_rate": "Tỷ lệ thắng",
    "windows": "Số cửa sổ",
    "prob_up": "Xác suất tăng",
    "invested": "Đã đầu tư",
    "value": "Giá trị",
    "profit": "Lãi/lỗ",
    "lump_sum": "Đầu tư một lần",
    "dca": "Tích lũy định kỳ",
    "gross": "Chưa trừ phí",
    "net": "Sau phí",
    "fees_lost": "Phí đã mất",
    "stale_warning": "Các mã sau chậm cập nhật quá 7 ngày",
    "fx_warning": "Không có tỷ giá cho các đồng tiền sau, giá giữ nguyên nội tệ",
    "no_selection": "Hãy chọn ít nhất một quỹ hoặc chỉ số ở thanh bên.",
    "not_enough_data": "Không đủ dữ liệu cho lựa chọn này.",
    # --- explanations -----------------------------------------------------
    "x_growth": """
- **Cách đọc:** mọi đường bắt đầu tại 100 vào ngày đầu kỳ. Đường cao nhất là quỹ tạo ra nhiều tài sản nhất.
- **So với chỉ số:** nằm dưới đường chỉ số tham chiếu nghĩa là quỹ thua thị trường sau chi phí.
- **Quy đổi tiền tệ:** tất cả đã đổi về đồng tiền hiển thị, nên chênh lệch tỷ giá đã được tính vào.
""",
    "x_periods": """
- Khung từ 3 năm trở lên được **quy đổi về lợi nhuận kép mỗi năm (CAGR)**; khung ngắn hơn là lợi nhuận tuyệt đối.
- So sánh cùng cột, không so chéo cột: một quỹ ra đời năm ngoái không có số liệu 10 năm.
""",
    "x_drawdown": """
- **Drawdown** đo mức lỗ tính từ đỉnh gần nhất — chính là "nỗi đau" phải chịu khi nắm giữ.
- Lỗ **-20%** cần lãi **+25%** để hòa vốn; lỗ **-50%** cần lãi **+100%**.
- Quỹ tốt là quỹ có đáy nông hơn và hồi phục nhanh hơn chỉ số trong cùng giai đoạn.
""",
    "x_riskreturn": """
- **Góc trên bên trái** là vùng lý tưởng: lợi nhuận cao, biến động thấp.
- **Sharpe** cho biết mỗi đơn vị rủi ro đổi lấy bao nhiêu lợi nhuận vượt lãi suất phi rủi ro; **Sortino** chỉ phạt biến động giảm.
- **Calmar** so lợi nhuận với sụt giảm tối đa — hữu ích cho người sợ lỗ sâu.
""",
    "x_benchmark": """
- **Beta > 1** biến động mạnh hơn chỉ số, **Beta < 1** phòng thủ hơn.
- **Alpha > 0** là phần lợi nhuận vượt trội sau khi trừ rủi ro thị trường.
- **Sai số bám (TE)** thấp là dấu hiệu ETF mô phỏng chỉ số tốt; TE cao bất thường cho thấy chi phí ẩn hoặc lệch danh mục.
- **Information Ratio** = alpha chia TE: chất lượng của phần vượt trội đó.
""",
    "x_markets": """
- Bảng so sánh chéo mọi thị trường sau khi đã quy đổi về một đồng tiền chung.
- Một thị trường có thể tăng bằng nội tệ nhưng vẫn lỗ với nhà đầu tư nước ngoài nếu đồng tiền mất giá.
""",
    "x_correlation": """
- Tương quan thấp giữa các tài sản là nguồn gốc của đa dạng hóa thực sự.
- Hệ số gần **1**: hai quỹ gần như trùng nhau, nắm cả hai không giảm rủi ro.
- Hệ số **< 0.5** hoặc âm: khi một bên giảm, bên kia có thể giữ giá.
""",
    "x_costs": """
- **TER** trừ trực tiếp vào NAV mỗi ngày, không hiện trên sao kê nhưng bào mòn lãi kép qua thời gian.
- Chênh lệch 0,5%/năm trong 20 năm có thể lấy đi hơn 10% tài sản cuối kỳ.
- Thanh khoản thấp làm tăng chi phí ẩn khi mua bán (trượt giá).
""",
    "x_cycles": """
- **Bắt sóng tăng** > 100% nghĩa là quỹ tăng mạnh hơn chỉ số trong phiên thị trường tăng.
- **Bắt sóng giảm** < 100% nghĩa là quỹ giảm ít hơn chỉ số — đặc tính phòng thủ.
- Bản đồ nhiệt theo tháng giúp nhìn ra giai đoạn nào thường thuận lợi trong năm.
""",
    "x_strategy": """
- **DCA** chia nhỏ vốn theo thời gian, giảm rủi ro chọn sai thời điểm nhưng thường giảm cả lợi nhuận kỳ vọng.
- **Một lần** thường thắng về mặt thống kê vì thị trường tăng nhiều hơn giảm, nhưng biến động chịu đựng lớn hơn.
- Bảng kết quả được tính trên toàn bộ lịch sử: mỗi ngày là một kịch bản khởi đầu độc lập.
""",
    "x_forecast": """
- **Monte Carlo** mô phỏng hàng nghìn kịch bản dựa trên phân phối lợi nhuận quá khứ.
- **ETS** ngoại suy xu hướng có giảm chấn từ chuỗi thời gian.
- Dự báo chỉ là phân phối xác suất từ dữ liệu cũ; biến cố vĩ mô bất ngờ không nằm trong mô hình.
""",
    "x_data": """
- Dữ liệu Việt Nam lấy từ VNDIRECT (ETF, chỉ số) và fmarket.vn (quỹ mở), dữ liệu thế giới từ Yahoo Finance với Stooq dự phòng.
- Giá thế giới đã điều chỉnh cổ tức và chia tách; NAV quỹ mở là giá trị ròng do quỹ công bố.
- Tỷ giá lấy theo ngày để quy đổi mọi tài sản về cùng một đồng tiền.
""",
}

STRINGS["EN"] = {
    "h_excess": "Rolling excess return (1 year)",
    "m_coverage": "Window coverage",
    # --- v4: coverage, liquidity, column presets ---
    "m_adv": "Liquidity (traded/day)",
    "m_tuw": "Time under water (days)",
    "m_td": "Tracking difference (ann.)",
    "screener_min_adv": "Minimum liquidity (m/day)",
    "h_coverage": "Market coverage",
    "coverage_tracked": "Tracked",
    "coverage_listed": "Listed",
    "coverage_note": "Every US-listed ETF is discovered automatically from the Nasdaq Trader symbol directory. The most liquid ones get a full price history; the rest are still listed here.",
    "catalogue": "ETF catalogue",
    "price_index_caveat": "Note: ETF prices are adjusted for dividends, index levels are not. A positive tracking difference against an index is usually the dividend yield, not outperformance.",
    "cols_essential": "Key columns",
    "cols_full": "All columns",
    "columns": "Columns",
    "sorted_by": "sorted by",
    "edit_selection": "Edit list",
    # --- v3 UI: dock, scope filters, readouts ---
    "group_sections": "Sections",
    "group_scope": "Data scope",
    "group_params": "Parameters",
    "brand_sub": "Automated report · refreshed daily",
    "filter_country": "Country / market",
    "filter_reset": "Clear all filters",
    "universe_size": "After filters",
    "filter_note": "Filters apply to the whole report: leaderboard, screener, markets and the picker.",
    "fresh_today": "Fresh today",
    "fresh_days": "{n} days behind",
    "fresh_stale": "{n} days old",
    "auto_daily": "Data refreshes itself every day after the Vietnamese and US closes.",
    "h_growth_heatmap": "Growth heatmap (year × month)",
    "month": "Month",
    "year": "Year",
    "positive_months": "Positive months",
    "readout_label": "What the chart says",
    "ccy": "Currency",
    # --- navigation & interaction (v2 UI) ---
    "nav_overview": "Overview",
    "nav_screener": "Screener",
    "nav_compare": "Compare",
    "nav_markets": "Markets",
    "nav_profile": "Fund profile",
    "nav_lab": "Lab",
    "nav_data": "Data",
    "nav_overview_help": "The big picture for the funds you are comparing",
    "nav_screener_help": "Filter and rank the whole universe by its metrics",
    "nav_compare_help": "Performance, risk and correlation across your selection",
    "nav_markets_help": "Region and country comparison plus the currency effect",
    "nav_profile_help": "Deep dive into a single fund",
    "nav_lab_help": "Simulate strategies and costs",
    "nav_data_help": "Data quality, the universe and the methodology",
    "selection": "Comparing",
    "selection_count": "instruments",
    "clear_selection": "Clear",
    "add_to_compare": "Add to comparison",
    "added": "Added",
    "remove": "Remove",
    "focus_fund": "Focused fund",
    "open_profile": "Open fund profile",
    "share_link": "Shareable link",
    "share_help": "Copy the URL to reopen exactly this view",
    "screener_title": "Universe screener",
    "screener_help": "Filter {n} instruments on their real metrics, tick the rows you want and add them to the comparison.",
    "screener_min_cagr": "Minimum CAGR (%)",
    "screener_max_vol": "Maximum volatility (%)",
    "screener_min_sharpe": "Minimum Sharpe",
    "screener_max_dd": "Worst drawdown allowed (%)",
    "screener_max_ter": "Maximum fee (%)",
    "screener_min_history": "Minimum history (years)",
    "screener_results": "Results",
    "screener_no_results": "Nothing matches these filters.",
    "screener_reset": "Reset filters",
    "screener_sort": "Sort by",
    "screener_computing": "Computing metrics for the whole universe...",
    "screener_hint": "Tick a row and press the button to add it to the comparison.",
    "sparkline": "Last 12 months",
    "chart_options": "Chart options",
    "opt_log": "Logarithmic scale",
    "opt_relative": "Relative to benchmark",
    "opt_show_dd": "Show drawdown band",
    "opt_normalize": "Rebase to 100",
    "profile_facts": "Key facts",
    "profile_vs_peers": "Against its peer group",
    "peer_group": "Peer group",
    "profile_pick": "Fund to analyse",
    "percentile": "Percentile",
    "inception": "Data starts",
    "profile_metrics": "Every metric",
    "lab_dca": "Dollar cost averaging",
    "lab_lsdca": "Lump sum vs DCA",
    "lab_portfolio": "Portfolio builder",
    "lab_costs": "Costs",
    "weights": "Weight (%)",
    "normalize_weights": "Normalise to 100%",
    "risk_contribution": "Risk contribution",
    "equal_weight": "Equal weight",
    "portfolio_vs": "Portfolio versus",
    "add_all_selected": "Use the whole selection",
    "no_focus": "No fund selected yet.",
    "compare_tabs": "Analysis group",
    "click_hint": "Click a point on the chart to open that fund's profile.",
    "top_n": "Rows to show",
    "all": "All",
    "app_title": "Global ETF Report",
    "app_subtitle": "Comprehensive comparison of ETFs and mutual funds across every market, against their benchmarks",
    "language": "Language",
    "settings": "Settings",
    "filters": "Universe filters",
    "data_updated": "Data updated to",
    "data_source": "Data sources",
    "auto_note": "All figures refresh automatically every day through GitHub Actions",
    "update_btn": "Refresh data now",
    "updating": "Downloading from all sources...",
    "update_done": "Update finished. Reload the page to see the new figures.",
    "update_failed": "Update failed",
    "no_data": "No data yet. Run `python update_data.py` or trigger the GitHub Action.",
    "loading": "Calculating...",
    "footer": "Automated report — for information only, not investment advice.",
    "region": "Region",
    "market": "Market",
    "asset_class": "Asset class",
    "kind": "Instrument type",
    "issuer": "Fund house",
    "category": "Category",
    "currency": "Reporting currency",
    "currency_help": "Every price is converted into this currency at the daily FX rate, so markets can be compared fairly.",
    "select_funds": "Funds / indices to compare",
    "benchmark": "Benchmark",
    "time_range": "Time range",
    "risk_free": "Risk-free rate (% p.a.)",
    "quick_pick": "Quick pick",
    "preset_vn": "Vietnam ETFs",
    "preset_global": "Global ETFs",
    "preset_us": "US ETFs",
    "preset_europe": "European ETFs",
    "preset_asia": "Asian ETFs",
    "preset_index": "Market indices",
    "preset_bond": "Bonds & gold",
    "preset_mutual": "Vietnam mutual funds",
    "scope": "Analysis scope",
    "apply": "Apply",
    "search_ticker": "Search ticker",
    "tab_summary": "Summary",
    "tab_performance": "Performance",
    "tab_risk": "Risk",
    "tab_riskreturn": "Risk–Return",
    "tab_benchmark": "vs Benchmark",
    "tab_markets": "Global markets",
    "tab_correlation": "Correlation",
    "tab_costs": "Costs & Structure",
    "tab_cycles": "Cycles & Seasonality",
    "tab_strategy": "Strategy",
    "tab_forecast": "Forecast",
    "tab_data": "Data & Method",
    "m_total_return": "Total return",
    "m_cagr": "CAGR",
    "m_volatility": "Volatility (ann.)",
    "m_downside": "Downside deviation",
    "m_maxdd": "Max drawdown",
    "m_sharpe": "Sharpe",
    "m_sortino": "Sortino",
    "m_calmar": "Calmar",
    "m_omega": "Omega",
    "m_ulcer": "Ulcer index",
    "m_martin": "Martin ratio",
    "m_stability": "Trend stability",
    "m_var": "VaR 95% (daily)",
    "m_cvar": "CVaR 95% (daily)",
    "m_skew": "Skewness",
    "m_kurtosis": "Kurtosis",
    "m_tail": "Tail ratio",
    "m_hit": "Positive days",
    "m_beta": "Beta",
    "m_alpha": "Alpha (ann.)",
    "m_r2": "R²",
    "m_te": "Tracking error",
    "m_ir": "Information ratio",
    "m_up": "Upside capture",
    "m_down": "Downside capture",
    "m_capture_spread": "Capture spread",
    "m_batting": "Batting average",
    "m_ter": "Expense ratio (TER)",
    "m_score": "Composite score",
    "m_rank": "Rank",
    "m_obs": "Observations",
    "m_first": "From",
    "m_last": "To",
    "m_name": "Name",
    "m_best_day": "Best day",
    "m_worst_day": "Worst day",
    "h_kpi": "Headline figures",
    "h_leaderboard": "Composite leaderboard",
    "h_growth": "Wealth growth (rebased to 100)",
    "h_period_returns": "Returns by period",
    "h_calendar": "Calendar-year returns",
    "h_rolling": "Rolling returns",
    "h_drawdown": "Drawdown from peak",
    "h_dd_table": "Deepest drawdown episodes",
    "h_riskmetrics": "Risk metrics",
    "h_scatter": "Risk–return map",
    "h_frontier": "Efficient frontier",
    "h_alpha": "Alpha, beta and tracking",
    "h_capture": "Upside / downside capture",
    "h_te": "Tracking error over time",
    "h_region": "Performance by region",
    "h_market_matrix": "Market matrix",
    "h_currency_effect": "Currency effect",
    "h_corr": "Correlation matrix",
    "h_corr_rolling": "Rolling correlation with the benchmark",
    "h_fees": "Fees and return erosion",
    "h_liquidity": "Liquidity",
    "h_ter_vs_perf": "Fee versus performance",
    "h_monthly": "Monthly return heatmap",
    "h_bullbear": "Bull versus bear behaviour",
    "h_seasonality": "Seasonality",
    "h_dca": "Dollar cost averaging",
    "h_lsdca": "Lump sum versus DCA",
    "h_portfolio": "Rebalanced portfolio",
    "h_forecast": "Trend forecast",
    "h_montecarlo": "Monte Carlo simulation",
    "h_quality": "Data quality",
    "h_method": "Methodology",
    "h_universe": "Investment universe",
    "h_export": "Export",
    "c_window_years": "Window length (years)",
    "c_contribution": "Amount per period",
    "c_frequency": "Frequency",
    "c_monthly": "Monthly",
    "c_weekly": "Weekly",
    "c_hold_years": "Holding period (years)",
    "c_spread_months": "Months to spread the capital",
    "c_horizon": "Forecast horizon (days)",
    "c_gross_return": "Assumed gross return (% p.a.)",
    "c_years": "Years",
    "c_initial": "Initial capital",
    "c_pick_one": "Pick one instrument",
    "c_show_table": "Show the data table",
    "c_rebalance": "Rebalancing frequency",
    "c_quarterly": "Quarterly",
    "c_annually": "Annually",
    "c_download_csv": "Download metrics (CSV)",
    "c_download_report": "Download report (Markdown)",
    "x_date": "Date",
    "x_vol": "Annual volatility (%)",
    "y_return": "Return (%)",
    "y_cagr": "CAGR (%)",
    "y_dd": "Drawdown (%)",
    "y_value": "Value",
    "y_te": "Tracking error (%)",
    "y_volume": "Volume",
    "n_funds": "Funds",
    "n_instruments": "Instruments",
    "n_markets": "Markets",
    "n_currencies": "Currencies",
    "insight": "How to read this",
    "auto_commentary": "Commentary",
    "bull": "Bull market",
    "bear": "Bear market",
    "best": "Best",
    "worst": "Worst",
    "median": "Median",
    "average": "Average",
    "win_rate": "Win rate",
    "windows": "Windows",
    "prob_up": "Probability of a gain",
    "invested": "Invested",
    "value": "Value",
    "profit": "Profit / loss",
    "lump_sum": "Lump sum",
    "dca": "DCA",
    "gross": "Before fees",
    "net": "After fees",
    "fees_lost": "Lost to fees",
    "stale_warning": "These tickers are more than 7 days stale",
    "fx_warning": "No FX rate for these currencies, prices stay in local currency",
    "no_selection": "Select at least one fund or index in the sidebar.",
    "not_enough_data": "Not enough data for this selection.",
    "x_growth": """
- **How to read:** every line starts at 100 on the first day of the window. The highest line built the most wealth.
- **Against the benchmark:** a line below the benchmark means the fund lost to the market after costs.
- **Currency:** everything is converted into the reporting currency, so FX moves are already included.
""",
    "x_periods": """
- Windows of three years and longer are shown as **compound annual growth (CAGR)**; shorter windows are absolute returns.
- Compare within a column, not across columns: a fund launched last year has no ten-year figure.
""",
    "x_drawdown": """
- **Drawdown** measures the loss from the most recent peak — the pain of holding the fund.
- A **-20%** loss needs **+25%** to break even; **-50%** needs **+100%**.
- Good funds show shallower troughs and faster recoveries than the index over the same stretch.
""",
    "x_riskreturn": """
- The **top-left corner** is the sweet spot: high return with low volatility.
- **Sharpe** is excess return per unit of total risk; **Sortino** only penalises downside volatility.
- **Calmar** compares return with the worst drawdown — useful if deep losses are your binding constraint.
""",
    "x_benchmark": """
- **Beta > 1** amplifies the index, **Beta < 1** is defensive.
- **Alpha > 0** is the return left over once market risk is paid for.
- Low **tracking error** means the ETF replicates its index tightly; unusually high TE points to hidden costs or drift.
- **Information ratio** = alpha divided by tracking error: the quality of that excess return.
""",
    "x_markets": """
- Cross-market comparison after converting every price into one common currency.
- A market can rise in local currency and still lose money for a foreign investor when its currency weakens.
""",
    "x_correlation": """
- Low correlation between holdings is where real diversification comes from.
- Coefficient near **1**: the two funds move as one, holding both adds no protection.
- Coefficient **below 0.5** or negative: when one falls, the other may hold its ground.
""",
    "x_costs": """
- The **TER** is deducted from NAV every day. It never appears on a statement but it compounds against you.
- Half a percent a year over twenty years can cost more than 10% of the final portfolio.
- Thin liquidity adds a second, hidden cost through slippage on entry and exit.
""",
    "x_cycles": """
- **Upside capture** above 100% means the fund rises more than the index on up days.
- **Downside capture** below 100% means it falls less than the index — a defensive profile.
- The monthly heatmap shows which parts of the year have historically been kind to the fund.
""",
    "x_strategy": """
- **DCA** spreads the entry over time, cutting timing risk but usually trimming expected return.
- **Lump sum** wins more often statistically because markets rise more than they fall — at the price of a rougher ride.
- The table rolls the comparison over the whole history: every start date is an independent scenario.
""",
    "x_forecast": """
- **Monte Carlo** draws thousands of paths from the historical return distribution.
- **ETS** extrapolates a damped trend from the time series itself.
- A forecast is a probability distribution built on the past; macro shocks are outside the model.
""",
    "x_data": """
- Vietnamese data comes from VNDIRECT (ETFs, indices) and fmarket.vn (open-ended funds); world data from Yahoo Finance with Stooq as fallback.
- World prices are adjusted for dividends and splits; mutual fund figures are the published NAV.
- Daily FX rates convert every asset into a single reporting currency.
""",
}

STRINGS["DE"] = {
    "h_excess": "Rollierende Überrendite (1 Jahr)",
    "m_coverage": "Zeitraumabdeckung",
    # --- v4: coverage, liquidity, column presets ---
    "m_adv": "Liquidität (Umsatz/Tag)",
    "m_tuw": "Zeit unter Wasser (Tage)",
    "m_td": "Tracking-Differenz (p.a.)",
    "screener_min_adv": "Mindestliquidität (Mio./Tag)",
    "h_coverage": "Marktabdeckung",
    "coverage_tracked": "Verfolgt",
    "coverage_listed": "Gelistet",
    "coverage_note": "Jeder in den USA gelistete ETF wird automatisch aus dem Symbolverzeichnis von Nasdaq Trader ermittelt. Die liquidesten erhalten eine vollständige Kurshistorie, die übrigen stehen trotzdem hier.",
    "catalogue": "ETF-Verzeichnis",
    "price_index_caveat": "Hinweis: ETF-Kurse sind dividendenbereinigt, Indexstände nicht. Eine positive Tracking-Differenz gegenüber einem Index ist meist die Dividendenrendite, keine Mehrleistung.",
    "cols_essential": "Kernspalten",
    "cols_full": "Alle Spalten",
    "columns": "Spalten",
    "sorted_by": "sortiert nach",
    "edit_selection": "Liste ändern",
    # --- v3 UI: dock, scope filters, readouts ---
    "group_sections": "Bereiche",
    "group_scope": "Datenumfang",
    "group_params": "Parameter",
    "brand_sub": "Automatisierter Bericht · täglich aktualisiert",
    "filter_country": "Land / Markt",
    "filter_reset": "Alle Filter löschen",
    "universe_size": "Nach Filtern",
    "filter_note": "Filter gelten für den ganzen Bericht: Rangliste, Screener, Märkte und Auswahl.",
    "fresh_today": "Heute aktuell",
    "fresh_days": "{n} Tage zurück",
    "fresh_stale": "{n} Tage alt",
    "auto_daily": "Die Daten aktualisieren sich täglich nach dem vietnamesischen und dem US-Schluss.",
    "h_growth_heatmap": "Wachstums-Heatmap (Jahr × Monat)",
    "month": "Monat",
    "year": "Jahr",
    "positive_months": "Positive Monate",
    "readout_label": "Was das Diagramm zeigt",
    "ccy": "Währung",
    # --- navigation & interaction (v2 UI) ---
    "nav_overview": "Überblick",
    "nav_screener": "Screener",
    "nav_compare": "Vergleich",
    "nav_markets": "Märkte",
    "nav_profile": "Fondsprofil",
    "nav_lab": "Labor",
    "nav_data": "Daten",
    "nav_overview_help": "Das Gesamtbild der verglichenen Fonds",
    "nav_screener_help": "Das gesamte Universum nach Kennzahlen filtern und ranken",
    "nav_compare_help": "Performance, Risiko und Korrelation der Auswahl",
    "nav_markets_help": "Regionen- und Ländervergleich samt Währungseffekt",
    "nav_profile_help": "Tiefenanalyse eines einzelnen Fonds",
    "nav_lab_help": "Strategien und Kosten simulieren",
    "nav_data_help": "Datenqualität, Universum und Methodik",
    "selection": "Im Vergleich",
    "selection_count": "Instrumente",
    "clear_selection": "Leeren",
    "add_to_compare": "Zum Vergleich hinzufügen",
    "added": "Hinzugefügt",
    "remove": "Entfernen",
    "focus_fund": "Ausgewählter Fonds",
    "open_profile": "Fondsprofil öffnen",
    "share_link": "Teilbarer Link",
    "share_help": "URL kopieren, um genau diese Ansicht wieder zu öffnen",
    "screener_title": "Universum-Screener",
    "screener_help": "{n} Instrumente nach echten Kennzahlen filtern, Zeilen markieren und in den Vergleich übernehmen.",
    "screener_min_cagr": "Mindest-CAGR (%)",
    "screener_max_vol": "Maximale Volatilität (%)",
    "screener_min_sharpe": "Mindest-Sharpe",
    "screener_max_dd": "Maximal erlaubter Drawdown (%)",
    "screener_max_ter": "Maximale Kosten (%)",
    "screener_min_history": "Mindesthistorie (Jahre)",
    "screener_results": "Ergebnisse",
    "screener_no_results": "Kein Instrument passt zu diesen Filtern.",
    "screener_reset": "Filter zurücksetzen",
    "screener_sort": "Sortieren nach",
    "screener_computing": "Kennzahlen für das gesamte Universum werden berechnet...",
    "screener_hint": "Zeile markieren und den Knopf drücken, um sie in den Vergleich zu übernehmen.",
    "sparkline": "Letzte 12 Monate",
    "chart_options": "Diagrammoptionen",
    "opt_log": "Logarithmische Skala",
    "opt_relative": "Relativ zur Benchmark",
    "opt_show_dd": "Drawdown-Band anzeigen",
    "opt_normalize": "Auf 100 normieren",
    "profile_facts": "Eckdaten",
    "profile_vs_peers": "Gegen die Vergleichsgruppe",
    "peer_group": "Vergleichsgruppe",
    "profile_pick": "Zu analysierender Fonds",
    "percentile": "Perzentil",
    "inception": "Daten ab",
    "profile_metrics": "Alle Kennzahlen",
    "lab_dca": "Sparplan",
    "lab_lsdca": "Einmalanlage vs. Sparplan",
    "lab_portfolio": "Portfolio-Baukasten",
    "lab_costs": "Kosten",
    "weights": "Gewicht (%)",
    "normalize_weights": "Auf 100% normieren",
    "risk_contribution": "Risikobeitrag",
    "equal_weight": "Gleichgewichtet",
    "portfolio_vs": "Portfolio gegen",
    "add_all_selected": "Gesamte Auswahl übernehmen",
    "no_focus": "Noch kein Fonds ausgewählt.",
    "compare_tabs": "Analysegruppe",
    "click_hint": "Auf einen Punkt im Diagramm klicken, um das Fondsprofil zu öffnen.",
    "top_n": "Angezeigte Zeilen",
    "all": "Alle",
    "app_title": "Globaler ETF-Bericht",
    "app_subtitle": "Umfassender Vergleich von ETFs und Investmentfonds über alle Märkte hinweg, gemessen an ihren Benchmarks",
    "language": "Sprache",
    "settings": "Einstellungen",
    "filters": "Anlageuniversum filtern",
    "data_updated": "Daten aktuell bis",
    "data_source": "Datenquellen",
    "auto_note": "Alle Zahlen werden täglich automatisch über GitHub Actions aktualisiert",
    "update_btn": "Daten jetzt aktualisieren",
    "updating": "Daten werden von allen Quellen geladen...",
    "update_done": "Aktualisierung abgeschlossen. Seite neu laden, um die neuen Zahlen zu sehen.",
    "update_failed": "Aktualisierung fehlgeschlagen",
    "no_data": "Noch keine Daten. `python update_data.py` ausführen oder die GitHub Action starten.",
    "loading": "Berechnung läuft...",
    "footer": "Automatisierter Bericht — nur zur Information, keine Anlageberatung.",
    "region": "Region",
    "market": "Markt",
    "asset_class": "Anlageklasse",
    "kind": "Instrumententyp",
    "issuer": "Fondsgesellschaft",
    "category": "Kategorie",
    "currency": "Berichtswährung",
    "currency_help": "Jeder Kurs wird zum Tageskurs in diese Währung umgerechnet, damit Märkte fair vergleichbar sind.",
    "select_funds": "Fonds / Indizes zum Vergleich",
    "benchmark": "Benchmark",
    "time_range": "Zeitraum",
    "risk_free": "Risikofreier Zins (% p.a.)",
    "quick_pick": "Schnellauswahl",
    "preset_vn": "Vietnam-ETFs",
    "preset_global": "Globale ETFs",
    "preset_us": "US-ETFs",
    "preset_europe": "Europäische ETFs",
    "preset_asia": "Asiatische ETFs",
    "preset_index": "Marktindizes",
    "preset_bond": "Anleihen & Gold",
    "preset_mutual": "Vietnamesische Publikumsfonds",
    "scope": "Analyseumfang",
    "apply": "Anwenden",
    "search_ticker": "Ticker suchen",
    "tab_summary": "Überblick",
    "tab_performance": "Performance",
    "tab_risk": "Risiko",
    "tab_riskreturn": "Risiko–Rendite",
    "tab_benchmark": "vs. Benchmark",
    "tab_markets": "Weltmärkte",
    "tab_correlation": "Korrelation",
    "tab_costs": "Kosten & Struktur",
    "tab_cycles": "Zyklen & Saisonalität",
    "tab_strategy": "Strategie",
    "tab_forecast": "Prognose",
    "tab_data": "Daten & Methodik",
    "m_total_return": "Gesamtrendite",
    "m_cagr": "CAGR",
    "m_volatility": "Volatilität (p.a.)",
    "m_downside": "Abwärtsabweichung",
    "m_maxdd": "Maximaler Drawdown",
    "m_sharpe": "Sharpe",
    "m_sortino": "Sortino",
    "m_calmar": "Calmar",
    "m_omega": "Omega",
    "m_ulcer": "Ulcer-Index",
    "m_martin": "Martin-Ratio",
    "m_stability": "Trendstabilität",
    "m_var": "VaR 95% (täglich)",
    "m_cvar": "CVaR 95% (täglich)",
    "m_skew": "Schiefe",
    "m_kurtosis": "Wölbung",
    "m_tail": "Tail-Ratio",
    "m_hit": "Positive Tage",
    "m_beta": "Beta",
    "m_alpha": "Alpha (p.a.)",
    "m_r2": "R²",
    "m_te": "Tracking Error",
    "m_ir": "Information Ratio",
    "m_up": "Aufwärtspartizipation",
    "m_down": "Abwärtspartizipation",
    "m_capture_spread": "Partizipationsdifferenz",
    "m_batting": "Trefferquote vs. Index",
    "m_ter": "Gesamtkostenquote (TER)",
    "m_score": "Gesamtscore",
    "m_rank": "Rang",
    "m_obs": "Beobachtungen",
    "m_first": "Von",
    "m_last": "Bis",
    "m_name": "Name",
    "m_best_day": "Bester Tag",
    "m_worst_day": "Schlechtester Tag",
    "h_kpi": "Kennzahlen",
    "h_leaderboard": "Gesamtrangliste",
    "h_growth": "Vermögensentwicklung (Basis 100)",
    "h_period_returns": "Renditen nach Zeitraum",
    "h_calendar": "Kalenderjahresrenditen",
    "h_rolling": "Rollierende Renditen",
    "h_drawdown": "Drawdown vom Höchststand",
    "h_dd_table": "Tiefste Drawdown-Phasen",
    "h_riskmetrics": "Risikokennzahlen",
    "h_scatter": "Risiko-Rendite-Karte",
    "h_frontier": "Effizienzkurve",
    "h_alpha": "Alpha, Beta und Tracking",
    "h_capture": "Auf- und Abwärtspartizipation",
    "h_te": "Tracking Error im Zeitverlauf",
    "h_region": "Performance nach Region",
    "h_market_matrix": "Marktmatrix",
    "h_currency_effect": "Währungseffekt",
    "h_corr": "Korrelationsmatrix",
    "h_corr_rolling": "Rollierende Korrelation zur Benchmark",
    "h_fees": "Gebühren und Renditeerosion",
    "h_liquidity": "Liquidität",
    "h_ter_vs_perf": "Kosten gegen Performance",
    "h_monthly": "Heatmap der Monatsrenditen",
    "h_bullbear": "Verhalten im Bullen- und Bärenmarkt",
    "h_seasonality": "Saisonalität",
    "h_dca": "Sparplan (DCA)",
    "h_lsdca": "Einmalanlage gegen Sparplan",
    "h_portfolio": "Rebalanciertes Portfolio",
    "h_forecast": "Trendprognose",
    "h_montecarlo": "Monte-Carlo-Simulation",
    "h_quality": "Datenqualität",
    "h_method": "Methodik",
    "h_universe": "Anlageuniversum",
    "h_export": "Export",
    "c_window_years": "Fensterlänge (Jahre)",
    "c_contribution": "Betrag je Periode",
    "c_frequency": "Frequenz",
    "c_monthly": "Monatlich",
    "c_weekly": "Wöchentlich",
    "c_hold_years": "Haltedauer (Jahre)",
    "c_spread_months": "Monate zur Verteilung des Kapitals",
    "c_horizon": "Prognosehorizont (Tage)",
    "c_gross_return": "Angenommene Bruttorendite (% p.a.)",
    "c_years": "Jahre",
    "c_initial": "Startkapital",
    "c_pick_one": "Ein Instrument wählen",
    "c_show_table": "Datentabelle anzeigen",
    "c_rebalance": "Rebalancing-Frequenz",
    "c_quarterly": "Quartalsweise",
    "c_annually": "Jährlich",
    "c_download_csv": "Kennzahlen herunterladen (CSV)",
    "c_download_report": "Bericht herunterladen (Markdown)",
    "x_date": "Datum",
    "x_vol": "Jahresvolatilität (%)",
    "y_return": "Rendite (%)",
    "y_cagr": "CAGR (%)",
    "y_dd": "Drawdown (%)",
    "y_value": "Wert",
    "y_te": "Tracking Error (%)",
    "y_volume": "Volumen",
    "n_funds": "Fonds",
    "n_instruments": "Instrumente",
    "n_markets": "Märkte",
    "n_currencies": "Währungen",
    "insight": "Lesehilfe",
    "auto_commentary": "Kommentar",
    "bull": "Bullenmarkt",
    "bear": "Bärenmarkt",
    "best": "Bester",
    "worst": "Schlechtester",
    "median": "Median",
    "average": "Durchschnitt",
    "win_rate": "Trefferquote",
    "windows": "Fenster",
    "prob_up": "Gewinnwahrscheinlichkeit",
    "invested": "Eingezahlt",
    "value": "Wert",
    "profit": "Gewinn / Verlust",
    "lump_sum": "Einmalanlage",
    "dca": "Sparplan",
    "gross": "Vor Kosten",
    "net": "Nach Kosten",
    "fees_lost": "Durch Kosten verloren",
    "stale_warning": "Diese Ticker sind mehr als 7 Tage veraltet",
    "fx_warning": "Für diese Währungen fehlt ein Kurs, die Preise bleiben in Landeswährung",
    "no_selection": "Bitte links mindestens einen Fonds oder Index auswählen.",
    "not_enough_data": "Für diese Auswahl liegen zu wenige Daten vor.",
    "x_growth": """
- **Lesart:** Jede Linie startet am ersten Tag des Zeitraums bei 100. Die oberste Linie hat das meiste Vermögen aufgebaut.
- **Gegen die Benchmark:** Eine Linie unterhalb der Benchmark bedeutet, dass der Fonds nach Kosten hinter dem Markt liegt.
- **Währung:** Alles ist in die Berichtswährung umgerechnet, Wechselkurseffekte sind also enthalten.
""",
    "x_periods": """
- Zeiträume ab drei Jahren erscheinen als **jährliche Wachstumsrate (CAGR)**, kürzere als absolute Rendite.
- Innerhalb einer Spalte vergleichen, nicht über Spalten hinweg: ein junger Fonds hat keinen Zehnjahreswert.
""",
    "x_drawdown": """
- **Drawdown** misst den Verlust vom letzten Höchststand — der Schmerz, den das Halten kostet.
- **-20%** Verlust brauchen **+25%** zum Ausgleich, **-50%** brauchen **+100%**.
- Gute Fonds zeigen flachere Täler und erholen sich schneller als der Index im selben Zeitraum.
""",
    "x_riskreturn": """
- Die **linke obere Ecke** ist der ideale Bereich: hohe Rendite bei geringer Schwankung.
- **Sharpe** misst Überrendite je Risikoeinheit, **Sortino** bestraft nur Abwärtsvolatilität.
- **Calmar** setzt die Rendite ins Verhältnis zum schlimmsten Drawdown.
""",
    "x_benchmark": """
- **Beta > 1** verstärkt den Index, **Beta < 1** wirkt defensiv.
- **Alpha > 0** ist die Rendite, die nach Bezahlung des Marktrisikos übrig bleibt.
- Ein niedriger **Tracking Error** zeigt eine präzise Indexabbildung; ein ungewöhnlich hoher deutet auf versteckte Kosten oder Drift hin.
- **Information Ratio** = Alpha geteilt durch Tracking Error: die Qualität dieser Überrendite.
""",
    "x_markets": """
- Marktübergreifender Vergleich, nachdem jeder Kurs in eine gemeinsame Währung umgerechnet wurde.
- Ein Markt kann in Landeswährung steigen und für ausländische Anleger dennoch Verlust bedeuten, wenn die Währung abwertet.
""",
    "x_correlation": """
- Geringe Korrelation zwischen den Positionen ist die Quelle echter Diversifikation.
- Koeffizient nahe **1**: beide Fonds laufen gleich, das Halten beider bringt keinen Schutz.
- Koeffizient **unter 0,5** oder negativ: fällt der eine, kann der andere stabil bleiben.
""",
    "x_costs": """
- Die **TER** wird täglich vom NAV abgezogen. Sie steht auf keiner Abrechnung, wirkt aber gegen den Zinseszins.
- Ein halbes Prozent pro Jahr kann über zwanzig Jahre mehr als 10% des Endvermögens kosten.
- Dünne Liquidität verursacht zusätzliche versteckte Kosten durch Slippage.
""",
    "x_cycles": """
- **Aufwärtspartizipation** über 100% heißt: der Fonds steigt an guten Tagen stärker als der Index.
- **Abwärtspartizipation** unter 100% heißt: er fällt weniger stark — ein defensives Profil.
- Die Monats-Heatmap zeigt, welche Jahresabschnitte historisch günstig waren.
""",
    "x_strategy": """
- **Sparplan** verteilt den Einstieg über die Zeit, senkt das Timing-Risiko und meist auch die erwartete Rendite.
- **Einmalanlage** gewinnt statistisch häufiger, weil Märkte öfter steigen als fallen — um den Preis größerer Schwankungen.
- Die Tabelle rollt den Vergleich über die gesamte Historie: jedes Startdatum ist ein eigenes Szenario.
""",
    "x_forecast": """
- **Monte Carlo** zieht tausende Pfade aus der historischen Renditeverteilung.
- **ETS** extrapoliert einen gedämpften Trend aus der Zeitreihe selbst.
- Eine Prognose ist eine Wahrscheinlichkeitsverteilung auf Basis der Vergangenheit; Makroschocks liegen außerhalb des Modells.
""",
    "x_data": """
- Vietnamesische Daten stammen von VNDIRECT (ETFs, Indizes) und fmarket.vn (Publikumsfonds), Weltdaten von Yahoo Finance mit Stooq als Reserve.
- Weltkurse sind dividenden- und splitbereinigt; Fondswerte sind der veröffentlichte NAV.
- Tägliche Wechselkurse rechnen jedes Papier in eine einheitliche Berichtswährung um.
""",
}


def t(lang: str, key: str) -> str:
    """Translate ``key``; falls back to English and finally to the key itself."""
    return STRINGS.get(lang, STRINGS["EN"]).get(key, STRINGS["EN"].get(key, key))


def missing_keys() -> dict[str, list[str]]:
    """Keys present in English but missing in another language (used by tests)."""
    base = set(STRINGS["EN"])
    return {lang: sorted(base - set(STRINGS[lang])) for lang in STRINGS if lang != "EN"}


# ===========================================================================
# automated, data-driven commentary
# ===========================================================================

def _pct(x: float, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "n/a"
    return f"{x * 100:.{digits}f}%"


def _num(x: float, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "n/a"
    return f"{x:.{digits}f}"


def summary_narrative(lang: str, facts: dict) -> str:
    """Executive commentary generated from the computed facts of the window."""
    f = facts
    if lang == "VI":
        return (
            f"Trong khung thời gian đang xem ({f['start']} → {f['end']}, quy đổi về {f['currency']}), "
            f"**{f['best']}** dẫn đầu với CAGR {_pct(f['best_cagr'])}, trong khi **{f['worst']}** ở cuối bảng "
            f"với {_pct(f['worst_cagr'])}. "
            f"Có {f['beat_count']}/{f['total']} công cụ vượt chỉ số tham chiếu **{f['benchmark']}** "
            f"({_pct(f['benchmark_cagr'])}). "
            f"Hiệu quả điều chỉnh rủi ro tốt nhất thuộc về **{f['best_sharpe']}** (Sharpe {_num(f['best_sharpe_value'])}), "
            f"còn **{f['deepest_dd']}** chịu mức sụt giảm sâu nhất {_pct(f['deepest_dd_value'])}. "
            f"Tương quan trung bình giữa các lựa chọn là {_num(f['avg_corr'])}, "
            f"{'mức phân tán rủi ro còn hạn chế' if f['avg_corr'] > 0.7 else 'đủ để mang lại lợi ích đa dạng hóa'}."
        )
    if lang == "DE":
        return (
            f"Im gewählten Zeitraum ({f['start']} → {f['end']}, umgerechnet in {f['currency']}) führt "
            f"**{f['best']}** mit einer CAGR von {_pct(f['best_cagr'])}, während **{f['worst']}** mit "
            f"{_pct(f['worst_cagr'])} das Schlusslicht bildet. "
            f"{f['beat_count']} von {f['total']} Instrumenten schlagen die Benchmark **{f['benchmark']}** "
            f"({_pct(f['benchmark_cagr'])}). "
            f"Die beste risikoadjustierte Rendite liefert **{f['best_sharpe']}** (Sharpe {_num(f['best_sharpe_value'])}); "
            f"den tiefsten Drawdown trägt **{f['deepest_dd']}** mit {_pct(f['deepest_dd_value'])}. "
            f"Die durchschnittliche Korrelation der Auswahl liegt bei {_num(f['avg_corr'])} — "
            f"{'der Diversifikationseffekt ist damit begrenzt' if f['avg_corr'] > 0.7 else 'das reicht für einen spürbaren Diversifikationseffekt'}."
        )
    return (
        f"Over the selected window ({f['start']} → {f['end']}, converted to {f['currency']}), "
        f"**{f['best']}** leads with a CAGR of {_pct(f['best_cagr'])}, while **{f['worst']}** trails at "
        f"{_pct(f['worst_cagr'])}. "
        f"{f['beat_count']} of {f['total']} instruments beat the **{f['benchmark']}** benchmark "
        f"({_pct(f['benchmark_cagr'])}). "
        f"The best risk-adjusted result belongs to **{f['best_sharpe']}** (Sharpe {_num(f['best_sharpe_value'])}), "
        f"and **{f['deepest_dd']}** carries the deepest drawdown at {_pct(f['deepest_dd_value'])}. "
        f"Average pairwise correlation is {_num(f['avg_corr'])}, "
        f"{'so the diversification benefit is limited' if f['avg_corr'] > 0.7 else 'enough for a real diversification benefit'}."
    )


def tracking_narrative(lang: str, ticker: str, te: float, ir: float,
                       beta: float, alpha: float, benchmark: str) -> str:
    quality = {
        "VI": ("bám sát rất tốt", "bám sát ở mức chấp nhận được", "lệch đáng kể"),
        "EN": ("tracks its index tightly", "tracks acceptably", "drifts noticeably"),
        "DE": ("bildet den Index eng ab", "bildet den Index akzeptabel ab", "weicht spürbar ab"),
    }[lang if lang in ("VI", "EN", "DE") else "EN"]
    label = quality[0] if te < 0.02 else quality[1] if te < 0.05 else quality[2]
    if lang == "VI":
        return (f"**{ticker}** {label} so với **{benchmark}**: sai số bám {_pct(te)}, beta {_num(beta)}, "
                f"alpha {_pct(alpha)} mỗi năm, Information Ratio {_num(ir)}.")
    if lang == "DE":
        return (f"**{ticker}** {label} gegenüber **{benchmark}**: Tracking Error {_pct(te)}, Beta {_num(beta)}, "
                f"Alpha {_pct(alpha)} p.a., Information Ratio {_num(ir)}.")
    return (f"**{ticker}** {label} against **{benchmark}**: tracking error {_pct(te)}, beta {_num(beta)}, "
            f"alpha {_pct(alpha)} p.a., information ratio {_num(ir)}.")


def market_narrative(lang: str, best_region: str, best_value: float,
                     worst_region: str, worst_value: float, currency: str) -> str:
    if lang == "VI":
        return (f"Tính theo {currency}, khu vực **{best_region}** dẫn đầu với lợi nhuận trung vị "
                f"{_pct(best_value)}, trong khi **{worst_region}** thấp nhất ở {_pct(worst_value)}.")
    if lang == "DE":
        return (f"Gerechnet in {currency} führt die Region **{best_region}** mit einer Medianrendite "
                f"von {_pct(best_value)}, **{worst_region}** liegt mit {_pct(worst_value)} am Ende.")
    return (f"Measured in {currency}, **{best_region}** leads with a median return of {_pct(best_value)}, "
            f"while **{worst_region}** is last at {_pct(worst_value)}.")


def drawdown_narrative(lang: str, ticker: str, current_dd: float, max_dd: float,
                       recovery_days: float | None) -> str:
    rec = "n/a" if recovery_days is None or (isinstance(recovery_days, float) and math.isnan(recovery_days)) \
        else f"{int(recovery_days)}"
    if lang == "VI":
        return (f"**{ticker}** đang thấp hơn đỉnh {_pct(abs(current_dd))}; mức sụt giảm sâu nhất trong kỳ là "
                f"{_pct(max_dd)} và lần hồi phục gần nhất mất {rec} ngày.")
    if lang == "DE":
        return (f"**{ticker}** liegt {_pct(abs(current_dd))} unter dem Höchststand; der tiefste Drawdown im "
                f"Zeitraum betrug {_pct(max_dd)}, die letzte Erholung dauerte {rec} Tage.")
    return (f"**{ticker}** sits {_pct(abs(current_dd))} below its peak; the deepest drawdown in the window was "
            f"{_pct(max_dd)} and the last recovery took {rec} days.")


def strategy_narrative(lang: str, win_rate: float, median_lump: float,
                       median_dca: float, hold_years: int) -> str:
    if lang == "VI":
        return (f"Trên toàn bộ lịch sử, đầu tư một lần thắng DCA trong {_num(win_rate, 1)}% số kịch bản "
                f"nắm giữ {hold_years} năm (trung vị {_pct(median_lump)} so với {_pct(median_dca)}).")
    if lang == "DE":
        return (f"Über die gesamte Historie schlägt die Einmalanlage den Sparplan in {_num(win_rate, 1)}% der "
                f"Szenarien mit {hold_years} Jahren Haltedauer (Median {_pct(median_lump)} gegen {_pct(median_dca)}).")
    return (f"Across the full history, lump sum beats DCA in {_num(win_rate, 1)}% of {hold_years}-year holding "
            f"scenarios (median {_pct(median_lump)} versus {_pct(median_dca)}).")


def cost_narrative(lang: str, ticker: str, ter: float, lost_pct: float, years: int) -> str:
    if lang == "VI":
        return (f"Với phí {_num(ter, 2)}%/năm, sau {years} năm **{ticker}** để lại khoảng {_pct(lost_pct)} "
                f"tài sản cuối kỳ cho chi phí.")
    if lang == "DE":
        return (f"Bei {_num(ter, 2)}% Kosten pro Jahr kostet **{ticker}** nach {years} Jahren rund "
                f"{_pct(lost_pct)} des Endvermögens.")
    return (f"At {_num(ter, 2)}% a year, after {years} years **{ticker}** gives up about {_pct(lost_pct)} "
            f"of the final portfolio to costs.")


def forecast_narrative(lang: str, ticker: str, prob_up: float, expected: float,
                       p05: float, p95: float, days: int) -> str:
    if lang == "VI":
        return (f"Mô phỏng {days} phiên tới cho **{ticker}**: xác suất tăng {_num(prob_up, 1)}%, "
                f"lợi nhuận trung vị {_pct(expected)}, khoảng tin cậy 90% từ {_num(p05, 0)} đến {_num(p95, 0)}.")
    if lang == "DE":
        return (f"Simulation der nächsten {days} Handelstage für **{ticker}**: Gewinnwahrscheinlichkeit "
                f"{_num(prob_up, 1)}%, Medianrendite {_pct(expected)}, 90%-Band von {_num(p05, 0)} bis {_num(p95, 0)}.")
    return (f"Simulating the next {days} trading days for **{ticker}**: {_num(prob_up, 1)}% chance of a gain, "
            f"median return {_pct(expected)}, 90% band from {_num(p05, 0)} to {_num(p95, 0)}.")


def quality_narrative(lang: str, instruments: int, markets: int, currencies: int,
                      last_date: str, stale: int) -> str:
    if lang == "VI":
        return (f"Bộ dữ liệu gồm {instruments} công cụ trên {markets} thị trường và {currencies} đồng tiền, "
                f"cập nhật đến {last_date}; {stale} mã chậm hơn 7 ngày.")
    if lang == "DE":
        return (f"Der Datensatz umfasst {instruments} Instrumente aus {markets} Märkten und {currencies} Währungen, "
                f"Stand {last_date}; {stale} Ticker sind älter als 7 Tage.")
    return (f"The dataset covers {instruments} instruments across {markets} markets and {currencies} currencies, "
            f"updated to {last_date}; {stale} tickers are more than 7 days stale.")


# ===========================================================================
# chart readouts — one sentence per chart, written from that chart's numbers
# ===========================================================================

MONTHS = {
    "VI": ["Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9",
           "Th10", "Th11", "Th12"],
    "EN": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
           "Oct", "Nov", "Dec"],
    "DE": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep",
           "Okt", "Nov", "Dez"],
}


def month_name(lang: str, month: int) -> str:
    names = MONTHS.get(lang, MONTHS["EN"])
    return names[int(month) - 1] if 1 <= int(month) <= 12 else str(month)


def _pick(lang: str, vi: str, en: str, de: str) -> str:
    return {"VI": vi, "EN": en, "DE": de}.get(lang, en)


def performance_readout(lang, best, best_ret, worst, worst_ret, bench,
                        bench_ret, beat, total):
    return _pick(
        lang,
        f"**{best}** tạo ra nhiều tài sản nhất ({_pct(best_ret)}), **{worst}** ít nhất "
        f"({_pct(worst_ret)}); {beat}/{total} công cụ vượt **{bench}** ({_pct(bench_ret)}). "
        f"Khoảng cách giữa đầu và cuối bảng là {_pct(best_ret - worst_ret)}.",
        f"**{best}** built the most wealth ({_pct(best_ret)}) and **{worst}** the least "
        f"({_pct(worst_ret)}); {beat} of {total} beat **{bench}** ({_pct(bench_ret)}). "
        f"The spread between first and last is {_pct(best_ret - worst_ret)}.",
        f"**{best}** hat am meisten Vermögen aufgebaut ({_pct(best_ret)}), **{worst}** am "
        f"wenigsten ({_pct(worst_ret)}); {beat} von {total} schlagen **{bench}** "
        f"({_pct(bench_ret)}). Der Abstand beträgt {_pct(best_ret - worst_ret)}.")


def drawdown_readout(lang, deepest, deepest_value, shallowest, shallowest_value,
                     current_worst, current_worst_value):
    return _pick(
        lang,
        f"Trong kỳ, **{deepest}** chịu đáy sâu nhất {_pct(deepest_value)} còn **{shallowest}** "
        f"chỉ {_pct(shallowest_value)}. Hiện **{current_worst}** đang xa đỉnh nhất, "
        f"thấp hơn {_pct(abs(current_worst_value))}.",
        f"**{deepest}** fell furthest at {_pct(deepest_value)} while **{shallowest}** only "
        f"gave up {_pct(shallowest_value)}. Right now **{current_worst}** sits furthest from "
        f"its peak, {_pct(abs(current_worst_value))} below it.",
        f"**{deepest}** fiel am tiefsten ({_pct(deepest_value)}), **{shallowest}** nur "
        f"{_pct(shallowest_value)}. Aktuell liegt **{current_worst}** am weitesten unter "
        f"seinem Höchststand, {_pct(abs(current_worst_value))} darunter.")


def positioning_readout(lang, efficient, sharpe_value, highest, highest_ret,
                        riskiest, riskiest_vol):
    return _pick(
        lang,
        f"**{efficient}** đổi rủi ro lấy lợi nhuận hiệu quả nhất (Sharpe {_num(sharpe_value)}). "
        f"**{highest}** lãi cao nhất ({_pct(highest_ret)}), còn **{riskiest}** biến động mạnh "
        f"nhất ({_pct(riskiest_vol)}) — hai điều đó thường đi cùng nhau.",
        f"**{efficient}** converts risk into return most efficiently (Sharpe {_num(sharpe_value)}). "
        f"**{highest}** returned the most ({_pct(highest_ret)}) and **{riskiest}** swung hardest "
        f"({_pct(riskiest_vol)}) — usually the same story from two sides.",
        f"**{efficient}** setzt Risiko am effizientesten in Rendite um (Sharpe {_num(sharpe_value)}). "
        f"**{highest}** brachte die höchste Rendite ({_pct(highest_ret)}), **{riskiest}** schwankte "
        f"am stärksten ({_pct(riskiest_vol)}) — meist zwei Seiten derselben Sache.")


def capture_readout(lang, best_up, up_value, best_down, down_value, benchmark):
    return _pick(
        lang,
        f"So với **{benchmark}**: **{best_up}** bám sóng tăng tốt nhất ({_num(up_value, 0)}% mức "
        f"tăng của chỉ số), **{best_down}** phòng thủ tốt nhất khi giảm (chỉ {_num(down_value, 0)}% "
        f"mức giảm). Quỹ lý tưởng có cột xanh cao và cột đỏ thấp.",
        f"Against **{benchmark}**: **{best_up}** captures the most upside ({_num(up_value, 0)}% of "
        f"the index's rise) and **{best_down}** defends best on the way down (only "
        f"{_num(down_value, 0)}% of the fall). You want a tall green bar and a short red one.",
        f"Gegen **{benchmark}**: **{best_up}** nimmt am meisten Aufwärtsbewegung mit "
        f"({_num(up_value, 0)}%), **{best_down}** verteidigt am besten nach unten (nur "
        f"{_num(down_value, 0)}%). Ideal ist ein hoher grüner und ein kurzer roter Balken.")


def correlation_readout(lang, average, low_a, low_b, low_value, high_a, high_b,
                        high_value):
    verdict = _pick(
        lang,
        "phần lớn danh sách đang di chuyển cùng nhau, nên lợi ích đa dạng hóa còn mỏng"
        if average > 0.7 else "danh sách đủ khác nhau để việc nắm nhiều mã thực sự giảm rủi ro",
        "most of the list moves together, so the diversification benefit is thin"
        if average > 0.7 else "the list is varied enough that holding several genuinely cuts risk",
        "die Auswahl bewegt sich weitgehend gemeinsam, der Diversifikationseffekt ist dünn"
        if average > 0.7 else "die Auswahl ist unterschiedlich genug, dass mehrere Positionen das Risiko wirklich senken")
    return _pick(
        lang,
        f"Tương quan trung bình {_num(average)} — {verdict}. Cặp ít liên quan nhất là "
        f"**{low_a}** / **{low_b}** ({_num(low_value)}); giống nhau nhất là **{high_a}** / "
        f"**{high_b}** ({_num(high_value)}).",
        f"Average correlation is {_num(average)} — {verdict}. The least related pair is "
        f"**{low_a}** / **{low_b}** ({_num(low_value)}); the most alike are **{high_a}** / "
        f"**{high_b}** ({_num(high_value)}).",
        f"Die durchschnittliche Korrelation liegt bei {_num(average)} — {verdict}. Das am "
        f"wenigsten verbundene Paar ist **{low_a}** / **{low_b}** ({_num(low_value)}), am "
        f"ähnlichsten sind **{high_a}** / **{high_b}** ({_num(high_value)}).")


def heatmap_readout(lang, ticker, best_month, best_value, worst_month,
                    worst_value, positive_share, best_year, best_year_value):
    return _pick(
        lang,
        f"**{ticker}** tăng trong {_num(positive_share, 0)}% số tháng. Tháng **{best_month}** "
        f"thường tốt nhất (trung bình {_num(best_value, 1)}%), **{worst_month}** kém nhất "
        f"({_num(worst_value, 1)}%). Năm mạnh nhất là **{best_year}** với {_pct(best_year_value)}.",
        f"**{ticker}** rose in {_num(positive_share, 0)}% of months. **{best_month}** is "
        f"historically its best month (avg {_num(best_value, 1)}%) and **{worst_month}** its "
        f"weakest ({_num(worst_value, 1)}%). Its strongest year was **{best_year}** at "
        f"{_pct(best_year_value)}.",
        f"**{ticker}** stieg in {_num(positive_share, 0)}% der Monate. **{best_month}** ist "
        f"historisch der beste Monat (Ø {_num(best_value, 1)}%), **{worst_month}** der "
        f"schwächste ({_num(worst_value, 1)}%). Stärkstes Jahr: **{best_year}** mit "
        f"{_pct(best_year_value)}.")


def calendar_readout(lang, best_year, best_value, worst_year, worst_value,
                     positive_years, total_years):
    return _pick(
        lang,
        f"Trong {total_years} năm có dữ liệu, {positive_years} năm dương. Tốt nhất là "
        f"**{best_year}** ({_pct(best_value)}), tệ nhất **{worst_year}** ({_pct(worst_value)}).",
        f"Of {total_years} calendar years, {positive_years} were positive. The best was "
        f"**{best_year}** ({_pct(best_value)}), the worst **{worst_year}** ({_pct(worst_value)}).",
        f"Von {total_years} Kalenderjahren waren {positive_years} positiv. Das beste war "
        f"**{best_year}** ({_pct(best_value)}), das schlechteste **{worst_year}** "
        f"({_pct(worst_value)}).")


def rolling_readout(lang, ticker, years, win_rate, median, worst):
    return _pick(
        lang,
        f"Với mọi thời điểm mua trong quá khứ, **{ticker}** nắm giữ {years} năm sinh lời "
        f"{_num(win_rate, 0)}% số lần; trung vị {_pct(median)}, kịch bản xấu nhất {_pct(worst)}.",
        f"Across every possible entry date, holding **{ticker}** for {years} years was "
        f"profitable {_num(win_rate, 0)}% of the time; median {_pct(median)}, worst case "
        f"{_pct(worst)}.",
        f"Über alle möglichen Einstiegszeitpunkte war **{ticker}** über {years} Jahre in "
        f"{_num(win_rate, 0)}% der Fälle im Plus; Median {_pct(median)}, schlimmster Fall "
        f"{_pct(worst)}.")


def screener_readout(lang, shown, total, top, top_value, sort_label, median_cagr,
                     median_ter, as_percent: bool = True):
    """Names the sort it actually used, so "leads" cannot mean the wrong column.

    Whether the leading value is a percentage or a ratio is the caller's to say:
    guessing from the magnitude turns a Sharpe of 1.82 into "182%".
    """
    value = _pct(top_value) if as_percent else _num(top_value)
    return _pick(
        lang,
        f"{shown}/{total} công cụ qua bộ lọc. Đứng đầu theo **{sort_label}** là **{top}** "
        f"({value}); trung vị nhóm: CAGR {_pct(median_cagr)}, phí {_num(median_ter)}%/năm.",
        f"{shown} of {total} instruments pass. Top by **{sort_label}** is **{top}** ({value}); "
        f"the group median is {_pct(median_cagr)} CAGR at {_num(median_ter)}% a year in fees.",
        f"{shown} von {total} Instrumenten passen. Spitzenreiter nach **{sort_label}** ist "
        f"**{top}** ({value}); Median der Gruppe: {_pct(median_cagr)} CAGR bei "
        f"{_num(median_ter)}% Kosten p.a.")


def portfolio_readout(lang, cagr, volatility, drawdown, top_risk, top_risk_share,
                      top_weight):
    return _pick(
        lang,
        f"Danh mục đạt {_pct(cagr)} mỗi năm với biến động {_pct(volatility)} và đáy "
        f"{_pct(drawdown)}. **{top_risk}** chiếm {_num(top_risk_share * 100, 0)}% rủi ro dù chỉ "
        f"{_num(top_weight * 100, 0)}% tỷ trọng — đó mới là vị thế quyết định.",
        f"The portfolio returned {_pct(cagr)} a year with {_pct(volatility)} volatility and a "
        f"{_pct(drawdown)} trough. **{top_risk}** carries {_num(top_risk_share * 100, 0)}% of the "
        f"risk on {_num(top_weight * 100, 0)}% of the weight — that is the position that decides "
        f"the outcome.",
        f"Das Portfolio erzielte {_pct(cagr)} p.a. bei {_pct(volatility)} Volatilität und einem "
        f"Tief von {_pct(drawdown)}. **{top_risk}** trägt {_num(top_risk_share * 100, 0)}% des "
        f"Risikos bei {_num(top_weight * 100, 0)}% Gewicht — diese Position entscheidet.")


def country_readout(lang, best, best_value, worst, worst_value, count, currency):
    return _pick(
        lang,
        f"Trong {count} thị trường, **{best}** dẫn đầu ({_pct(best_value)} tính bằng {currency}) "
        f"và **{worst}** ở cuối ({_pct(worst_value)}). Chênh lệch này đã bao gồm cả biến động tỷ giá.",
        f"Across {count} markets, **{best}** leads ({_pct(best_value)} in {currency}) and "
        f"**{worst}** trails ({_pct(worst_value)}). That gap already includes the currency move.",
        f"Über {count} Märkte führt **{best}** ({_pct(best_value)} in {currency}), **{worst}** "
        f"bildet das Schlusslicht ({_pct(worst_value)}). Die Währungsbewegung steckt darin.")


def currency_readout(lang, ticker, local, converted, currency):
    delta = converted - local
    direction = _pick(lang,
                      "cộng thêm" if delta >= 0 else "lấy đi",
                      "added" if delta >= 0 else "took away",
                      "brachte zusätzlich" if delta >= 0 else "kostete")
    return _pick(
        lang,
        f"Với **{ticker}**, quy đổi sang {currency} {direction} {_pct(abs(delta))} mỗi năm so với "
        f"lợi nhuận tính bằng nội tệ ({_pct(local)} → {_pct(converted)}).",
        f"For **{ticker}**, converting into {currency} {direction} {_pct(abs(delta))} a year versus "
        f"the local-currency return ({_pct(local)} → {_pct(converted)}).",
        f"Bei **{ticker}** {direction} die Umrechnung in {currency} {_pct(abs(delta))} p.a. "
        f"gegenüber der Rendite in Landeswährung ({_pct(local)} → {_pct(converted)}).")


def freshness_label(lang: str, days: int) -> tuple[str, str]:
    """(text, css class) for the data freshness pill."""
    if days <= 1:
        return t(lang, "fresh_today"), "fresh-ok"
    if days <= 4:
        return t(lang, "fresh_days").format(n=days), "fresh-warn"
    return t(lang, "fresh_stale").format(n=days), "fresh-old"


def excess_readout(lang, ticker, average, share_ahead, benchmark):
    return _pick(
        lang,
        f"Tính trên mọi cửa sổ 12 tháng, **{ticker}** vượt **{benchmark}** trung bình "
        f"{_pct(average)} và đi trước trong {_num(share_ahead, 0)}% thời gian. Khoảng thời "
        f"gian dưới vạch 0 là lúc nắm giữ nó khó chịu nhất, dù kết quả cuối kỳ có đẹp.",
        f"Across every 12-month window, **{ticker}** beat **{benchmark}** by {_pct(average)} "
        f"on average and was ahead {_num(share_ahead, 0)}% of the time. The stretches below "
        f"zero are when holding it hurt, whatever the final total says.",
        f"Über alle 12-Monats-Fenster schlug **{ticker}** die Benchmark **{benchmark}** um "
        f"durchschnittlich {_pct(average)} und lag {_num(share_ahead, 0)}% der Zeit vorn. Die "
        f"Phasen unter null sind die, in denen das Halten wehtat — unabhängig vom Endergebnis.")
