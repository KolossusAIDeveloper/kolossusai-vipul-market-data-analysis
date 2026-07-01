import pandas as pd
import numpy as np

from pages_src.data_utils import (
    INDICES, NSE_STOCKS, get_quote, get_ohlcv, compute_indicators,
    _yahoo_v8_quote, _yfinance_quote, _yahoo_v8_ohlcv,
)


def test_indices_include_nifty_50():
    assert INDICES["Nifty 50"] == "^NSEI"


def test_nse_stocks_includes_reliance():
    assert "Reliance" in NSE_STOCKS
    assert NSE_STOCKS["Reliance"] == "RELIANCE.NS"


def test_compute_indicators_adds_expected_columns():
    df = pd.DataFrame(
        {
            "open": list(range(100, 120)),
            "high": list(range(101, 121)),
            "low": list(range(99, 119)),
            "close": list(range(100, 120)),
            "volume": [1000] * 20,
        }
    )
    out = compute_indicators(df)
    for col in ["rsi", "macd", "atr", "sma20", "bb_upper", "bb_lower", "vwap", "stoch_k"]:
        assert col in out.columns, f"Missing column: {col}"


def test_compute_indicators_empty_returns_empty():
    out = compute_indicators(pd.DataFrame())
    assert out.empty


def test_get_quote_returns_dict():
    result = get_quote("RELIANCE.NS")
    assert isinstance(result, dict)


def test_get_quote_complete_keys_when_non_empty():
    result = get_quote("RELIANCE.NS")
    if result:
        for key in ["price", "change", "change_pct"]:
            assert key in result, f"Missing key: {key}"


def test_get_ohlcv_returns_dataframe():
    df = get_ohlcv("RELIANCE.NS", interval="1d", period="1mo")
    assert isinstance(df, pd.DataFrame)


def test_get_ohlcv_has_ohlcv_columns():
    df = get_ohlcv("RELIANCE.NS", interval="1d", period="1mo")
    if not df.empty:
        for col in ["open", "high", "low", "close", "volume"]:
            assert col in df.columns
