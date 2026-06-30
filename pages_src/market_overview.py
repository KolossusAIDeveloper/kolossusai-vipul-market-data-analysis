import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from pages_src.data_utils import INDICES, NSE_STOCKS, get_quote, get_ohlcv


def show():
    st.markdown('<div class="module-header"><h2 style="margin:0">📊 Market Overview</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
    ⚠️ <b>Disclaimer:</b> Market data shown is delayed. This platform is for research purposes only — not investment advice. Past performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)

    col_refresh, col_time = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_time:
        st.markdown(f"<span style='color:#8b949e; font-size:13px'>Last updated: {datetime.now().strftime('%d %b %Y %H:%M:%S IST')}</span>", unsafe_allow_html=True)

    st.subheader("Major Indices")
    idx_cols = st.columns(len(INDICES))
    for i, (name, ticker) in enumerate(INDICES.items()):
        with idx_cols[i]:
            data = get_quote(ticker)
            if data:
                delta_color = "normal" if data["change"] >= 0 else "inverse"
                st.metric(
                    label=name,
                    value=f"₹{data['price']:,.2f}" if "BSESN" in ticker or "NSEI" in ticker else f"{data['price']:,.2f}",
                    delta=f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)",
                    delta_color="normal" if data["change"] >= 0 else "inverse",
                )
            else:
                st.metric(label=name, value="Loading...")

    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Nifty 50 — Intraday Chart")
        nifty_df = get_ohlcv("^NSEI", interval="5m", period="5d")
        if not nifty_df.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.75, 0.25], vertical_spacing=0.03)
            fig.add_trace(go.Candlestick(
                x=nifty_df.index,
                open=nifty_df["open"], high=nifty_df["high"],
                low=nifty_df["low"], close=nifty_df["close"],
                name="Nifty 50",
                increasing_line_color="#00ff88",
                decreasing_line_color="#ff4444",
            ), row=1, col=1)
            # SMA
            nifty_df["sma20"] = nifty_df["close"].rolling(20).mean()
            fig.add_trace(go.Scatter(x=nifty_df.index, y=nifty_df["sma20"],
                                     name="SMA 20", line=dict(color="#ffa500", width=1)), row=1, col=1)
            fig.add_trace(go.Bar(x=nifty_df.index, y=nifty_df["volume"],
                                 name="Volume",
                                 marker_color=["#00ff88" if c >= o else "#ff4444"
                                               for c, o in zip(nifty_df["close"], nifty_df["open"])]),
                          row=2, col=1)
            fig.update_layout(
                height=450, template="plotly_dark",
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                showlegend=True,
            )
            fig.update_xaxes(gridcolor="#1f2937", zeroline=False)
            fig.update_yaxes(gridcolor="#1f2937", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Unable to fetch Nifty 50 data. Markets may be closed.")

    with col2:
        st.subheader("Market Heatmap")
        heat_data = []
        for name, ticker in list(NSE_STOCKS.items())[:12]:
            data = get_quote(ticker)
            if data:
                heat_data.append({
                    "Stock": name[:10],
                    "Change %": data["change_pct"],
                    "Price": data["price"],
                    "Volume": data["volume"],
                })
        if heat_data:
            hdf = pd.DataFrame(heat_data)
            fig_heat = go.Figure(go.Treemap(
                labels=hdf["Stock"],
                parents=[""] * len(hdf),
                values=[abs(v) + 1 for v in hdf["Change %"]],
                customdata=hdf[["Change %", "Price"]],
                hovertemplate="<b>%{label}</b><br>Change: %{customdata[0]:.2f}%<br>Price: ₹%{customdata[1]:,.2f}<extra></extra>",
                marker=dict(
                    colors=hdf["Change %"],
                    colorscale=[[0, "#7f0000"], [0.5, "#1a1a2e"], [1, "#004d20"]],
                    cmid=0,
                    showscale=True,
                ),
                texttemplate="<b>%{label}</b><br>%{customdata[0]:.1f}%",
                textfont=dict(color="white", size=11),
            ))
            fig_heat.update_layout(
                height=450, template="plotly_dark",
                paper_bgcolor="#0d1117",
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()
    st.subheader("NSE Top Stocks")
    stock_data = []
    with st.spinner("Fetching stock data..."):
        for name, ticker in NSE_STOCKS.items():
            data = get_quote(ticker)
            if data:
                stock_data.append({
                    "Stock": name,
                    "Ticker": ticker.replace(".NS", ""),
                    "LTP (₹)": f"₹{data['price']:,.2f}",
                    "Change": f"{'▲' if data['change'] >= 0 else '▼'} {data['change']:+.2f}",
                    "Change %": f"{data['change_pct']:+.2f}%",
                    "High (₹)": f"₹{data['high']:,.2f}",
                    "Low (₹)": f"₹{data['low']:,.2f}",
                    "Volume": f"{data['volume']:,}",
                    "_chg": data["change_pct"],
                })

    if stock_data:
        sdf = pd.DataFrame(stock_data)
        def color_change(val):
            if "▲" in str(val):
                return "color: #00ff88"
            elif "▼" in str(val):
                return "color: #ff4444"
            return ""
        styled = sdf.drop(columns=["_chg"]).style.applymap(color_change, subset=["Change", "Change %"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Global Cues")
    global_indices = {
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
    g_cols = st.columns(5)
    for i, (name, ticker) in enumerate(global_indices.items()):
        with g_cols[i % 5]:
            data = get_quote(ticker)
            if data:
                st.metric(
                    label=name,
                    value=f"{data['price']:,.2f}",
                    delta=f"{data['change_pct']:+.2f}%",
                    delta_color="normal" if data["change"] >= 0 else "inverse",
                )
