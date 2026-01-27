import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import subprocess
import sys

# ==========================================
# 1. TỪ ĐIỂN NGÔN NGỮ CHUYÊN SÂU
# ==========================================
LANG = {
    "VN": {
        "page_title": "Trung tâm Phân tích ETF Việt Nam",
        "sidebar_settings": "Cấu hình",
        "data_updated": "Dữ liệu cập nhật đến",
        "manager": "Nhà quản lý",
        "select_ticker": "Chọn Mã Quỹ",
        "time_range": "Khung thời gian",
        "update_btn": "Cập nhật Dữ liệu",
        "loading": "Đang tải dữ liệu...",
        "success_update": "Đã cập nhật xong! Nhấn 'R' để tải lại.",
        "tab_perf": "Hiệu Suất", "tab_risk": "Rủi Ro", "tab_rr": "Risk-Return",
        "tab_trend": "Xu Hướng", "tab_corr": "Tương Quan", "tab_struct": "Cấu Trúc",
        "tab_cycle": "Chu Kỳ", "tab_forecast": "Dự Báo",
        "chart_cum_ret": "Tăng trưởng tài sản lũy kế",
        "chart_dd": "Mức sụt giảm từ đỉnh (Drawdown)",
        "chart_rr": "Vị thế Rủi ro vs Lợi nhuận",
        "chart_trend": "Phân tích Xu hướng Giá",
        "chart_corr": "Ma trận Tương quan Biến động",
        "chart_te": "Tracking Error (Độ lệch chuẩn)",
        "chart_vol": "Thanh khoản (Volume)",
        "chart_bb": "Hiệu suất Bull vs Bear",
        "chart_forecast": "Dự báo Xu hướng (ETS)",
        "metric_ret": "Lợi nhuận", "metric_vol": "Biến động (Năm)", 
        "metric_sharpe": "Sharpe Ratio", "metric_alpha": "Alpha", "metric_beta": "Beta",
        "interp_title": "💡 Phân tích chuyên sâu:",
        "interp_perf": """
        - **Ý nghĩa:** Biểu đồ giả định khoản đầu tư 100 đơn vị tiền tệ vào đầu kỳ. Đường nằm trên cùng là quỹ có hiệu suất tốt nhất.
        - **So sánh:** Nếu đường của quỹ (Line) nằm dưới đường VNINDEX/VN30, quỹ đó đang hoạt động kém hơn thị trường (Underperform).
        - **Lãi kép:** Độ dốc của đường biểu diễn sức mạnh của lãi kép. Dốc càng đứng, đà tăng trưởng càng mạnh.
        """,
        "interp_risk": """
        - **Drawdown là gì?** Là mức sụt giảm tính từ đỉnh cao nhất gần đó. Nó đo lường "nỗi đau" tối đa nhà đầu tư phải chịu đựng.
        - **Toán học về lỗ:** Nếu tài khoản lỗ **-20%**, bạn cần lãi **+25%** để hòa vốn. Nếu lỗ **-50%**, bạn cần lãi **+100%**.
        - **Đánh giá:** Quỹ tốt là quỹ có mức sụt giảm (đáy của vùng màu) nông hơn so với thị trường chung trong các đợt khủng hoảng.
        """,
        "interp_rr": """
        - **Vùng lý tưởng:** Góc trên bên trái (Lợi nhuận cao - Rủi ro thấp). Các quỹ nằm ở đây là "hàng tuyển".
        - **Sharpe Ratio:** Đo lường hiệu quả. Sharpe > 1 là Tốt, > 2 là Xuất sắc. Nó trả lời: "Chấp nhận thêm 1 đơn vị rủi ro thì thu về bao nhiêu đơn vị lợi nhuận?".
        - **Alpha & Beta:** * **Alpha > 0:** Quỹ có khả năng "chiến thắng" thị trường nhờ kỹ năng quản lý.
            * **Beta < 1:** Quỹ biến động ít hơn thị trường (Phòng thủ). **Beta > 1:** Quỹ biến động mạnh hơn (Tấn công).
        """,
        "interp_trend": """
        - **Golden Cross (Giao cắt vàng):** Khi đường Vàng (MA50 - Trung hạn) cắt lên trên đường Đỏ (MA200 - Dài hạn) → Tín hiệu xác nhận xu hướng Tăng dài hạn.
        - **Death Cross (Giao cắt tử thần):** Khi đường Vàng cắt xuống dưới đường Đỏ → Tín hiệu cảnh báo xu hướng Giảm dài hạn.
        - **Hỗ trợ/Kháng cự:** Các đường MA thường đóng vai trò là ngưỡng hỗ trợ động trong xu hướng tăng.
        """,
        "interp_corr": """
        - **Đa dạng hóa danh mục:** Mục tiêu là tìm các tài sản có tương quan thấp để giảm rủi ro tổng thể.
        - **Hệ số = 1:** Hai quỹ biến động y hệt nhau. Nắm giữ cả 2 không có tác dụng phân tán rủi ro.
        - **Hệ số < 0.5:** Hai quỹ ít liên quan. Khi quỹ này giảm, quỹ kia có thể không giảm hoặc giảm ít hơn, giúp tài khoản ổn định.
        """,
        "interp_struct": """
        - **Tracking Error (TE):** Rất quan trọng với ETF. TE càng thấp chứng tỏ quỹ mô phỏng càng sát chỉ số tham chiếu. TE cao bất thường là dấu hiệu quỹ quản trị kém hoặc chi phí ẩn cao.
        - **Thanh khoản:** Khối lượng giao dịch (Volume) cao và ổn định giúp nhà đầu tư dễ dàng mua/bán mà không bị trượt giá (Slippage).
        """,
        "interp_cycle": """
        - **Capture Ratio:** Đánh giá năng lực của quỹ trong 2 trạng thái thị trường.
        - **Bull Market (Cột Xanh):** Khi thị trường tăng, quỹ có tăng mạnh hơn không? (Cần > Benchmark).
        - **Bear Market (Cột Đỏ):** Khi thị trường sập, quỹ có giữ giá tốt hơn không? (Cần < Benchmark, tức là cột đỏ ngắn hơn).
        """,
        "interp_forecast": """
        - **Mô hình:** Sử dụng Monte Carlo Simulation (1000 kịch bản ngẫu nhiên dựa trên biến động quá khứ) và ETS (Dự báo chuỗi thời gian).
        - **Fan Chart:** Vùng màu hiển thị khoảng dao động giá có xác suất xảy ra cao nhất (Confidence Interval).
        - **Lưu ý:** Dự báo chỉ mang tính tham khảo dựa trên dữ liệu lịch sử. Thị trường luôn có những biến số vĩ mô bất ngờ (Black Swan) không thể dự báo bằng toán học.
        """,
        "prob_up": "Xác suất Tăng", "scenario": "Kịch bản", "worst": "Xấu nhất", "best": "Tốt nhất"
    },
    "EN": {
        "page_title": "Vietnam ETF Analytics Hub",
        "sidebar_settings": "Settings",
        "data_updated": "Data updated to",
        "manager": "Fund Manager",
        "select_ticker": "Select Ticker",
        "time_range": "Time Range",
        "update_btn": "Update Data",
        "loading": "Loading data...",
        "success_update": "Update complete! Press 'R' to reload.",
        "tab_perf": "Performance", "tab_risk": "Risk", "tab_rr": "Risk-Return",
        "tab_trend": "Trend", "tab_corr": "Correlation", "tab_struct": "Structure",
        "tab_cycle": "Cycles", "tab_forecast": "Forecast",
        "chart_cum_ret": "Cumulative Wealth Growth",
        "chart_dd": "Drawdown from Peak",
        "chart_rr": "Risk vs Return Positioning",
        "chart_trend": "Price Trend Analysis",
        "chart_corr": "Correlation Matrix",
        "chart_te": "Tracking Error",
        "chart_vol": "Liquidity (Volume)",
        "chart_bb": "Bull vs Bear Performance",
        "chart_forecast": "Trend Forecast (ETS)",
        "metric_ret": "Return", "metric_vol": "Volatility (Ann.)",
        "metric_sharpe": "Sharpe Ratio", "metric_alpha": "Alpha", "metric_beta": "Beta",
        "interp_title": "💡 Analytical Insight:",
        "interp_perf": """
        - **Meaning:** Shows the growth of a hypothetical 100 currency units investment. The top line represents the best performer.
        - **Comparison:** If a fund's line is below VNINDEX, it is underperforming the broader market.
        - **Compounding:** The steepness of the curve indicates the power of compounding. Steeper slopes mean stronger momentum.
        """,
        "interp_risk": """
        - **Drawdown:** The percentage drop from the nearest peak. It measures the maximum 'pain' an investor must endure.
        - **Loss Math:** A **-20%** loss requires a **+25%** gain to break even. A **-50%** loss requires a **+100%** gain.
        - **Evaluation:** Superior funds have shallower drawdowns compared to the market during crises.
        """,
        "interp_rr": """
        - **Sweet Spot:** Top-left corner (High Return - Low Risk). Funds here are considered 'efficient'.
        - **Sharpe Ratio:** Measures risk-adjusted return. >1 is Good, >2 is Excellent. It asks: "For every unit of risk, how much return do I get?".
        - **Alpha & Beta:** * **Alpha > 0:** The fund beats the market benchmark.
            * **Beta < 1:** Defensive (Less volatile than market). **Beta > 1:** Aggressive (More volatile).
        """,
        "interp_trend": """
        - **Golden Cross:** When MA50 (Yellow) crosses above MA200 (Red) → Confirmed long-term BULLISH signal.
        - **Death Cross:** When MA50 crosses below MA200 → Long-term BEARISH warning.
        - **Support/Resistance:** Moving Averages often act as dynamic support levels in an uptrend.
        """,
        "interp_corr": """
        - **Diversification:** The goal is to find assets with low correlation to reduce overall portfolio risk.
        - **Coeff = 1:** Identical movement. Holding both adds no diversification benefit.
        - **Coeff < 0.5:** Low correlation. When one asset falls, the other might hold steady, smoothing the equity curve.
        """,
        "interp_struct": """
        - **Tracking Error (TE):** Crucial for ETFs. Low TE indicates precise index replication. High TE suggests poor management or hidden costs.
        - **Liquidity:** High and consistent volume ensures you can enter/exit positions without significant slippage.
        """,
        "interp_cycle": """
        - **Capture Ratio:** Evaluates fund behavior in different market regimes.
        - **Bull Market (Green Bar):** Does the fund rise more than the market? (Upside Capture).
        - **Bear Market (Red Bar):** Does the fund fall less than the market? (Downside Protection).
        """,
        "interp_forecast": """
        - **Models:** Uses Monte Carlo (1000 scenarios based on historical volatility) and ETS (Time-series forecasting).
        - **Fan Chart:** The shaded area shows the most probable price range (Confidence Interval).
        - **Disclaimer:** Forecasts are probabilistic and based on history. Markets are subject to unpredictable macro events (Black Swans).
        """,
        "prob_up": "Prob. of Increase", "scenario": "Scenario", "worst": "Worst case", "best": "Best case"
    },
    "DE": {
        "page_title": "Vietnam ETF Analysezentrum",
        "sidebar_settings": "Einstellungen",
        "data_updated": "Daten aktualisiert bis",
        "manager": "Fondsmanager",
        "select_ticker": "Ticker auswählen",
        "time_range": "Zeitraum",
        "update_btn": "Daten aktualisieren",
        "loading": "Daten werden geladen...",
        "success_update": "Update fertig! Drücken Sie 'R' zum Neuladen.",
        "tab_perf": "Performance", "tab_risk": "Risiko", "tab_rr": "Risiko-Rendite",
        "tab_trend": "Trend", "tab_corr": "Korrelation", "tab_struct": "Struktur",
        "tab_cycle": "Zyklen", "tab_forecast": "Prognose",
        "chart_cum_ret": "Kumuliertes Vermögenswachstum",
        "chart_dd": "Wertverlust vom Höchststand (Drawdown)",
        "chart_rr": "Risiko-Rendite-Positionierung",
        "chart_trend": "Preistrend-Analyse",
        "chart_corr": "Korrelationsmatrix",
        "chart_te": "Tracking Error (Nachbildungsfehler)",
        "chart_vol": "Liquidität (Volumen)",
        "chart_bb": "Bull vs Bear Performance",
        "chart_forecast": "Trendprognose (ETS)",
        "metric_ret": "Rendite", "metric_vol": "Volatilität (p.a.)",
        "metric_sharpe": "Sharpe-Quotient", "metric_alpha": "Alpha", "metric_beta": "Beta",
        "interp_title": "💡 Erklärung:",
        "interp_perf": """
        - **Bedeutung:** Zeigt das Wachstum einer hypothetischen Investition von 100 Währungseinheiten. Die oberste Linie zeigt den besten Fonds.
        - **Vergleich:** Liegt die Linie unter dem VNINDEX, schneidet der Fonds schlechter ab als der Gesamtmarkt.
        - **Zinseszins:** Die Steilheit der Kurve zeigt die Kraft des Zinseszinses. Steilere Anstiege bedeuten stärkeres Momentum.
        """,
        "interp_risk": """
        - **Drawdown:** Der prozentuale Verlust vom letzten Höchststand. Er misst den "Schmerz", den ein Anleger ertragen muss.
        - **Verlust-Mathematik:** Ein Verlust von **-20%** erfordert einen Gewinn von **-25%** zum Ausgleich. **-50%** Verlust benötigt **+100%** Gewinn.
        - **Bewertung:** Gute Fonds haben in Krisenzeiten geringere Drawdowns als der Markt.
        """,
        "interp_rr": """
        - **Idealzone:** Oben links (Hohe Rendite - Geringes Risiko). Fonds in diesem Bereich gelten als effizient.
        - **Sharpe-Ratio:** Risikobereinigte Rendite. >1 ist gut, >2 ist exzellent. Frage: "Wie viel Rendite erhalte ich pro Risikoeinheit?".
        - **Alpha & Beta:** * **Alpha > 0:** Der Fonds schlägt die Benchmark durch Managementleistung.
            * **Beta < 1:** Defensiv (Weniger volatil als der Markt). **Beta > 1:** Offensiv (Volatiler).
        """,
        "interp_trend": """
        - **Golden Cross:** Wenn der MA50 (Gelb) den MA200 (Rot) nach oben kreuzt → Bestätigtes langfristiges Kaufsignal (Bullish).
        - **Death Cross:** Wenn der MA50 den MA200 nach unten kreuzt → Warnsignal für Abwärtstrend (Bearish).
        - **Support:** Gleitende Durchschnitte fungieren oft als dynamische Unterstützungslinien.
        """,
        "interp_corr": """
        - **Diversifikation:** Ziel ist es, Vermögenswerte mit geringer Korrelation zu finden, um das Gesamtrisiko zu senken.
        - **Koeff = 1:** Identische Bewegung. Der Besitz beider Fonds bietet keinen Diversifikationsvorteil.
        - **Koeff < 0.5:** Geringe Korrelation. Wenn ein Fonds fällt, bleibt der andere stabil, was die Portfoliokurve glättet.
        """,
        "interp_struct": """
        - **Tracking Error (TE):** Entscheidend für ETFs. Ein niedriger TE zeigt eine präzise Indexabbildung an. Hoher TE deutet auf schlechtes Management oder versteckte Kosten hin.
        - **Liquidität:** Hohes und konstantes Volumen sichert den Ein- und Ausstieg ohne große Preisschwankungen (Slippage).
        """,
        "interp_cycle": """
        - **Capture Ratio:** Bewertet das Verhalten des Fonds in verschiedenen Marktphasen.
        - **Bullenmarkt (Grün):** Steigt der Fonds stärker als der Markt? (Upside Capture).
        - **Bärenmarkt (Rot):** Fällt der Fonds weniger als der Markt? (Downside Protection).
        """,
        "interp_forecast": """
        - **Modelle:** Nutzt Monte-Carlo-Simulation (1000 Szenarien basierend auf historischer Volatilität) und ETS (Zeitreihenprognose).
        - **Fan-Chart:** Der farbige Bereich zeigt die Preisspanne mit der höchsten Wahrscheinlichkeit (Konfidenzintervall).
        - **Disclaimer:** Prognosen sind probabilistisch und basieren auf der Vergangenheit. Märkte unterliegen unvorhersehbaren Makroereignissen (Black Swans).
        """,
        "prob_up": "Aufstiegs-WSK", "scenario": "Szenario", "worst": "Worst Case", "best": "Best Case"
    }
}

# ==========================================
# 2. CONFIG & CSS
# ==========================================
st.set_page_config(layout="wide", page_title="Vietnam ETF Hub", page_icon="📈", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; color: #31333F; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #004D40 !important; font-weight: 700; }
    
    div[data-testid="stMetric"] {
        background-color: #FFFFFF; padding: 15px; border-radius: 8px;
        border: 1px solid #E0E0E0; border-left: 5px solid #004D40; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] label { font-size: 0.9rem; color: #616161 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #212121 !important; font-weight: 700; }
    
    /* WIDER & COMFORTABLE TABS */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 10px; 
        display: flex;
        flex-wrap: wrap; 
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF; 
        border-radius: 8px; 
        color: #424242; 
        border: 1px solid #E0E0E0; 
        font-weight: 600;
        padding: 12px 30px; /* Tăng khoảng cách đệm */
        flex-grow: 1; /* Tự động giãn đều */
        text-align: center;
        min-width: 120px;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #F5F5F5;
        border-color: #BDBDBD;
    }
    .stTabs [aria-selected="true"] {
        background-color: #004D40 !important; 
        color: #FFFFFF !important; 
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .interpret-box {
        background-color: #E8F5E9; border-left: 5px solid #4CAF50; padding: 15px;
        border-radius: 5px; margin-top: 10px; font-size: 0.95rem; color: #1B5E20;
    }
    .interpret-title { font-weight: bold; color: #2E7D32; display: block; margin-bottom: 5px;}
    .stButton button { background-color: #004D40; color: white; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- FLAG LANGUAGE SELECTOR ---
if 'language' not in st.session_state:
    st.session_state['language'] = 'VN'

with st.sidebar:
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🇻🇳"): st.session_state['language'] = 'VN'
    with col2:
        if st.button("🇺🇸"): st.session_state['language'] = 'EN'
    with col3:
        if st.button("🇩🇪"): st.session_state['language'] = 'DE'
    
    L_CODE = st.session_state['language']
    st.caption(f"Language: **{L_CODE}**")

def t(key):
    return LANG[L_CODE].get(key, key)

st.title(f"📈 {t('page_title')}")

# ==========================================
# 3. CORE LOGIC
# ==========================================
TRADING_DAYS = 252

def calculate_returns(df): return df.pct_change()
def calculate_cumulative_returns(df): return (1 + df.pct_change()).cumprod() - 1
def calculate_drawdown(df):
    roll_max = df.cummax()
    return (df - roll_max) / roll_max

def calculate_risk_metrics(daily_ret, risk_free_rate=0.0):
    if daily_ret.empty: return pd.Series()
    ann_ret = daily_ret.mean() * TRADING_DAYS
    ann_vol = daily_ret.std() * np.sqrt(TRADING_DAYS)
    neg_ret = daily_ret[daily_ret < 0]
    downside_dev = neg_ret.std() * np.sqrt(TRADING_DAYS)
    sharpe = (ann_ret - risk_free_rate) / ann_vol if ann_vol != 0 else 0
    sortino = (ann_ret - risk_free_rate) / downside_dev if downside_dev != 0 else 0
    cum_ret = (1 + daily_ret).cumprod()
    max_dd = ((cum_ret - cum_ret.cummax()) / cum_ret.cummax()).min()
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else 0
    return pd.Series({"Ann. Return": ann_ret, "Volatility": ann_vol, "Max Drawdown": max_dd, "Sharpe Ratio": sharpe, "Sortino Ratio": sortino, "Calmar Ratio": calmar})

def calculate_beta_alpha(asset_ret, bench_ret):
    asset_ret = asset_ret.rename("Asset")
    bench_ret = bench_ret.rename("Benchmark")
    df = pd.concat([asset_ret, bench_ret], axis=1).dropna()
    if df.empty: return 0, 0
    cov = np.cov(df["Asset"], df["Benchmark"])[0][1]
    var = np.var(df["Benchmark"])
    beta = cov / var if var != 0 else 0
    alpha = (df["Asset"].mean() - beta * df["Benchmark"].mean()) * TRADING_DAYS
    return beta, alpha

def calculate_tracking_error(asset_ret, bench_ret, window=63):
    diff = asset_ret - bench_ret
    return diff.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100

def calculate_bull_bear_stats(asset_ret, bench_ret):
    a_name, b_name = "Asset", "Bench"
    df = pd.concat([asset_ret.rename(a_name), bench_ret.rename(b_name)], axis=1).dropna()
    if df.empty: return 0, 0
    bull = df[df[b_name] > 0][a_name].mean() * 252
    bear = df[df[b_name] < 0][a_name].mean() * 252
    return (bull if not pd.isna(bull) else 0) * 100, (bear if not pd.isna(bear) else 0) * 100

def run_monte_carlo(price_series, days=30, simulations=1000):
    returns = price_series.pct_change().dropna()
    last_price = price_series.iloc[-1]
    mu = returns.mean()
    sigma = returns.std()
    daily_returns = np.random.normal(mu, sigma, (days, simulations))
    price_paths = np.zeros_like(daily_returns)
    price_paths[0] = last_price
    for t in range(1, days):
        price_paths[t] = price_paths[t-1] * (1 + daily_returns[t])
    final_prices = price_paths[-1]
    prob_up = np.mean(final_prices > last_price) * 100
    expected_price = np.median(final_prices)
    worst_case = np.percentile(final_prices, 5)
    best_case = np.percentile(final_prices, 95)
    return price_paths, prob_up, expected_price, worst_case, best_case

# Mock ETS
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    def run_ets_forecast(price_series, days=30):
        ts = price_series.asfreq('B').fillna(method='ffill')
        try:
            model = ExponentialSmoothing(ts, trend='add', damped_trend=True, seasonal=None).fit()
            return model.forecast(days)
        except: return ExponentialSmoothing(ts).fit().forecast(days)
except ImportError:
    def run_ets_forecast(price_series, days=30): return pd.Series([price_series.iloc[-1]]*days)

# ==========================================
# 4. LOAD DATA
# ==========================================
@st.cache_data
def load_all_data():
    try:
        df_p = pd.read_csv('funds_data.csv', parse_dates=['Date'], index_col='Date')
        df_v = pd.read_csv('funds_volume.csv', parse_dates=['Date'], index_col='Date')
        df_meta = pd.read_csv('funds_profile.csv', index_col='Ticker')
        return df_p, df_v, df_meta
    except FileNotFoundError: return None, None, None

df, df_vol, df_profile = load_all_data()

if df is None:
    st.warning(t("loading"))
    st.stop()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header(f"⚙️ {t('sidebar_settings')}")
    
    # Update Button
    if st.button(t("update_btn")):
        with st.spinner(t("loading")):
            try:
                result = subprocess.run([sys.executable, "update_data.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success(t("success_update"))
                    st.cache_data.clear()
                else: st.error(f"Error: {result.stderr}")
            except Exception as e: st.error(f"Error: {e}")
    
    last_update = df.index.max().strftime('%d/%m/%Y')
    st.info(f"📅 {t('data_updated')}: **{last_update}**")
    
    all_issuers = df_profile['Issuer'].dropna().unique().tolist()
    sel_issuers = st.multiselect(f"{t('manager')}:", all_issuers, default=all_issuers[:3])
    
    filtered_profile = df_profile[df_profile['Issuer'].isin(sel_issuers)]
    avail_funds = filtered_profile.index.tolist()
    display_list = [c for c in df.columns if c in (['VNINDEX', 'VN30'] + avail_funds)]
    
    default_f = [f for f in ['VNINDEX', 'E1VFVN30', 'FUEVFVND'] if f in display_list]
    if not default_f and display_list: default_f = [display_list[0]]
    
    sel_funds = st.multiselect(f"{t('select_ticker')}:", display_list, default=default_f)
    if not sel_funds: st.stop()

    t_range = st.select_slider(f"{t('time_range')}:", options=["3M", "6M", "YTD", "1Y", "3Y", "5Y", "Max"], value="1Y")
    end_d = df.index.max()
    start_d = {
        "3M": end_d - timedelta(days=90), "6M": end_d - timedelta(days=180),
        "1Y": end_d - timedelta(days=365), "3Y": end_d - timedelta(days=365*3),
        "5Y": end_d - timedelta(days=365*5), "YTD": datetime(end_d.year, 1, 1),
        "Max": df.index.min()
    }[t_range]
    
    st.markdown("---")
    st.caption("© 2026 | Developed by Minh Phu Dinh")

df_view = df.loc[start_d:end_d, sel_funds]
daily_ret = calculate_returns(df_view)
bench_ticker = 'VNINDEX' if 'VNINDEX' in df.columns else sel_funds[0]
bench_ret = calculate_returns(df.loc[start_d:end_d, bench_ticker])

# ==========================================
# 5. DASHBOARD TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    t("tab_perf"), t("tab_risk"), t("tab_rr"), 
    t("tab_trend"), t("tab_corr"), t("tab_struct"), t("tab_cycle"), t("tab_forecast")
])

def chart_layout(fig, title="", x_title="", y_title=""):
    fig.update_layout(
        template="plotly_white", 
        title=dict(text=title, font=dict(color="#004D40", size=18)),
        xaxis=dict(title=x_title, showgrid=True, gridcolor='#F0F2F6'),
        yaxis=dict(title=y_title, showgrid=True, gridcolor='#F0F2F6'),
        legend=dict(orientation="h", y=1.1), hovermode="x unified", margin=dict(t=50, b=40)
    )
    return fig

def interpret(text):
    st.markdown(f"""<div class="interpret-box"><span class="interpret-title">{t('interp_title')}</span> {text}</div>""", unsafe_allow_html=True)

# --- TAB 1 ---
with tab1:
    st.markdown(f"### 🚀 {t('chart_cum_ret')}")
    cols = st.columns(len(sel_funds))
    norm_df = (df_view / df_view.iloc[0] - 1) * 100
    latest = norm_df.iloc[-1]
    for i, f in enumerate(sel_funds):
        cols[i].metric(label=f, value=f"{latest[f]:.2f}%")
    fig = chart_layout(px.line(norm_df, height=500), y_title=f"{t('metric_ret')} (%)")
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)
    interpret(t("interp_perf"))

# --- TAB 2 ---
with tab2:
    st.markdown(f"### 📉 {t('chart_dd')}")
    dd = calculate_drawdown(df_view) * 100
    fig = chart_layout(px.area(dd, height=450), y_title="Drawdown (%)")
    st.plotly_chart(fig, use_container_width=True)
    interpret(t("interp_risk"))

# --- TAB 3 ---
with tab3:
    st.markdown(f"### ⚖️ {t('chart_rr')}")
    r_data = []
    for f in sel_funds:
        m = calculate_risk_metrics(daily_ret[f])
        b, a = calculate_beta_alpha(daily_ret[f], bench_ret)
        if not m.empty: r_data.append({"Ticker": f, "Return": m["Ann. Return"]*100, "Vol": m["Volatility"]*100, "Sharpe": m["Sharpe Ratio"], "Beta": b, "Alpha": a*100})
    
    if r_data:
        df_r = pd.DataFrame(r_data).set_index("Ticker")
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = chart_layout(px.scatter(df_r, x="Vol", y="Return", color=df_r.index, size=[25]*len(df_r), text=df_r.index), title="Positioning", x_title=f"{t('metric_vol')} (%)", y_title=f"{t('metric_ret')} (%)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("##### 🏆 Ranking")
            # Removed styling to fix import error
            st.dataframe(df_r[["Sharpe", "Alpha", "Beta"]], use_container_width=True)
    interpret(t("interp_rr"))

# --- TAB 4 ---
with tab4:
    tf = st.selectbox(f"{t('select_ticker')}:", sel_funds, key="trend")
    td = df_view[[tf]].copy()
    td['MA50'], td['MA200'] = td[tf].rolling(50).mean(), td[tf].rolling(200).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=td.index, y=td[tf], name="Price", line=dict(color='#263238', width=1.5)))
    fig.add_trace(go.Scatter(x=td.index, y=td['MA50'], name="MA50", line=dict(color='#FBC02D')))
    fig.add_trace(go.Scatter(x=td.index, y=td['MA200'], name="MA200", line=dict(color='#D32F2F')))
    st.plotly_chart(chart_layout(fig, title=f"{t('chart_trend')}: {tf}"), use_container_width=True)
    interpret(t("interp_trend"))

# --- TAB 5 ---
with tab5:
    st.markdown(f"### 🔗 {t('chart_corr')}")
    st.plotly_chart(chart_layout(px.imshow(daily_ret.corr(), text_auto=".2f", color_continuous_scale='RdBu', zmin=-1, zmax=1)), use_container_width=True)
    interpret(t("interp_corr"))

# --- TAB 6 ---
with tab6:
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown(f"##### 🎯 {t('chart_te')}")
        te_df = pd.DataFrame({f: calculate_tracking_error(daily_ret[f], bench_ret) for f in sel_funds if f != bench_ticker})
        if not te_df.empty: st.plotly_chart(chart_layout(px.line(te_df), y_title="TE (%)"), use_container_width=True)
    with c_b:
        st.markdown(f"##### 💰 {t('chart_vol')}")
        if df_vol is not None:
            v_cols = [c for c in sel_funds if c in df_vol.columns]
            if v_cols:
                vf = st.selectbox(f"{t('select_ticker')}:", v_cols, key="v")
                st.plotly_chart(chart_layout(go.Figure(go.Bar(x=df_vol.index, y=df_vol.loc[start_d:end_d, vf], marker_color='#00897B')), title=f"Volume: {vf}"), use_container_width=True)
    interpret(t("interp_struct"))

# --- TAB 7 ---
with tab7:
    st.markdown(f"### 🔄 {t('chart_bb')}")
    bb_list = []
    for f in sel_funds:
        bu, be = calculate_bull_bear_stats(daily_ret[f], bench_ret)
        bb_list.append({"Asset": f, "Bull": bu, "Bear": be})
    bb = pd.DataFrame(bb_list).set_index("Asset")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=bb.index, y=bb['Bull'], name="Bull (Up)", marker_color='#4CAF50'))
    fig.add_trace(go.Bar(x=bb.index, y=bb['Bear'], name="Bear (Down)", marker_color='#EF5350'))
    st.plotly_chart(chart_layout(fig, title=f"vs {bench_ticker}"), use_container_width=True)
    interpret(t("interp_cycle"))

# --- TAB 8 ---
with tab8:
    st.markdown(f"### 🔮 {t('chart_forecast')}")
    f_fund = st.selectbox(f"{t('select_ticker')}:", sel_funds, key="forecast")
    train_data = df[f_fund].last('2Y')
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("#### ETS Forecast (30 Days/Tage/Ngày)")
        days = 30
        try:
            fc = run_ets_forecast(train_data, days)
            last_date = train_data.index[-1]
            dates = [last_date + timedelta(days=i) for i in range(1, days+1)]
            vol = train_data.pct_change().std() * np.sqrt(days)
            upper, lower = fc * (1 + vol), fc * (1 - vol)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=train_data.last('3M').index, y=train_data.last('3M'), name="History", line=dict(color='black')))
            fig.add_trace(go.Scatter(x=dates, y=fc, name="Forecast", line=dict(color='#00897B', dash='dash')))
            fig.add_trace(go.Scatter(x=dates+dates[::-1], y=pd.concat([upper, lower[::-1]]), fill='toself', fillcolor='rgba(0,137,123,0.2)', line=dict(color='rgba(0,0,0,0)'), name="Confidence"))
            st.plotly_chart(chart_layout(fig, title=f"Forecast: {f_fund}"), use_container_width=True)
        except Exception as e: st.error(f"Error: {e}")
        
    with c2:
        st.markdown("#### Monte Carlo Prob.")
        paths, prob, exp, worst, best = run_monte_carlo(train_data)
        st.metric(t("prob_up"), f"{prob:.1f}%", delta=f"{prob-50:.1f}%")
        st.write(f"**Median:** {exp:,.0f}")
        st.write(f"**{t('worst')} (5%):** :red[{worst:,.0f}]")
        st.write(f"**{t('best')} (5%):** :green[{best:,.0f}]")
        
        fig = go.Figure()
        for i in range(50): fig.add_trace(go.Scatter(y=paths[:, i], line=dict(color='gray', width=0.5), opacity=0.3, showlegend=False))
        fig.add_trace(go.Scatter(y=np.median(paths, axis=1), line=dict(color='red', width=2), name="Median"))
        fig.update_layout(template="plotly_white", height=200, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True)
    interpret(t("interp_forecast"))