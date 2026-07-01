import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pages_src.data_utils import INDICES, NSE_STOCKS, get_ohlcv, compute_indicators

ALL_SYMBOLS = {**INDICES, **NSE_STOCKS}

INTERVAL_MAP = {
    "5 min": ("5m", "5d"),
    "15 min": ("15m", "10d"),
    "1 min": ("1m", "5d"),
    "1 hour": ("1h", "60d"),
    "1 day": ("1d", "1y"),
    "1 week": ("1wk", "5y"),
}


def show():
    st.markdown('<div class="module-header"><h2 style="margin:0">📈 Live Charts & Technical Indicators</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
    ⚠️ Technical indicators are computational tools for analysis only. They do not predict future prices. Always conduct your own due diligence before trading.
    </div>
    """, unsafe_allow_html=True)

    col_sym, col_tf, col_btn = st.columns([2, 2, 1])
    with col_sym:
        symbol_name = st.selectbox("Symbol", list(ALL_SYMBOLS.keys()), index=0)
    with col_tf:
        timeframe = st.selectbox("Timeframe", list(INTERVAL_MAP.keys()), index=0)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reload", use_container_width=True):
            st.cache_data.clear()

    ticker = ALL_SYMBOLS[symbol_name]
    interval, period = INTERVAL_MAP[timeframe]

    with st.spinner(f"Loading {symbol_name} ({timeframe})..."):
        df = get_ohlcv(ticker, interval=interval, period=period)

    if df.empty:
        st.warning(f"No data returned for {symbol_name} at {timeframe}. Markets may be closed or this timeframe is unavailable. Try '1 day' or '5 min'.")
        return

    # Ensure all OHLC columns exist and have no NaN
    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            st.warning(f"Incomplete data for {symbol_name}.")
            return
    df = df.dropna(subset=["open", "high", "low", "close"])
    if df.empty:
        st.warning(f"No complete OHLC bars available for {symbol_name} at {timeframe}.")
        return

    df = compute_indicators(df)

    # Indicator toggles
    st.markdown("**Overlay Indicators**")
    st.caption("Clean Zerodha-style layout: minimal clutter, right-side price scale, and focus on candlesticks + volume.")
    ind_cols = st.columns(8)
    show_sma20 = ind_cols[0].checkbox("SMA 20", value=True)
    show_sma50 = ind_cols[1].checkbox("SMA 50", value=False)
    show_ema20 = ind_cols[2].checkbox("EMA 20", value=False)
    show_bb = ind_cols[3].checkbox("Bollinger Bands", value=False)
    show_vwap = ind_cols[4].checkbox("VWAP", value=False)
    show_supertrend = ind_cols[5].checkbox("Supertrend", value=False)
    show_rsi = ind_cols[6].checkbox("RSI", value=True)
    show_macd = ind_cols[7].checkbox("MACD", value=False)

    # Determine subplot count
    sub_count = 2  # price + volume always
    if show_rsi:
        sub_count += 1
    if show_macd:
        sub_count += 1

    row_heights = [0.55, 0.15]
    if show_rsi:
        row_heights.append(0.15)
    if show_macd:
        row_heights.append(0.15)
    total = sum(row_heights)
    row_heights = [r / total for r in row_heights]

    subplot_titles = [symbol_name, "Volume"]
    if show_rsi:
        subplot_titles.append("RSI (14)")
    if show_macd:
        subplot_titles.append("MACD")

    fig = make_subplots(
        rows=sub_count, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        subplot_titles=subplot_titles,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="OHLC",
        increasing_line_color="#22c55e", increasing_fillcolor="#22c55e",
        decreasing_line_color="#ef4444", decreasing_fillcolor="#ef4444",
        increasing_width=1,
        decreasing_width=1,
    ), row=1, col=1)

    if show_sma20 and "sma20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma20"], name="SMA 20",
                                  line=dict(color="#ffa500", width=1.5)), row=1, col=1)
    if show_sma50 and "sma50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma50"], name="SMA 50",
                                  line=dict(color="#a78bfa", width=1.5)), row=1, col=1)
    if show_ema20 and "ema20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ema20"], name="EMA 20",
                                  line=dict(color="#38bdf8", width=1.5)), row=1, col=1)
    if show_vwap and "vwap" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["vwap"], name="VWAP",
                                  line=dict(color="#fb923c", width=1.5, dash="dash")), row=1, col=1)
    if show_bb and "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper",
                                  line=dict(color="#94a3b8", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_mid"], name="BB Mid",
                                  line=dict(color="#64748b", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower",
                                  line=dict(color="#94a3b8", width=1, dash="dot"),
                                  fill="tonexty", fillcolor="rgba(148,163,184,0.05)"), row=1, col=1)
    if show_supertrend and "supertrend" in df.columns:
        bull = df[df["supertrend_dir"] == 1]
        bear = df[df["supertrend_dir"] == -1]
        fig.add_trace(go.Scatter(x=bull.index, y=bull["supertrend"], name="Supertrend (Bull)",
                                  mode="markers", marker=dict(color="#00ff88", size=3)), row=1, col=1)
        fig.add_trace(go.Scatter(x=bear.index, y=bear["supertrend"], name="Supertrend (Bear)",
                                  mode="markers", marker=dict(color="#ff4444", size=3)), row=1, col=1)

    # Volume
    colors = ["#00ff88" if c >= o else "#ff4444" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color=colors, opacity=0.7), row=2, col=1)

    current_row = 3
    if show_rsi and "rsi" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                                  line=dict(color="#38bdf8", width=1.5)), row=current_row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", line_width=1, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", line_width=1, row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#8b949e", line_width=0.5, row=current_row, col=1)
        fig.update_yaxes(range=[0, 100], row=current_row, col=1)
        current_row += 1

    if show_macd and "macd" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                                  line=dict(color="#38bdf8", width=1.5)), row=current_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal",
                                  line=dict(color="#ffa500", width=1.5)), row=current_row, col=1)
        hist_colors = ["#00ff88" if v >= 0 else "#ff4444" for v in df["macd_hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="Histogram",
                              marker_color=hist_colors, opacity=0.7), row=current_row, col=1)

    fig.update_layout(
        height=760, template="plotly_dark",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        xaxis_rangeslider_visible=False,
        margin=dict(l=8, r=8, t=24, b=8),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10), orientation="h", y=1.02, x=0),
        font=dict(color="#d1d5db"),
    )
    fig.update_xaxes(
        gridcolor="#1f2937",
        zeroline=False,
        showgrid=True,
        showline=False,
        ticks="outside",
        tickfont=dict(color="#9ca3af"),
        rangeslider_visible=False,
    )
    fig.update_yaxes(
        gridcolor="#1f2937",
        zeroline=False,
        showgrid=True,
        showline=False,
        tickfont=dict(color="#9ca3af"),
        side="right",
    )
    for ann in fig.layout.annotations:
        ann.font.color = "#8b949e"
        ann.font.size = 11

    st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}_{interval}_{len(df)}")

    # Key stats
    st.divider()
    last = df.iloc[-1]
    st.subheader(f"{symbol_name} — Key Statistics")
    s_cols = st.columns(6)
    prev_close = df.iloc[-2]["close"] if len(df) > 1 else last["close"]
    chg = last["close"] - prev_close
    chg_pct = (chg / prev_close) * 100

    s_cols[0].metric("Current Price", f"₹{last['close']:,.2f}", f"{chg:+.2f} ({chg_pct:+.2f}%)",
                     delta_color="normal" if chg >= 0 else "inverse")
    s_cols[1].metric("High (Period)", f"₹{df['high'].max():,.2f}")
    s_cols[2].metric("Low (Period)", f"₹{df['low'].min():,.2f}")
    if "rsi" in df.columns and not pd.isna(last["rsi"]):
        rsi_val = last["rsi"]
        rsi_signal = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
        s_cols[3].metric("RSI (14)", f"{rsi_val:.1f}", rsi_signal)
    if "atr" in df.columns and not pd.isna(last["atr"]):
        s_cols[4].metric("ATR (14)", f"₹{last['atr']:,.2f}")
    avg_vol = df["volume"].mean()
    s_cols[5].metric("Avg Volume", f"{avg_vol:,.0f}")

    st.divider()
    st.subheader("Raw Data")
    with st.expander("Show OHLCV Data Table", expanded=False):
        display_df = df[["open", "high", "low", "close", "volume"]].tail(100).copy()
        display_df.columns = ["Open", "High", "Low", "Close", "Volume"]
        display_df = display_df.sort_index(ascending=False)
        st.dataframe(display_df.style.format({
            "Open": "₹{:.2f}", "High": "₹{:.2f}", "Low": "₹{:.2f}", "Close": "₹{:.2f}",
            "Volume": "{:,.0f}",
        }), use_container_width=True)
