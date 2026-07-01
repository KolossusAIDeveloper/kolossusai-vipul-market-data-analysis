import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import requests

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


def _make_session() -> requests.Session:
    """Create a requests session that mimics a real browser to bypass rate limits."""
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return sess


# Module-level session reused across all calls
_SESSION = _make_session()


def _fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Try Ticker.history first; fall back to yf.download on failure."""
    # Attempt 1: Ticker with session
    try:
        t = yf.Ticker(ticker, session=_SESSION)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if not df.empty:
            return df
    except Exception:
        pass

    # Attempt 2: yf.download (different code path inside yfinance)
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict:
    try:
        df = _fetch_history(ticker, period="5d", interval="1d")
        if df.empty:
            return {}

        # Flatten multi-level columns produced by yf.download
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]

        df = df.dropna(subset=["close"])
        if df.empty:
            return {}

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]

        price = float(last["close"])
        prev_close = float(prev["close"])
        change = price - prev_close
        change_pct = (change / prev_close) * 100

        return {
            "price": round(price, 2),
            "open": round(float(last.get("open", price)), 2),
            "high": round(float(last.get("high", price)), 2),
            "low": round(float(last.get("low", price)), 2),
            "volume": int(last.get("volume", 0)),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_ohlcv(ticker: str, interval: str = "1d", period: str = "6mo") -> pd.DataFrame:
    try:
        df = _fetch_history(ticker, period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()

        # Flatten multi-level columns produced by yf.download
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]

        needed = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        if not needed:
            return pd.DataFrame()

        df = df[needed].copy()
        df.index = pd.to_datetime(df.index)
        if df.index.tzinfo is not None:
            df.index = df.index.tz_localize(None)

        # Ensure all expected columns exist
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = np.nan

        df = df.dropna(subset=["close"])
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
    denom = (high14 - low14).replace(0, np.nan)
    df["stoch_k"] = 100 * (df["close"] - low14) / denom
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    # Supertrend
    atr_mult = 3.0
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = (hl2 + atr_mult * df["atr"]).values
    lower_band = (hl2 - atr_mult * df["atr"]).values
    close_vals = df["close"].values
    supertrend = np.full(len(df), np.nan)
    direction = np.zeros(len(df), dtype=int)
    for i in range(1, len(df)):
        if np.isnan(upper_band[i - 1]) or np.isnan(lower_band[i - 1]):
            direction[i] = 0
            supertrend[i] = np.nan
        elif close_vals[i] > upper_band[i - 1]:
            direction[i] = 1
        elif close_vals[i] < lower_band[i - 1]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
        if not np.isnan(upper_band[i]) and not np.isnan(lower_band[i]):
            supertrend[i] = lower_band[i] if direction[i] == 1 else upper_band[i]
    df["supertrend"] = supertrend
    df["supertrend_dir"] = direction
    return df
