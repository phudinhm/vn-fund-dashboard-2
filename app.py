import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Vietnam Fund Tracker")
st.title("📈 Dashboard Hiệu suất Quỹ & Thị trường")

# --- 1. LOAD DATA ---
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
    st.error("⚠️ Chưa có file dữ liệu. Vui lòng chạy file update_data.py trước!")
    st.stop()

# --- 2. SIDEBAR CONFIG ---
st.sidebar.header("🛠 Cấu hình")

# Chọn Quỹ/Chỉ số
all_funds = df.columns.tolist()
selected_funds = st.sidebar.multiselect(
    "Chọn Quỹ để so sánh:", 
    options=all_funds,
    default=['DCDS', 'VNINDEX'] if 'DCDS' in all_funds else all_funds[:2]
)

# Chọn Time Horizon (Đã thêm 3Y, 5Y)
time_options = ["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "All"]
selected_time = st.sidebar.select_slider("Khung thời gian:", options=time_options, value="1Y")

# --- 3. FILTER DATA ---
end_date = df.index.max()
start_date = df.index.min() # Mặc định là All

if selected_time == "1M":
    start_date = end_date - timedelta(days=30)
elif selected_time == "3M":
    start_date = end_date - timedelta(days=90)
elif selected_time == "6M":
    start_date = end_date - timedelta(days=180)
elif selected_time == "YTD":
    start_date = datetime(end_date.year, 1, 1)
elif selected_time == "1Y":
    start_date = end_date - timedelta(days=365)
elif selected_time == "3Y":
    start_date = end_date - timedelta(days=365*3)
elif selected_time == "5Y":
    start_date = end_date - timedelta(days=365*5)

# Đảm bảo start_date không nhỏ hơn dữ liệu có sẵn
if start_date < df.index.min():
    start_date = df.index.min()

# Cắt dữ liệu
df_filtered = df.loc[start_date:end_date, selected_funds]

if df_filtered.empty:
    st.warning("Không đủ dữ liệu cho khung thời gian này.")
    st.stop()

# --- 4. TÍNH PERFORMANCE (%) ---
# Quy đổi về % tăng trưởng so với ngày đầu tiên của giai đoạn
normalized_df = (df_filtered / df_filtered.iloc[0] - 1) * 100

# --- 5. HIỂN THỊ BIỂU ĐỒ ---
st.markdown(f"### 📊 Hiệu suất từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}")

# Vẽ Line Chart
fig = px.line(
    normalized_df, 
    x=normalized_df.index, 
    y=normalized_df.columns,
    labels={"value": "Tăng trưởng (%)", "variable": "Quỹ/Chỉ số"},
    height=500
)

fig.update_layout(
    template="plotly_dark",
    hovermode="x unified",
    legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
    yaxis_title="Lợi nhuận (%)"
)

st.plotly_chart(fig, use_container_width=True)

# --- 6. THỐNG KÊ CHI TIẾT ---
cols = st.columns(len(selected_funds))
latest_values = df_filtered.iloc[-1]
returns = normalized_df.iloc[-1]

for i, fund in enumerate(selected_funds):
    with cols[i]:
        st.metric(
            label=fund,
            value=f"{latest_values[fund]:,.0f}", # Hiển thị giá NAV thực tế
            delta=f"{returns[fund]:.2f}%"        # Hiển thị % tăng trưởng trong kỳ
        )