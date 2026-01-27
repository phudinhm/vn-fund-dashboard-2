import pandas as pd
import numpy as np
from datetime import datetime

def update_csv():
    dates = pd.date_range(start="2023-01-01", end=datetime.today(), freq='D')
    df = pd.DataFrame(index=dates)
    
    # Giả lập dữ liệu
    np.random.seed(42)
    df['VNINDEX'] = 1000 + np.random.randn(len(dates)).cumsum()
    df['VESAF'] = 15000 + (np.random.randn(len(dates)) + 0.05).cumsum() * 20
    df['DCDS'] = 60000 + (np.random.randn(len(dates)) + 0.1).cumsum() * 50
    
    df.index.name = 'Date'
    df.reset_index().to_csv('funds_data.csv', index=False)
    print("Dữ liệu đã được tạo thành công: funds_data.csv")

if __name__ == "__main__":
    update_csv()
    