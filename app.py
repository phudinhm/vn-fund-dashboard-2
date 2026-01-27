import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import subprocess
import sys

# Thư viện dự báo
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from scipy.stats import norm
except ImportError:
    st.error("⚠️ Thiếu thư viện phân tích. Vui lòng thêm 'statsmodels' và 'scipy' vào requirements.txt")
    st.stop()

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN PROFESSIONAL
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Vietnam ETF Hub", 
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Custom CSS: Light Mode & Professional Style
st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; color: #31333F; }
    h1, h2, h3, h4 { font-family: 'Segoe UI', sans-serif; color: #004D40 !important; font-weight: 700; }
    
    /* Card Metric Style */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #004D40;
    }
    div[data-testid="stMetric"] label { font-size: 0.9rem; color: #616161 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #212121 !important; font-weight: 700; }
    
    /* Tabs Style */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFFFFF; border-radius: 6px; color: #424242; border: 1px solid #E0E0E0; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #004D40 !important; color: #FFFFFF !important; border: none;
    }
    
    /* Interpret Box */
    .interpret-box {
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        padding: 15px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 0.95rem;
    }
    .interpret-title { font-weight: bold; color: #2E7D32; display: flex; align-items: center; gap: 5px; }
    
    /* Button Update */
    .stButton button { background-color: #004D40; color: white; width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("📈 Vietnam ETF Analytics Hub")

# ==========================================
# 2. CHỨC NĂNG CẬP NHẬT DỮ LIỆU TỰ ĐỘNG
# ==========================================
with st.sidebar:
    st.markdown("### 🔄 Data Control")
    if st.button("Cập nhật Dữ liệu Mới nhất"):
        with st.spinner("Đang tải dữ liệu từ VNDIRECT & Yahoo..."):
            try:
                result = subprocess.run([sys.executable, "update_data.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("Đã cập nhật xong! Nhấn 'R' để tải lại.")
                    st.cache_data.clear()
                else: st.error(f"Lỗi: {result.stderr}")
            except Exception as e: st.error(f"Lỗi chạy script: {e}")
    st.markdown("---")

# ==========================================
# 3. MODULE TÍNH TOÁN (Core Logic)
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

# --- MODULE DỰ BÁO (FORECASTING) ---
def run_monte_carlo(price_series, days=30, simulations=1000):
    """Mô phỏng Monte Carlo để dự báo xác suất"""
    returns = price_series.pct_change().dropna()
    last_price = price_series.iloc[-1]
    
    # Tham số mô phỏng
    mu = returns.mean()
    sigma = returns.std()
    
    # Tạo ma trận ngẫu nhiên [days, simulations]
    daily_returns = np.random.normal(mu, sigma, (days, simulations))
    
    # Tính đường giá: Price_t = Price_{t-1} * (1 + r)
    price_paths = np.zeros_like(daily_returns)
    price_paths[0] = last_price
    
    for t in range(1, days):
        price_paths[t] = price_paths[t-1] * (1 + daily_returns[t])
        
    final_prices = price_paths[-1]
    
    # Thống kê xác suất
    prob_up = np.mean(final_prices > last_price) * 100
    expected_price = np.median(final_prices)
    worst_case = np.percentile(final_prices, 5) # VaR 95%
    best_case = np.percentile(final_prices, 95)
    
    return price_paths, prob_up, expected_price, worst_case, best_case

def run_ets_forecast(price_series, days=30):
    """Dự báo chuỗi thời gian bằng Exponential Smoothing (Holt-Winters)"""
    # Resample về Business Day hoặc Daily để tránh lỗi tần suất
    ts = price_series.asfreq('B').fillna(method='ffill')
    
    try:
        # Mô hình Trend + Damped (Trend giảm dần)
        model = ExponentialSmoothing(ts, trend='add', damped_trend=True, seasonal=None).fit()
        forecast = model.forecast(days)
        return forecast
    except:
        # Fallback: Simple Exponential Smoothing
        model = ExponentialSmoothing(ts).fit()
        forecast = model.forecast(days)
        return forecast

# ==========================================
# 4. LOAD DỮ LIỆU
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
    st.warning("⚠️ Chưa có dữ liệu. Hãy bấm nút cập nhật bên trái.")
    st.stop()

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("⚙️ Bộ Lọc Phân Tích")
    
    # Status
    last_update = df.index.max().strftime('%d/%m/%Y')
    st.info(f"📅 Data cập nhật đến: **{last_update}**")
    
    # Filters
    all_issuers = df_profile['Issuer'].dropna().unique().tolist()
    sel_issuers = st.multiselect("Nhà quản lý:", all_issuers, default=all_issuers[:3])
    
    filtered_profile = df_profile[df_profile['Issuer'].isin(sel_issuers)]
    avail_funds = filtered_profile.index.tolist()
    display_list = [c for c in df.columns if c in (['VNINDEX', 'VN30'] + avail_funds)]
    
    default_f = [f for f in ['VNINDEX', 'E1VFVN30', 'FUEVFVND'] if f in display_list]
    if not default_f and display_list: default_f = [display_list[0]]
    
    sel_funds = st.multiselect("Chọn Mã:", display_list, default=default_f)
    if not sel_funds: st.stop()

    # Time
    t_range = st.select_slider("Thời gian:", options=["3M", "6M", "YTD", "1Y", "3Y", "5Y", "Max"], value="1Y")
    end_d = df.index.max()
    start_d = {
        "3M": end_d - timedelta(days=90), "6M": end_d - timedelta(days=180),
        "1Y": end_d - timedelta(days=365), "3Y": end_d - timedelta(days=365*3),
        "5Y": end_d - timedelta(days=365*5), "YTD": datetime(end_d.year, 1, 1),
        "Max": df.index.min()
    }[t_range]
    
    st.markdown("---")
    st.caption("© 2026 | Developed by Minh Phu Dinh")

# Prepare Data
df_view = df.loc[start_d:end_d, sel_funds]
daily_ret = calculate_returns(df_view)
bench_ticker = 'VNINDEX' if 'VNINDEX' in df.columns else sel_funds[0]
bench_ret = calculate_returns(df.loc[start_d:end_d, bench_ticker])

# ==========================================
# 5. DASHBOARD TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📈 Hiệu Suất", "🛡️ Rủi Ro", "⚖️ Risk-Return", 
    "🌊 Xu Hướng", "🔗 Tương Quan", "📊 Cấu Trúc", "🔄 Chu Kỳ", "🔮 Dự Báo"
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

# Helper for Interpretation
def interpret(text):
    st.markdown(f"""<div class="interpret-box"><span class="interpret-title">💡 Giải thích (Interpretation):</span> {text}</div>""", unsafe_allow_html=True)

# --- TAB 1: HIỆU SUẤT ---
with tab1:
    st.markdown("### 🚀 Tăng trưởng tài sản")
    cols = st.columns(len(sel_funds))
    norm_df = (df_view / df_view.iloc[0] - 1) * 100
    latest = norm_df.iloc[-1]
    for i, f in enumerate(sel_funds):
        cols[i].metric(label=f, value=f"{latest[f]:.2f}%", delta=f"{latest[f]:.2f}%")
    
    fig = chart_layout(px.line(norm_df, height=500), y_title="Lợi nhuận (%)")
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)
    
    interpret("""
    * **Cumulative Return:** Nếu bạn đầu tư 100đ vào đầu kỳ, biểu đồ cho biết hiện tại bạn lãi/lỗ bao nhiêu %.
    * **So sánh:** Đường nào nằm cao nhất là quỹ hiệu quả nhất trong giai đoạn này.
    * **Quan sát:** Hãy chú ý những đoạn 'dốc xuống' xem quỹ nào giảm ít nhất.
    """)

# --- TAB 2: RỦI RO ---
with tab2:
    st.markdown("### 📉 Mức sụt giảm (Drawdown)")
    dd = calculate_drawdown(df_view) * 100
    fig = chart_layout(px.area(dd, height=450), y_title="Sụt giảm từ đỉnh (%)")
    st.plotly_chart(fig, use_container_width=True)
    
    interpret("""
    * **Max Drawdown:** Là % lỗ tối đa bạn phải chịu nếu lỡ 'đu đỉnh' và bán đúng đáy.
    * **Ý nghĩa:** Quỹ có Drawdown thấp (ví dụ -10%) an toàn hơn quỹ có Drawdown cao (ví dụ -30%).
    * **Mental Strength:** Hãy tự hỏi: 'Nếu tài khoản âm số % này, mình có ngủ ngon không?'.
    """)

# --- TAB 3: RISK-RETURN ---
with tab3:
    st.markdown("### ⚖️ Risk vs Return Matrix")
    r_data = []
    for f in sel_funds:
        m = calculate_risk_metrics(daily_ret[f])
        b, a = calculate_beta_alpha(daily_ret[f], bench_ret)
        if not m.empty: r_data.append({"Ticker": f, "Return": m["Ann. Return"]*100, "Vol": m["Volatility"]*100, "Sharpe": m["Sharpe Ratio"], "Beta": b, "Alpha": a*100})
    
    if r_data:
        df_r = pd.DataFrame(r_data).set_index("Ticker")
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = chart_layout(px.scatter(df_r, x="Vol", y="Return", color=df_r.index, size=[25]*len(df_r), text=df_r.index), title="Vị thế Quỹ", x_title="Rủi ro (Vol %)", y_title="Lợi nhuận (Năm %)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("##### 🏆 Ranking")
            st.dataframe(df_r[["Sharpe", "Alpha", "Beta"]].style.background_gradient(cmap="Greens"), use_container_width=True)
            
    interpret("""
    * **Góc phần tư tốt nhất:** Góc trên bên trái (Lợi nhuận cao - Rủi ro thấp).
    * **Sharpe Ratio:** > 1 là Tốt. Đo lường hiệu quả sinh lời trên mỗi đơn vị rủi ro.
    * **Alpha:** > 0 là Tốt. Cho biết quỹ chiến thắng thị trường bao nhiêu %.
    * **Beta:** < 1 là Phòng thủ (biến động ít hơn Index), > 1 là Tấn công (biến động mạnh hơn Index).
    """)

# --- TAB 4: XU HƯỚNG ---
with tab4:
    tf = st.selectbox("Chọn quỹ xem Trend:", sel_funds)
    td = df_view[[tf]].copy()
    td['MA50'], td['MA200'] = td[tf].rolling(50).mean(), td[tf].rolling(200).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=td.index, y=td[tf], name="Giá", line=dict(color='#263238', width=1.5)))
    fig.add_trace(go.Scatter(x=td.index, y=td['MA50'], name="MA50 (Trung hạn)", line=dict(color='#FBC02D')))
    fig.add_trace(go.Scatter(x=td.index, y=td['MA200'], name="MA200 (Dài hạn)", line=dict(color='#D32F2F')))
    st.plotly_chart(chart_layout(fig, title=f"Trend Analysis: {tf}"), use_container_width=True)
    
    interpret("""
    * **Golden Cross:** Khi đường Vàng (MA50) cắt lên đường Đỏ (MA200) → Tín hiệu Mua dài hạn.
    * **Death Cross:** Khi đường Vàng cắt xuống đường Đỏ → Tín hiệu Bán/Thận trọng.
    * **Giá trên MA:** Xu hướng tăng. **Giá dưới MA:** Xu hướng giảm.
    """)

# --- TAB 5: TƯƠNG QUAN ---
with tab5:
    st.markdown("### 🔗 Ma trận Tương quan")
    st.plotly_chart(chart_layout(px.imshow(daily_ret.corr(), text_auto=".2f", color_continuous_scale='RdBu', zmin=-1, zmax=1)), use_container_width=True)
    
    interpret("""
    * **Hệ số = 1:** Hai quỹ biến động y hệt nhau. Mua cả 2 không có tác dụng đa dạng hóa.
    * **Hệ số thấp (< 0.5):** Hai quỹ ít liên quan. Kết hợp chúng sẽ giúp giảm rủi ro danh mục.
    * **Lời khuyên:** Nên chọn các quỹ có màu xanh nhạt hoặc trắng để tối ưu danh mục.
    """)

# --- TAB 6: CẤU TRÚC ---
with tab6:
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown("##### 🎯 Tracking Error")
        te_df = pd.DataFrame({f: calculate_tracking_error(daily_ret[f], bench_ret) for f in sel_funds if f != bench_ticker})
        if not te_df.empty: st.plotly_chart(chart_layout(px.line(te_df), y_title="TE (%)"), use_container_width=True)
    with c_b:
        st.markdown("##### 💰 Thanh khoản")
        if df_vol is not None:
            v_cols = [c for c in sel_funds if c in df_vol.columns]
            if v_cols:
                vf = st.selectbox("Chọn mã:", v_cols, key="v")
                st.plotly_chart(chart_layout(go.Figure(go.Bar(x=df_vol.index, y=df_vol.loc[start_d:end_d, vf], marker_color='#00897B')), title=f"Volume: {vf}"), use_container_width=True)
    
    interpret("""
    * **Tracking Error (TE):** Càng thấp càng tốt. Nó cho thấy quỹ ETF bám sát chỉ số tham chiếu đến mức nào.
    * **Thanh khoản:** Cột volume càng cao và đều đặn càng tốt. Tránh các quỹ có volume lèo tèo vì rất khó bán khi cần tiền.
    """)

# --- TAB 7: CHU KỲ ---
with tab7:
    st.markdown("### 🔄 Bull vs Bear Performance")
    bb_list = []
    for f in sel_funds:
        bu, be = calculate_bull_bear_stats(daily_ret[f], bench_ret)
        bb_list.append({"Asset": f, "Bull": bu, "Bear": be})
    bb = pd.DataFrame(bb_list).set_index("Asset")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=bb.index, y=bb['Bull'], name="Khi TT Tăng", marker_color='#4CAF50'))
    fig.add_trace(go.Bar(x=bb.index, y=bb['Bear'], name="Khi TT Giảm", marker_color='#EF5350'))
    st.plotly_chart(chart_layout(fig, title=f"So với {bench_ticker}"), use_container_width=True)
    
    interpret("""
    * **Bull Beta (Cột Xanh):** Quỹ tăng bao nhiêu khi thị trường tăng? (Càng cao càng tốt).
    * **Bear Beta (Cột Đỏ):** Quỹ giảm bao nhiêu khi thị trường giảm? (Càng thấp/ngắn càng tốt).
    * **Quỹ tốt:** Là quỹ có cột xanh cao hơn Benchmark và cột đỏ ngắn hơn Benchmark.
    """)

# --- TAB 8: DỰ BÁO (NEW) ---
with tab8:
    st.markdown("### 🔮 Dự báo Xu hướng & Xác suất (Forecast)")
    
    f_fund = st.selectbox("Chọn quỹ để dự báo:", sel_funds)
    
    # Lấy dữ liệu 2 năm gần nhất để train model cho nhanh & nhạy
    train_data = df[f_fund].last('2Y')
    
    col_f1, col_f2 = st.columns([2, 1])
    
    with col_f1:
        st.markdown("#### 1. ETS Time-Series Forecast (30 Ngày)")
        # Chạy mô hình ETS
        forecast_days = 30
        forecast_values = run_ets_forecast(train_data, forecast_days)
        
        # Vẽ Fan Chart
        last_date = train_data.index[-1]
        future_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days+1)]
        
        # Tạo biên độ dao động (Confidence Interval giả định dựa trên volatility)
        vol_30d = train_data.pct_change().std() * np.sqrt(forecast_days)
        upper_band = forecast_values * (1 + vol_30d)
        lower_band = forecast_values * (1 - vol_30d)
        
        fig_f = go.Figure()
        # Lịch sử (3 tháng gần nhất)
        hist_view = train_data.last('3M')
        fig_f.add_trace(go.Scatter(x=hist_view.index, y=hist_view, name="Lịch sử", line=dict(color='black', width=2)))
        # Dự báo
        fig_f.add_trace(go.Scatter(x=future_dates, y=forecast_values, name="Dự báo (Mean)", line=dict(color='#00897B', dash='dash')))
        # Fan Chart
        fig_f.add_trace(go.Scatter(x=future_dates+future_dates[::-1], 
                                   y=pd.concat([upper_band, lower_band[::-1]]), 
                                   fill='toself', fillcolor='rgba(0,137,123,0.2)', 
                                   line=dict(color='rgba(255,255,255,0)'), name="Vùng dao động (68%)"))
        
        st.plotly_chart(chart_layout(fig_f, title=f"Dự phóng giá: {f_fund}"), use_container_width=True)
        
    with col_f2:
        st.markdown("#### 2. Monte Carlo Probability")
        # Chạy mô phỏng
        paths, prob_up, exp_price, worst, best = run_monte_carlo(train_data)
        
        st.metric("Xác suất Tăng giá (1 tháng tới)", f"{prob_up:.1f}%", delta=f"{prob_up-50:.1f}% vs Random",
                 help="Dựa trên 1000 lần giả lập biến động lịch sử.")
        
        st.markdown("---")
        st.write(f"**Kịch bản dự kiến (Median):** {exp_price:,.0f}")
        st.write(f"**Kịch bản xấu (Worst 5%):** :red[{worst:,.0f}]")
        st.write(f"**Kịch bản tốt (Best 5%):** :green[{best:,.0f}]")
        
        # Vẽ 50 đường mô phỏng ngẫu nhiên
        fig_mc = go.Figure()
        for i in range(50):
            fig_mc.add_trace(go.Scatter(y=paths[:, i], mode='lines', line=dict(color='gray', width=0.5), opacity=0.3, showlegend=False))
        fig_mc.add_trace(go.Scatter(y=np.median(paths, axis=1), mode='lines', line=dict(color='red', width=2), name="Trung bình"))
        fig_mc.update_layout(template="plotly_white", margin=dict(l=0,r=0,t=30,b=0), height=200, title="50 đường giả lập")
        st.plotly_chart(fig_mc, use_container_width=True)

    interpret("""
    * **ETS Forecast (Fan Chart):** Dự báo xu hướng dựa trên quán tính giá quá khứ. Vùng màu xanh nhạt là vùng giá có khả năng dao động cao nhất.
    * **Monte Carlo:** Máy tính chạy thử 1000 kịch bản tương lai dựa trên độ biến động quá khứ.
    * **Xác suất Tăng:** Nếu > 50% nghĩa là xu hướng lịch sử đang ủng hộ đà tăng. Tuy nhiên, **Dự báo chỉ mang tính tham khảo**, thị trường luôn có biến số bất ngờ.
    """)