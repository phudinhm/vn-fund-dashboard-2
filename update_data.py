import pandas as pd
import requests
from vnstock3 import Vnstock
from datetime import datetime
import time

# 1. Cấu hình ID các quỹ trên Fmarket (Bạn có thể thêm quỹ khác nếu biết ID)
# Cách tìm ID: Vào Fmarket, bấm F12 -> Network -> tìm request "get-nav-history"
FUND_IDS = {
    'DCDS': 20,
    'DCIP': 21,
    'VESAF': 18,
    'VIBF': 24,
    'E1VFVN30': 11 # ETF cũng lấy được
}

def get_fund_data(fund_code, fund_id):
    """Hàm lấy dữ liệu NAV từ API Fmarket"""
    url = "https://api.fmarket.vn/res/product/get-nav-history"
    payload = {
        "isAllData": 1,
        "productId": fund_id
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']
            df = pd.DataFrame(data)
            # Fmarket trả về field: 'navDate' (YYYYMMDD) và 'nav'
            df['Date'] = pd.to_datetime(df['navDate'], format='%Y%m%d')
            df[fund_code] = df['nav']
            return df[['Date', fund_code]].set_index('Date')
    except Exception as e:
        print(f"Lỗi lấy dữ liệu {fund_code}: {e}")
        return pd.DataFrame()

def get_vnindex():
    """Hàm lấy dữ liệu VNINDEX từ vnstock"""
    try:
        # Lấy dữ liệu từ năm 2020 đến nay
        stock = Vnstock().stock(symbol='VNINDEX', source='VCI')
        df = stock.quote.history(start='2020-01-01', end=datetime.today().strftime('%Y-%m-%d'))
        
        # vnstock trả về cột 'time' và 'close'
        df['Date'] = pd.to_datetime(df['time'])
        df['VNINDEX'] = df['close']
        return df[['Date', 'VNINDEX']].set_index('Date')
    except Exception as e:
        print(f"Lỗi lấy VNINDEX: {e}")
        return pd.DataFrame()

def update_csv():
    print("⏳ Đang tải dữ liệu thực tế...")
    
    # 1. Lấy VNINDEX
    final_df = get_vnindex()
    
    # 2. Lấy dữ liệu từng quỹ và gộp vào (Merge)
    for fund_code, fund_id in FUND_IDS.items():
        print(f"   -> Đang lấy {fund_code}...")
        fund_df = get_fund_data(fund_code, fund_id)
        
        if not fund_df.empty:
            # Merge vào bảng chính theo ngày (Outer join để giữ đủ ngày)
            if final_df.empty:
                final_df = fund_df
            else:
                final_df = final_df.join(fund_df, how='outer')
        
        # Nghỉ 1 xíu để không bị chặn IP
        time.sleep(0.5)

    # 3. Xử lý dữ liệu
    final_df.sort_index(inplace=True)
    
    # Fill các ngày nghỉ lễ/cuối tuần bằng giá ngày trước đó (Forward Fill)
    # Vì quỹ không giao dịch cuối tuần, nhưng biểu đồ cần liền mạch
    final_df.ffill(inplace=True)
    
    # Chỉ lấy dữ liệu từ 2021 trở lại đây cho nhẹ
    final_df = final_df[final_df.index >= '2021-01-01']

    # 4. Lưu file
    final_df.reset_index().to_csv('funds_data.csv', index=False)
    print("✅ Cập nhật dữ liệu thành công!")
    print(final_df.tail(3))

if __name__ == "__main__":
    update_csv()
    