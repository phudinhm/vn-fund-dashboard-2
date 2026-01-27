import numpy as np
import pandas as pd

TRADING_DAYS = 252

def calculate_returns(df):
    return df.pct_change()

def calculate_cumulative_returns(df):
    return (1 + df.pct_change()).cumprod() - 1

def calculate_drawdown(df):
    """Trả về Series Drawdown (%)"""
    roll_max = df.cummax()
    drawdown = (df - roll_max) / roll_max
    return drawdown

def calculate_max_drawdown(df):
    """Trả về giá trị Max Drawdown"""
    dd = calculate_drawdown(df)
    return dd.min()

def calculate_risk_metrics(daily_ret, risk_free_rate=0.0):
    """Tính toán nhóm chỉ số Rủi ro & Hiệu suất (Risk Dimensions)"""
    if daily_ret.empty: return pd.Series()
    
    # 1. Return
    ann_ret = daily_ret.mean() * TRADING_DAYS
    
    # 2. Volatility
    ann_vol = daily_ret.std() * np.sqrt(TRADING_DAYS)
    
    # 3. Downside Deviation (Rủi ro giảm giá)
    neg_ret = daily_ret[daily_ret < 0]
    downside_dev = neg_ret.std() * np.sqrt(TRADING_DAYS)
    
    # 4. Ratios
    sharpe = (ann_ret - risk_free_rate) / ann_vol if ann_vol != 0 else 0
    sortino = (ann_ret - risk_free_rate) / downside_dev if downside_dev != 0 else 0
    
    # 5. Max Drawdown (Tính xấp xỉ từ chuỗi return)
    cum_ret = (1 + daily_ret).cumprod()
    dd = calculate_max_drawdown(cum_ret)
    
    # 6. Calmar Ratio
    calmar = ann_ret / abs(dd) if dd != 0 else 0
    
    return pd.Series({
        "Ann. Return": ann_ret,
        "Volatility": ann_vol,
        "Max Drawdown": dd,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Calmar Ratio": calmar
    })

def calculate_rolling_beta(asset_ret, market_ret, window=63):
    """Tính Beta trượt (Rolling Beta)"""
    cov = asset_ret.rolling(window).cov(market_ret)
    var = market_ret.rolling(window).var()
    return cov / var

def calculate_monthly_heatmap(series):
    monthly_ret = series.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    return monthly_ret * 100