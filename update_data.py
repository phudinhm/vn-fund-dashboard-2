import pandas as pd
import yfinance as yf
from vnstock3 import Vnstock
from datetime import datetime

# 1. Danh sách ETF lấy từ Yahoo Finance (Hoạt động tốt)
YAHOO_ETFS = {
    'E1VFVN30': 'E1VFVN30.VN',   # Dragon Capital VN30
    'FUEVFVND': 'FUEVFVND.VN',   # Dragon Capital Diamond
    'FUEVN100': 'FUEVN100.VN',   # VinaCapital VN100
    'FUESSV30': 'FUESSV30.VN',   # SSIAM VN30
    'FUESSVFL': 'FUESSVFL.VN',   # SSIAM FinLead
    'FUESSV50': 'FUESSV50.VN',   # SSIAM VNX50
    'FUEDCMID': 'FUEDCMID.VN'    # Dragon Capital Midcap
}

def get_yahoo_data():
    print("1️⃣ Đang tải ETF từ Yahoo Finance...")
    tickers = list(YAHOO_ETFS.values())
    try:
        # Tải dữ liệu từ 2020
        data = yf.download(tickers, start="2020-01-01", group_by='ticker', progress=False)
        
        df_etf = pd.DataFrame()
        for display_name, yahoo_symbol in YAHOO_ETFS.items():
            try:
                # Lấy cột Close
                if yahoo_symbol in data.columns.levels[0]:
                    series = data[yahoo_symbol]['Close']
                else:
                    series = data['Close'][yahoo_symbol]
                df_etf[display_name] = series
            except KeyError:
                print(f"   ⚠️ Thiếu dữ liệu Yahoo: {display_name}")
        
        # Xử lý Index của Yahoo (Thường có múi giờ UTC) -> chuyển về naive
        df_etf.index = df_etf.index.tz_localize(None)
        return df_etf
    except Exception as e:
        print(f"❌ Lỗi Yahoo: {e}")
        return pd.DataFrame()

def get_vnindex_data():
    print("2️⃣ Đang tải VNINDEX từ TCBS (vnstock)...")
    try:
        # Sử dụng nguồn TCBS (ổn định, ít bị chặn hơn nguồn mặc định)
        stock = Vnstock().stock(symbol='VNINDEX', source='TCBS')
        df = stock.quote.history(start='2020-01-01', end=datetime.today().strftime('%Y-%m-%d'))
        
        # Chuẩn hóa tên cột
        if 'time' in df.columns:
            df['Date'] = pd.to_datetime(df['time'])
        elif 'tradingDate' in df.columns:
            df['Date'] = pd.to_datetime(df['tradingDate'])
            
        df = df.set_index('Date')
        df = df[['close']].rename(columns={'close': 'VNINDEX'})
        return df
    except Exception as e:
        print(f"❌ Lỗi tải VNINDEX: {e}")
        return pd.DataFrame()

def update_csv():
    # Bước 1: Lấy ETF từ Yahoo
    df_yahoo = get_yahoo_data()
    
    # Bước 2: Lấy VNINDEX từ Vnstock
    df_vnindex = get_vnindex_data()
    
    # Bước 3: Gộp 2 nguồn lại (Merge)
    print("3️⃣ Đang gộp dữ liệu...")
    if not df_yahoo.empty and not df_vnindex.empty:
        # Gộp theo Index (Date), dùng outer join để giữ đủ ngày
        final_df = df_vnindex.join(df_yahoo, how='outer')
        
        # Sắp xếp và làm sạch
        final_df.sort_index(inplace=True)
        final_df.index.name = 'Date'
        
        # Forward Fill (Lấp đầy ngày nghỉ bằng giá trước đó)
        final_df.ffill(inplace=True)
        final_df.dropna(how='all', inplace=True)
        
        # Lọc từ năm 2020 trở đi
        final_df = final_df[final_df.index >= '2020-01-01']

        # Lưu file
        final_df.reset_index().to_csv('funds_data.csv', index=False)
        print("✅ THÀNH CÔNG! Đã cập nhật đầy đủ VNINDEX và ETF.")
        print(final_df.tail(3))
    else:
        print("❌ Thất bại: Một trong hai nguồn dữ liệu bị lỗi hoàn toàn.")

if __name__ == "__main__":
    update_csv()