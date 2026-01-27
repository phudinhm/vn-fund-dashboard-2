import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📈 Vietnam Fund Tracker")

# Load data
try:
    df = pd.read_csv('funds_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
except:
    st.error("Chưa có file dữ liệu. Hãy chạy update_data.py trước.")
    st.stop()

# Chọn quỹ
selected = st.multiselect("Chọn quỹ:", df.columns, default=df.columns[0])
if selected:
    st.plotly_chart(px.line(df, y=selected), use_container_width=True)