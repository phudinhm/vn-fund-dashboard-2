import pandas as pd
import requests
import time
from datetime import datetime

# --- 1. MASTER DATA CHUẨN HÓA (ETFs & Indices) ---
# Đã cập nhật theo danh sách bạn cung cấp
MASTER_DATA = [
    # --- INDICES (Chỉ số thị trường) ---
    {'Ticker': 'VNINDEX',  'Name': 'Vietnam Index',       'Issuer': 'HOSE',           'Type': 'Market Index', 'Benchmark': None,       'Launch': '2000-07-28', 'Fee': 0.00},
    {'Ticker': 'VN30',     'Name': 'VN30 Index',          'Issuer': 'HOSE',           'Type': 'Market Index', 'Benchmark': None,       'Launch': '2012-02-06', 'Fee': 0.00},
    {'Ticker': 'VN100',    'Name': 'VN100 Index',         'Issuer': 'HOSE',           'Type': 'Market Index', 'Benchmark': None,       'Launch': '2014-01-24', 'Fee': 0.00},
    {'Ticker': 'VNFINLEAD','Name': 'Vietnam FinLead',     'Issuer': 'HOSE',           'Type': 'Sector Index', 'Benchmark': None,       'Launch': '2019-11-18', 'Fee': 0.00},
    {'Ticker': 'VNX50',    'Name': 'VNX50 Index',         'Issuer': 'HOSE',           'Type': 'Market Index', 'Benchmark': None,       'Launch': '2017-10-23', 'Fee': 0.00},
    {'Ticker': 'VNDIAMOND','Name': 'Vietnam Diamond',     'Issuer': 'HOSE',           'Type': 'Thematic',     'Benchmark': None,       'Launch': '2019-11-18', 'Fee': 0.00},

    # --- DRAGON CAPITAL (DCVFM) ---
    {'Ticker': 'E1VFVN30', 'Name': 'VFM VN30 ETF',        'Issuer': 'Dragon Capital', 'Type': 'Equity ETF',   'Benchmark': 'VN30',     'Launch': '2014-10-06', 'Fee': 0.65},
    {'Ticker': 'FUEVFVND', 'Name': 'VFM VN Diamond ETF',  'Issuer': 'Dragon Capital', 'Type': 'Thematic ETF', 'Benchmark': 'VNDIAMOND','Launch': '2020-05-12', 'Fee': 0.80},
    {'Ticker': 'FUEDCMID', 'Name': 'DCVFM Midcap ETF',    'Issuer': 'Dragon Capital', 'Type': 'Equity ETF',   'Benchmark': 'VN70',     'Launch': '2022-09-29', 'Fee': 0.80},
    {'Ticker': 'FUEIP100', 'Name': 'DCVFM VN100 ETF',     'Issuer': 'Dragon Capital', 'Type': 'Equity ETF',   'Benchmark': 'VN100',    'Launch': '2021-09-14', 'Fee': 0.70},

    # --- SSIAM ---
    {'Ticker': 'FUESSV30', 'Name': 'SSIAM VN30 ETF',      'Issuer': 'SSIAM',          'Type': 'Equity ETF',   'Benchmark': 'VN30',     'Launch': '2020-08-18', 'Fee': 0.55},
    {'Ticker': 'FUESSVFL', 'Name': 'SSIAM FinLead ETF',   'Issuer': 'SSIAM',          'Type': 'Sector ETF',   'Benchmark': 'VNFINLEAD','Launch': '2020-01-14', 'Fee': 0.65},
    {'Ticker': 'FUESSV50', 'Name': 'SSIAM VNX50 ETF',     'Issuer': 'SSIAM',          'Type': 'Equity ETF',   'Benchmark': 'VNX50',    'Launch': '2014-11-17', 'Fee': 0.50},

    # --- VINACAPITAL ---
    {'Ticker': 'FUEVN100', 'Name': 'VinaCapital VN100',   'Issuer': 'VinaCapital',    'Type': 'Equity ETF',   'Benchmark': 'VN100',    'Launch': '2020-06-16', 'Fee': 0.67},

    # --- MIRAE ASSET ---
    {'Ticker': 'FUEMAV30', 'Name': 'Mirae Asset VN30 ETF','Issuer': 'Mirae Asset',    'Type': 'Equity ETF',   'Benchmark': 'VN30',     'Launch': '2020-09-22', 'Fee': 0.60},
    {'Ticker': 'FUEMAVND', 'Name': 'MAFM Diamond ETF',    'Issuer': 'Mirae Asset',    'Type': 'Thematic ETF', 'Benchmark': 'VNDIAMOND','Launch': '2024-05-15', 'Fee': 0.70},

    # --- TECHCOM CAPITAL (Mới thêm) ---
    {'Ticker': 'FUETCV30', 'Name': 'TCInvest VN30 ETF',   'Issuer': 'Techcom Capital','Type': 'Equity ETF',   'Benchmark': 'VN30',     'Launch': '2021-06-15', 'Fee': 0.00},

    # --- KIM VIETNAM ---
    {'Ticker': 'FUEKIV30', 'Name': 'KIM Growth VN30 ETF', 'Issuer': 'KIM Vietnam',    'Type': 'Equity ETF',   'Benchmark': 'VN30',     'Launch': '2020-12-28', 'Fee': 0.55},
    {'Ticker': 'FUEKIVFS', 'Name': 'KIM FinSelect ETF',   'Issuer': 'KIM Vietnam',    'Type': 'Sector ETF',   'Benchmark': 'VNFINSELECT','Launch': '2021-11-12', 'Fee': 0.60},
]

# Thời điểm bắt đầu lấy dữ liệu (2014)
START_TIMESTAMP = 1388534400 

def create_dimension_table():
    """Tạo file funds_profile.csv chuẩn hóa"""
    df = pd.DataFrame(MASTER_DATA)
    # Sắp xếp cho đẹp
    df = df[['Ticker', 'Name', 'Issuer', 'Type', 'Benchmark', 'Launch', 'Fee']]
    df.to_csv('funds_profile.csv', index=False)
    print("✅ Đã chuẩn hóa Master Data: funds_profile.csv")
    return df

def get_vndirect_data(symbol):
    """Lấy dữ liệu Full History từ VNDIRECT"""
    print(f"   -> Đang tải {symbol}...")
    current_ts = int(time.time())
    
    # API của VNDIRECT
    url = f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={symbol}&from={START_TIMESTAMP}&to={current_ts}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://dchart.vndirect.com.vn/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if 't' in data and 'c' in data:
                df = pd.DataFrame({
                    'Date': pd.to_datetime(data['t'], unit='s'),
                    'Close': data['c'],
                    'Volume': data.get('v', 0)
                })
                df['Date'] = df['Date'].dt.normalize()
                # Loại bỏ các giá trị 0 hoặc NaN
                df = df[df['Close'] > 0]
                return df.set_index('Date')
    except Exception as e:
        print(f"❌ Lỗi tải {symbol}: {e}")
    
    return pd.DataFrame()

def update_csv():
    # 1. Tạo Dimension Table
    df_profile = create_dimension_table()
    tickers_to_fetch = df_profile['Ticker'].tolist()

    # 2. Tải dữ liệu Fact Tables
    print(f"⏳ Bắt đầu tải dữ liệu lịch sử cho {len(tickers_to_fetch)} mã...")
    
    close_list = []
    vol_list = []
    
    for ticker in tickers_to_fetch:
        df = get_vndirect_data(ticker)
        if not df.empty:
            close_list.append(df['Close'].rename(ticker))
            vol_list.append(df['Volume'].rename(ticker))
        time.sleep(1) # Delay nhẹ để tránh bị chặn

    if not close_list:
        print("❌ Không tải được dữ liệu nào!")
        return

    # 3. Gộp và Xử lý
    print("🔄 Đang xử lý và gộp dữ liệu...")
    
    # Gộp giá (Close Price)
    df_close = pd.concat(close_list, axis=1)
    df_close.sort_index(inplace=True)
    df_close.ffill(inplace=True) # Lấp đầy ngày nghỉ
    df_close.dropna(how='all', inplace=True)
    
    # Gộp khối lượng (Volume)
    df_vol = pd.concat(vol_list, axis=1)
    df_vol.sort_index(inplace=True)
    df_vol.fillna(0, inplace=True)

    # Lọc từ ngày bắt đầu
    start_date_str = datetime.fromtimestamp(START_TIMESTAMP).strftime('%Y-%m-%d')
    df_close = df_close[df_close.index >= start_date_str]
    df_vol = df_vol[df_vol.index >= start_date_str]

    # 4. Lưu file
    df_close.index.name = 'Date'
    df_vol.index.name = 'Date'
    
    df_close.reset_index().to_csv('funds_data.csv', index=False)
    df_vol.reset_index().to_csv('funds_volume.csv', index=False)
    
    print(f"✅ HOÀN TẤT! Dữ liệu từ {df_close.index.min().date()} đến {df_close.index.max().date()}")

if __name__ == "__main__":
    update_csv()