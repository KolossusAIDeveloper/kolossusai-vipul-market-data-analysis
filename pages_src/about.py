import streamlit as st


def show():
    st.markdown('<div class="module-header"><h2 style="margin:0">ℹ️ About Market Data Analysis</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box" style="font-size:13px; line-height:1.8;">
    ⚠️ <b>MANDATORY DISCLAIMER — PLEASE READ:</b><br>
    This platform is a <b>research and educational tool only</b>. All market predictions, signals, and sentiment scores are probabilistic estimates — not financial advice.<br>
    <b>Past backtest performance does NOT guarantee future results.</b><br>
    You are solely responsible for your own trading decisions and for compliance with SEBI's algo trading framework and your broker's requirements.<br>
    SEBI explicitly prohibits "guaranteed return" claims. This platform makes none.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ## AI-Powered Nifty/Sensex Trading Platform

    A full-stack market research platform for Indian equity markets (NSE/BSE), covering:

    ### Modules

    | Module | Description | Status |
    |---|---|---|
    | 📊 Market Overview | Live quotes, indices heatmap, global cues | ✅ Live |
    | 📈 Charts & Indicators | Candlestick charts with 10+ technical indicators | ✅ Live |
    | 🤖 AI Sentiment | News sentiment + technical signal prediction | ✅ Live |
    | ⚙️ Strategy Builder | Visual strategy builder + backtesting engine | ✅ Live |
    | 📋 Paper Trading | Simulated order placement with risk controls | ✅ Live |

    ### Technical Stack
    """)

    cols = st.columns(3)
    with cols[0]:
        st.markdown("""
        **Frontend / UI**
        - Streamlit (Python)
        - Plotly for interactive charts
        - Dark theme throughout
        """)
    with cols[1]:
        st.markdown("""
        **Data Sources**
        - yfinance (market data)
        - Financial RSS feeds (news)
        - Simulated option chain (PCR)
        """)
    with cols[2]:
        st.markdown("""
        **AI / Analytics**
        - Keyword-based sentiment scoring
        - Technical indicator signals (RSI, MACD, SMA, Supertrend)
        - Backtest engine with equity curves
        """)

    st.divider()

    st.subheader("Available Indicators")
    ind_cols = st.columns(4)
    indicators = [
        ("SMA 20 / 50", "Simple Moving Average"),
        ("EMA 20", "Exponential Moving Average"),
        ("Bollinger Bands", "Volatility bands (2σ)"),
        ("RSI (14)", "Relative Strength Index"),
        ("MACD", "Moving Average Convergence/Divergence"),
        ("Stochastic", "Stochastic Oscillator K/D"),
        ("ATR (14)", "Average True Range"),
        ("VWAP", "Volume-Weighted Average Price"),
        ("Supertrend", "Trend-following indicator"),
        ("Volume Profile", "Volume bar overlay"),
    ]
    for i, (name, desc) in enumerate(indicators):
        with ind_cols[i % 4]:
            st.markdown(f"""
            <div style="background:#161b22; border: 1px solid #30363d; border-radius:6px; padding:8px 10px; margin-bottom:6px;">
                <div style="color:#38bdf8; font-size:13px; font-weight:bold;">{name}</div>
                <div style="color:#8b949e; font-size:11px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Supported Symbols")
    st.markdown("""
    **Indices:** Nifty 50, Sensex, Bank Nifty, Nifty IT, Nifty Pharma, Nifty Midcap 100

    **Stocks (NSE):** Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, HUL, ITC, Kotak Mahindra, L&T, Axis Bank, Bharti Airtel, Wipro, HCL Tech, Asian Paints, Bajaj Finance, Maruti Suzuki, Sun Pharma, Titan, UltraTech Cement, NTPC

    **Global:** S&P 500, NASDAQ, Dow Jones, FTSE 100, Nikkei 225, Hang Seng, Crude Oil, Gold, USD/INR, VIX
    """)

    st.divider()
    st.subheader("SEBI Compliance Notes")
    st.markdown("""
    Per SEBI's retail algo trading framework (effective April 1, 2026):

    - **OAuth + 2FA** is mandatory for all broker API sessions
    - **Static IP whitelisting** is required for automated order placement
    - **Daily session reset** — broker tokens must not persist indefinitely
    - **Algo/Strategy ID tagging** — all bot-placed orders must carry a broker-issued Algo-ID
    - **No guaranteed return claims** — this platform makes none
    - **Personal use only** (< 10 orders/second) does not require separate strategy registration

    Confirm current requirements with your broker before going live.
    """)

    st.divider()
    st.subheader("Broker APIs Supported (via BrokerAdapter pattern)")
    broker_cols = st.columns(5)
    brokers = [
        ("Zerodha", "Kite Connect", "₹2000/mo"),
        ("Upstox", "Upstox API", "Free"),
        ("Angel One", "SmartAPI", "Free"),
        ("Fyers", "Fyers API", "Free"),
        ("5paisa", "5paisa API", "Free"),
    ]
    for i, (broker, api, cost) in enumerate(brokers):
        with broker_cols[i]:
            st.markdown(f"""
            <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:10px; text-align:center;">
                <div style="color:#e6edf3; font-weight:bold; font-size:14px;">{broker}</div>
                <div style="color:#8b949e; font-size:11px;">{api}</div>
                <div style="color:#38bdf8; font-size:11px; margin-top:4px;">{cost}</div>
            </div>
            """, unsafe_allow_html=True)
