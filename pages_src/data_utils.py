import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import requests
import time

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

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_YF_HOSTS = ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]


def _fresh_session() -> requests.Session:
    """Create a new session per request — avoids Yahoo CDN returning cached wrong-ticker data."""
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": _UA,
        "Accept": "application/json,text/html,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return sess


# ---------------------------------------------------------------------------
# Primary quote source: yfinance fast_info (handles auth/crumbs internally)
# ---------------------------------------------------------------------------

def _yfinance_fast_quote(ticker: str) -> dict:
    """Use yfinance fast_info for reliable per-ticker real-time data."""
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        price = float(fi.last_price or 0)
        if price <= 0:
            return {}
        prev_close = float(fi.previous_close or price)
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        return {
            "price": round(price, 2),
            "open": round(float(fi.open or price), 2),
            "high": round(float(fi.day_high or price), 2),
            "low": round(float(fi.day_low or price), 2),
            "volume": int(fi.three_month_average_volume or 0),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Fallback quote: history-based calculation
# ---------------------------------------------------------------------------

def _yfinance_history_quote(ticker: str) -> dict:
    """Fetch quote from recent daily history as fallback."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="5d", interval="1d", auto_adjust=True)
        if df.empty:
            return {}
        df.columns = [c.lower() for c in df.columns]
        df = df.dropna(subset=["close"])
        if df.empty:
            return {}
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        price = float(last["close"])
        prev_close = float(prev["close"])
        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
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


# ---------------------------------------------------------------------------
# OHLCV: Yahoo v8 API with per-request session (no shared state)
# ---------------------------------------------------------------------------

def _yahoo_v8_ohlcv(ticker: str, interval: str, range_: str) -> pd.DataFrame:
    """Fetch OHLCV directly from Yahoo Finance chart v8 API using a fresh session."""
    iv = "60m" if interval == "1h" else interval
    sess = _fresh_session()
    for host in _YF_HOSTS:
        try:
            url = f"https://{host}/v8/finance/chart/{ticker}"
            resp = sess.get(url, params={"range": range_, "interval": iv}, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                continue
            timestamps = result[0].get("timestamp", [])
            quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
            if not timestamps:
                continue
            n = len(timestamps)
            df = pd.DataFrame(
                {
                    "open":   quotes.get("open",   [np.nan] * n),
                    "high":   quotes.get("high",   [np.nan] * n),
                    "low":    quotes.get("low",    [np.nan] * n),
                    "close":  quotes.get("close",  [np.nan] * n),
                    "volume": quotes.get("volume", [0] * n),
                },
                index=pd.to_datetime(timestamps, unit="s"),
            )
            df.index.name = "datetime"
            # Remove timezone if present
            if df.index.tzinfo is not None:
                df.index = df.index.tz_convert(None)
            # Drop rows where ANY of OHLC is NaN — ensures valid candles
            df = df.dropna(subset=["open", "high", "low", "close"])
            df["volume"] = df["volume"].fillna(0).astype(float)
            if not df.empty:
                return df
        except Exception:
            continue
    return pd.DataFrame()


def _yfinance_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV via yfinance as fallback."""
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        needed = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        if len(needed) < 4:
            return pd.DataFrame()
        df = df[needed].copy()
        df.index = pd.to_datetime(df.index)
        # Convert tz-aware to tz-naive
        if df.index.tzinfo is not None:
            df.index = df.index.tz_convert(None)
        # Drop rows where ANY of OHLC is NaN
        df = df.dropna(subset=["open", "high", "low", "close"])
        if "volume" not in df.columns:
            df["volume"] = 0
        df["volume"] = df["volume"].fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


# Map yfinance period strings to Yahoo v8 range strings
_PERIOD_TO_RANGE = {
    "1d":  "1d",
    "5d":  "5d",
    "10d": "1mo",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y":  "1y",
    "2y":  "2y",
    "5y":  "5y",
    "60d": "3mo",
}


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict:
    """Get real-time quote for a ticker. Uses fast_info first, falls back to history."""
    result = _yfinance_fast_quote(ticker)
    if result:
        return result
    return _yfinance_history_quote(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def get_ohlcv(ticker: str, interval: str = "1d", period: str = "6mo") -> pd.DataFrame:
    """Get OHLCV data. Yahoo v8 API first, yfinance fallback."""
    range_ = _PERIOD_TO_RANGE.get(period, period)
    df = _yahoo_v8_ohlcv(ticker, interval, range_)
    if not df.empty:
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = 0.0
        return df
    return _yfinance_ohlcv(ticker, period, interval)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 5:
        return df
    c = df["close"].copy()
    if len(df) >= 20:
        df["sma20"] = c.rolling(20).mean()
        df["bb_mid"] = c.rolling(20).mean()
        std = c.rolling(20).std()
        df["bb_upper"] = df["bb_mid"] + 2 * std
        df["bb_lower"] = df["bb_mid"] - 2 * std
    if len(df) >= 50:
        df["sma50"] = c.rolling(50).mean()
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    delta = c.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    vol = df["volume"].replace(0, np.nan)
    df["vwap"] = (df["close"] * vol).cumsum() / vol.cumsum()
    low14 = df["low"].rolling(14).min()
    high14 = df["high"].rolling(14).max()
    denom = (high14 - low14).replace(0, np.nan)
    df["stoch_k"] = 100 * (df["close"] - low14) / denom
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
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
