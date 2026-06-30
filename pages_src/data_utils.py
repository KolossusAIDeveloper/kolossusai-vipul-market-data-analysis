import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Midcap 100": "^NSEMDCP100",
}

NSE_STOCKS = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "ITC": "ITC.NS",
    "Kotak Mahindra": "KOTAKBANK.NS",
    "L&T": "LT.NS",
    "Axis Bank": "AXISBANK.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Wipro": "WIPRO.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Titan Company": "TITAN.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "NTPC": "NTPC.NS",
}

@st.cache_data(ttl=60)
def get_quote(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        hist = t.history(period="2d", interval="1d")
        if hist.empty:
            return {}
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]
        price = float(last["Close"])
        prev_close = float(prev["Close"])
        change = price - prev_close
        change_pct = (change / prev_close) * 100
        return {
            "price": round(price, 2),
            "open": round(float(last["Open"]), 2),
            "high": round(float(last["High"]), 2),
            "low": round(float(last["Low"]), 2),
            "volume": int(last["Volume"]),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_ohlcv(ticker: str, interval: str = "1d", period: str = "6mo") -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None) if df.index.tzinfo else df.index
        df.columns = ["open", "high", "low", "close", "volume"]
        df = df.dropna()
        return df
    except Exception:
        return pd.DataFrame()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 20:
        return df
    c = df["close"].copy()
    # SMA
    df["sma20"] = c.rolling(20).mean()
    df["sma50"] = c.rolling(50).mean()
    # EMA
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    # Bollinger Bands
    df["bb_mid"] = c.rolling(20).mean()
    std = c.rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * std
    df["bb_lower"] = df["bb_mid"] - 2 * std
    # RSI
    delta = c.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    # MACD
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    # ATR
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    # VWAP (approximate daily)
    df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
    # Stochastic
    low14 = df["low"].rolling(14).min()
    high14 = df["high"].rolling(14).max()
    df["stoch_k"] = 100 * (df["close"] - low14) / (high14 - low14)
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    # Supertrend
    atr_mult = 3.0
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = hl2 + atr_mult * df["atr"]
    lower_band = hl2 - atr_mult * df["atr"]
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    for i in range(1, len(df)):
        if df["close"].iloc[i] > upper_band.iloc[i - 1]:
            direction.iloc[i] = 1
        elif df["close"].iloc[i] < lower_band.iloc[i - 1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i - 1]
        supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]
    df["supertrend"] = supertrend
    df["supertrend_dir"] = direction
    return df
