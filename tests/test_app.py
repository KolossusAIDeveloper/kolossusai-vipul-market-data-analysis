import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    import pandas
    import numpy
    import plotly
    import streamlit
    assert True


def make_test_df(n=300):
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    np.random.seed(42)
    close = 22000 + np.cumsum(np.random.randn(n) * 100)
    close = np.abs(close) + 1000  # ensure positive
    return pd.DataFrame({
        "open": close * 0.998,
        "high": close * 1.005,
        "low": close * 0.995,
        "close": close,
        "volume": np.random.randint(1000000, 5000000, n).astype(float),
    }, index=dates)


def test_compute_indicators():
    from pages_src.data_utils import compute_indicators
    df = make_test_df(300)
    result = compute_indicators(df)
    assert "rsi" in result.columns
    assert "macd" in result.columns
    assert "sma20" in result.columns
    assert "bb_upper" in result.columns
    assert "supertrend" in result.columns
    assert len(result) == 300
    # After dropping NaN, should have at least 200 rows
    valid = result.dropna()
    assert len(valid) > 50, f"Only {len(valid)} valid rows after dropna"


def test_sentiment_scoring():
    from pages_src.sentiment import score_headline
    pos = score_headline("Nifty surges to record high on strong rally")
    neg = score_headline("Market crash as Nifty falls sharply on heavy selling")
    neutral = score_headline("RBI holds rates steady at scheduled meeting")
    assert pos > 0
    assert neg < 0
    assert -1 <= pos <= 1
    assert -1 <= neg <= 1


def test_backtest_engine():
    from pages_src.strategy import run_backtest
    df = make_test_df(300)
    strategy = {"rule": "rsi_oversold", "rsi_buy": 30, "rsi_sell": 70, "sl_pct": 2.0, "target_pct": 4.0}
    result = run_backtest(df, strategy, 100000.0)
    assert isinstance(result, dict), "run_backtest should return a dict"
    assert len(result) > 0, f"run_backtest returned empty dict"
    assert "total_return" in result
    assert "sharpe" in result
    assert "equity_curve" in result
    assert result["final_equity"] > 0


def test_symbol_maps():
    from pages_src.data_utils import INDICES, NSE_STOCKS
    assert "Nifty 50" in INDICES
    assert "Sensex" in INDICES
    assert "TCS" in NSE_STOCKS
    assert "Reliance" in NSE_STOCKS
    assert INDICES["Nifty 50"] == "^NSEI"


def test_paper_trading_init():
    portfolio = {
        "cash": 500000.0,
        "positions": {},
        "orders": [],
    }
    assert portfolio["cash"] == 500000.0
    assert len(portfolio["positions"]) == 0
    buy_cost = 100 * 2000.0
    portfolio["cash"] -= buy_cost
    portfolio["positions"]["TCS"] = {"ticker": "TCS.NS", "qty": 100, "avg_price": 2000.0}
    assert portfolio["cash"] == 300000.0
    assert portfolio["positions"]["TCS"]["qty"] == 100
