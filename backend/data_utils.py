import time
import functools
import pandas as pd
import numpy as np
import requests
import feedparser
import yfinance as yf
from datetime import datetime

# ── Symbol maps ─────────────────────────────────────────────────────────────
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

GLOBAL_INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "FTSE 100": "^FTSE",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "Crude Oil": "CL=F",
    "Gold": "GC=F",
    "USD/INR": "USDINR=X",
    "VIX": "^VIX",
}

# ── Simple TTL cache ─────────────────────────────────────────────────────────
_cache: dict = {}

def ttl_cache(seconds: int = 60):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            entry = _cache.get(key)
            if entry and now - entry["ts"] < seconds:
                return entry["val"]
            result = fn(*args, **kwargs)
            _cache[key] = {"val": result, "ts": now}
            return result
        return wrapper
    return decorator

# ── yfinance helpers ─────────────────────────────────────────────────────────
def _fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    # No shared session — per-ticker Ticker() objects avoid Yahoo CDN returning
    # cached data from a previous ticker across different requests.
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if not df.empty:
            return df
    except Exception:
        pass
    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=True,
                         progress=False)
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    return df


@ttl_cache(seconds=60)
def get_quote(ticker: str) -> dict:
    try:
        df = _fetch_history(ticker, period="5d", interval="1d")
        if df.empty:
            return {}
        df = _flatten_cols(df).dropna(subset=["close"])
        if df.empty:
            return {}
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
        price = float(last["close"])
        prev_close = float(prev["close"])
        change = price - prev_close
        return {
            "price": round(price, 2),
            "open": round(float(last.get("open", price)), 2),
            "high": round(float(last.get("high", price)), 2),
            "low": round(float(last.get("low", price)), 2),
            "volume": int(last.get("volume", 0)),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_pct": round((change / prev_close) * 100, 2),
        }
    except Exception:
        return {}


@ttl_cache(seconds=300)
def get_ohlcv(ticker: str, interval: str = "1d", period: str = "6mo") -> pd.DataFrame:
    try:
        df = _fetch_history(ticker, period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df = _flatten_cols(df)
        needed = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        if not needed:
            return pd.DataFrame()
        df = df[needed].copy()
        df.index = pd.to_datetime(df.index)
        if df.index.tzinfo is not None:
            df.index = df.index.tz_convert(None)
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                df[col] = np.nan
        return df.dropna(subset=["close"])
    except Exception:
        return pd.DataFrame()


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 20:
        return df
    c = df["close"].copy()
    df = df.copy()
    df["sma20"] = c.rolling(20).mean()
    df["sma50"] = c.rolling(50).mean()
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    df["bb_mid"] = c.rolling(20).mean()
    std = c.rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * std
    df["bb_lower"] = df["bb_mid"] - 2 * std
    delta = c.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    h, l, pc = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["vwap"] = (df["close"] * df["volume"]).cumsum() / df["volume"].cumsum()
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


# IST offset: UTC+5:30 = 19800 seconds
IST_OFFSET = 19800

def df_to_chart_data(df: pd.DataFrame, interval: str) -> dict:
    is_daily = interval in ("1d", "1wk")
    indicator_cols = [
        "sma20", "sma50", "ema20",
        "bb_upper", "bb_mid", "bb_lower",
        "vwap", "rsi", "macd", "macd_signal", "macd_hist",
        "supertrend", "supertrend_dir",
        "stoch_k", "stoch_d", "atr",
    ]

    candles, volume = [], []
    indicator_series: dict = {col: [] for col in indicator_cols if col in df.columns}

    for idx, row in df.iterrows():
        if is_daily:
            t = idx.strftime("%Y-%m-%d")
        else:
            t = int(idx.timestamp()) + IST_OFFSET

        candles.append({
            "time": t,
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
        })
        is_up = row["close"] >= row["open"]
        volume.append({"time": t, "value": int(row["volume"]),
                       "color": "#00ff88" if is_up else "#ff4444"})

        for col in indicator_series:
            val = row.get(col)
            if pd.notna(val):
                indicator_series[col].append({"time": t, "value": round(float(val), 4)})

    # Stats
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
    chg = float(last["close"]) - float(prev["close"])
    stats = {
        "last_close": round(float(last["close"]), 2),
        "period_high": round(float(df["high"].max()), 2),
        "period_low": round(float(df["low"].min()), 2),
        "change": round(chg, 2),
        "change_pct": round((chg / float(prev["close"])) * 100, 2),
        "avg_volume": round(float(df["volume"].mean()), 0),
        "rsi": round(float(last["rsi"]), 2) if "rsi" in df.columns and pd.notna(last.get("rsi")) else None,
        "atr": round(float(last["atr"]), 2) if "atr" in df.columns and pd.notna(last.get("atr")) else None,
    }

    return {"candles": candles, "volume": volume,
            "indicators": {k: v for k, v in indicator_series.items() if v},
            "stats": stats}


# ── News sentiment ────────────────────────────────────────────────────────────
POSITIVE_WORDS = {
    "rally", "surge", "gain", "rise", "high", "bull", "profit", "growth", "strong",
    "positive", "up", "outperform", "record", "boost", "recovery", "optimism",
    "upgrade", "buy", "accumulate", "upside", "breakout", "support",
}
NEGATIVE_WORDS = {
    "fall", "drop", "decline", "loss", "bear", "weak", "sell", "downgrade",
    "crash", "slump", "concern", "risk", "uncertainty", "outflow", "pressure",
    "volatility", "warning", "low", "cut", "negative", "pullback", "resistance",
}

RSS_FEEDS = {
    "Economic Times": "https://economictimes.indiatimes.com/markets/rss.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
}


def _score(text: str) -> float:
    words = text.lower().split()
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    return 0.0 if total == 0 else (pos - neg) / total


@ttl_cache(seconds=900)
def fetch_news() -> list:
    articles = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                published = entry.get("published", "")
                score = _score(title)
                articles.append({
                    "source": source,
                    "headline": title,
                    "published": published,
                    "score": round(score, 3),
                    "sentiment": "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral"),
                })
        except Exception:
            pass
    return sorted(articles, key=lambda x: abs(x["score"]), reverse=True)
