import pandas as pd

from pages_src.data_utils import INDICES, get_quote, compute_indicators


def test_indices_include_nifty_50():
    assert INDICES["Nifty 50"] == "^NSEI"


def test_compute_indicators_adds_expected_columns():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            "high": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120],
            "low": [99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118],
            "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            "volume": [1000] * 20,
        }
    )
    out = compute_indicators(df)
    assert "rsi" in out.columns
    assert "macd" in out.columns
    assert "atr" in out.columns


def test_get_quote_returns_dict_for_known_symbol():
    result = get_quote("^NSEI")
    assert isinstance(result, dict)
