import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd
import numpy as np
from backend.data_utils import (
    INDICES, NSE_STOCKS, GLOBAL_INDICES,
    _score, compute_indicators, df_to_chart_data, ttl_cache,
)


def test_indices_not_empty():
    assert len(INDICES) > 0
    assert 'Nifty 50' in INDICES


def test_nse_stocks_not_empty():
    assert len(NSE_STOCKS) >= 10
    assert 'TCS' in NSE_STOCKS


def test_global_indices_not_empty():
    assert len(GLOBAL_INDICES) >= 5


def test_sentiment_score_positive():
    score = _score('markets rally to record highs on strong growth')
    assert score > 0


def test_sentiment_score_negative():
    score = _score('markets crash on heavy selling bear pressure')
    assert score < 0


def test_sentiment_score_neutral():
    score = _score('the market opened flat today')
    assert score == 0.0


def make_sample_df(n=60):
    dates = pd.date_range('2023-01-01', periods=n, freq='D')
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame({
        'open': close * (1 - rng.uniform(0, 0.01, n)),
        'high': close * (1 + rng.uniform(0, 0.01, n)),
        'low': close * (1 - rng.uniform(0, 0.01, n)),
        'close': close,
        'volume': rng.integers(100000, 1000000, n).astype(float),
    }, index=dates)
    return df


def test_compute_indicators_adds_columns():
    df = make_sample_df()
    result = compute_indicators(df)
    for col in ['sma20', 'ema20', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'vwap']:
        assert col in result.columns, f'{col} missing'


def test_compute_indicators_rsi_range():
    df = make_sample_df(100)
    result = compute_indicators(df)
    rsi = result['rsi'].dropna()
    assert rsi.between(0, 100).all()


def test_df_to_chart_data_structure():
    df = make_sample_df()
    df = compute_indicators(df)
    out = df_to_chart_data(df, '1d')
    assert 'candles' in out
    assert 'volume' in out
    assert 'indicators' in out
    assert 'stats' in out
    assert len(out['candles']) == len(df)


def test_df_to_chart_data_candle_format():
    df = make_sample_df()
    out = df_to_chart_data(df, '1d')
    for candle in out['candles'][:5]:
        assert 'time' in candle
        assert 'open' in candle
        assert 'high' in candle
        assert 'low' in candle
        assert 'close' in candle
        assert isinstance(candle['time'], str)  # daily = string date


def test_df_to_chart_data_intraday_time():
    df = make_sample_df()
    df.index = pd.date_range('2023-01-01 09:15', periods=len(df), freq='5min')
    out = df_to_chart_data(df, '5m')
    assert isinstance(out['candles'][0]['time'], int)


def test_ttl_cache():
    call_count = [0]

    @ttl_cache(seconds=60)
    def fn(x):
        call_count[0] += 1
        return x * 2

    assert fn(5) == 10
    assert fn(5) == 10
    assert call_count[0] == 1  # Only called once due to cache


def test_fastapi_app_imports():
    from backend.main import app
    assert app is not None


def test_fastapi_routes():
    from backend.main import app
    routes = [r.path for r in app.routes]
    assert '/api/config' in routes
    assert '/api/news' in routes
    assert '/api/quotes/batch' in routes
