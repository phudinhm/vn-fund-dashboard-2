import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Vietnam ETF Tracker")
st.title("📈 Vietnam ETF Performance Dashboard")

# --- 1. CẤU HÌNH NHÓM QUỸ (Grouping) ---
FUND_GROUPS = {
    "Chỉ số thị trường": ["VNINDEX"],
    "Dragon Capital": ["E1VFVN30", "FUEVFVND"],
    "VinaCapital": ["FUEVN100"],
    "SSIAM": ["FUESSV30", "FUESSVFL", "FUESSV50"]
}

# --- 2. LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('funds_data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df
    except FileNotFoundError:
        return None

df = load_data()

if df is None:
    st.error("⚠️ Chưa có dữ liệu. Hãy chạy 'python update_data.py' trước.")
    st.stop()

# --- 3. SIDEBAR THÔNG MINH ---
st.sidebar.header("🔍 Bộ lọc")

# Bước 1: Chọn Công ty quản lý (Providers)
all_providers = list(FUND_GROUPS.keys())
selected_providers = st.sidebar.multiselect(
    "1. Chọn Công ty Quản lý:",
    all_providers,
    default=["Chỉ số thị trường", "Dragon Capital"] # Mặc định chọn 2 nhóm này
)

# Bước 2: Tổng hợp các quỹ thuộc nhóm đã chọn
available_funds = []
for provider in selected_providers:
    available_funds.extend(FUND_GROUPS[provider])

# Lọc lại những quỹ thực sự có trong file CSV (phòng trường hợp file CSV thiếu)
available_funds = [f for f in available_funds if f in df.columns]

# Bước 3: Chọn chi tiết từng quỹ
selected_funds = st.sidebar.multiselect(
    "2. Chọn Quỹ cụ thể:",
    options=df.columns.tolist(), # Cho phép chọn tất cả nếu muốn
    default=available_funds      # Mặc định tick theo nhóm đã chọn ở trên
)

if not selected_funds:
    st.warning("👈 Vui lòng chọn ít nhất một quỹ từ cột bên trái.")
    st.stop()

# Bước 4: Time Horizon (Có 5Y)
time_options = ["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "All"]
selected_time = st.sidebar.select_slider("3. Khung thời gian:", options=time_options, value="1Y")

# --- 4. XỬ LÝ DỮ LIỆU ---
end_date = df.index.max()
start_date = df.index.min()

if selected_time == "1M": start_date = end_date - timedelta(days=30)
elif selected_time == "3M": start_date = end_date - timedelta(days=90)
elif selected_time == "6M": start_date = end_date - timedelta(days=180)
elif selected_time == "YTD": start_date = datetime(end_date.year, 1, 1)
elif selected_time == "1Y": start_date = end_date - timedelta(days=365)
elif selected_time == "3Y": start_date = end_date - timedelta(days=365*3)
elif selected_time == "5Y": start_date = end_date - timedelta(days=365*5)

# Đảm bảo start_date hợp lệ
if start_date < df.index.min(): start_date = df.index.min()

df_filtered = df.loc[start_date:end_date, selected_funds]

# Tính Performance (%)
if not df_filtered.empty:
    normalized_df = (df_filtered / df_filtered.iloc[0] - 1) * 100
    
    # --- 5. VẼ BIỂU ĐỒ ---
    st.markdown(f"### 🔥 Hiệu suất từ {start_date.strftime('%d/%m/%Y')}")
    
    fig = px.line(
        normalized_df, 
        x=normalized_df.index, 
        y=normalized_df.columns,
        height=550,
        labels={"value": "Tăng trưởng (%)", "variable": "Quỹ"}
    )
    
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
        yaxis_title="Lợi nhuận (%)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. BẢNG THỐNG KÊ ---
    st.markdown("### 📊 Chi tiết Tăng trưởng")
    
    # Tính toán các chỉ số
    latest_ret = normalized_df.iloc[-1]
    latest_price = df_filtered.iloc[-1]
    
    stats_df = pd.DataFrame({
        "Giá hiện tại": latest_price,
        "Tăng trưởng trong kỳ (%)": latest_ret
    }).sort_values("Tăng trưởng trong kỳ (%)", ascending=False)
    
    st.dataframe(
        stats_df.style.format({"Giá hiện tại": "{:,.0f}", "Tăng trưởng trong kỳ (%)": "{:,.2f}%"}),
        use_container_width=True
    )
else:
    st.error("Không có dữ liệu trong khoảng thời gian này.")
    