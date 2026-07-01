import pandas as pd
import numpy as np

from pages_src.data_utils import INDICES, NSE_STOCKS, compute_indicators


def test_indices_include_nifty_50():
    assert INDICES["Nifty 50"] == "^NSEI"


def test_indices_include_sensex():
    assert INDICES["Sensex"] == "^BSESN"


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


def test_compute_indicators_returns_dataframe():
    df = pd.DataFrame(
        {
            "open": list(range(100, 120)),
            "high": list(range(101, 121)),
            "low": list(range(99, 119)),
            "close": list(range(100, 120)),
            "volume": [1000] * 20,
        }
    )
    result = compute_indicators(df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 20
