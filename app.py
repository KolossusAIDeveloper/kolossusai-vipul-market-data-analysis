import streamlit as st

st.set_page_config(
    page_title="Market Data Analysis — Indian Markets",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global dark theme CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; color: #e6edf3; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
    .disclaimer-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #e74c3c;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 12px;
        color: #e74c3c;
        margin-bottom: 16px;
    }
    .signal-up { color: #00ff88; font-weight: bold; font-size: 18px; }
    .signal-down { color: #ff4444; font-weight: bold; font-size: 18px; }
    .signal-neutral { color: #ffaa00; font-weight: bold; font-size: 18px; }
    div[data-testid="stMetricValue"] { color: #00ff88; }
    .stSelectbox label, .stSlider label { color: #8b949e; }
    h1, h2, h3 { color: #e6edf3; }
    .module-header {
        background: linear-gradient(90deg, #0d1117 0%, #161b22 100%);
        border-left: 4px solid #238636;
        padding: 8px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.image("https://img.icons8.com/fluency/96/combo-chart.png", width=60)
st.sidebar.title("Market Data Analysis")
st.sidebar.markdown("**AI-Powered Indian Markets**")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Market Overview",
        "📈 Live Charts & Indicators",
        "🤖 AI Sentiment & Prediction",
        "⚙️ Strategy Builder & Backtest",
        "📋 Paper Trading",
        "ℹ️ About",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("""
<div style='font-size:11px; color:#8b949e; line-height:1.5;'>
⚠️ <b>Disclaimer:</b> All signals are probabilistic research tools, not financial advice. Past backtest performance does not guarantee future results. You are solely responsible for compliance with SEBI and your broker's algo trading requirements.
</div>
""", unsafe_allow_html=True)

# Route to pages
if page == "📊 Market Overview":
    from pages_src import market_overview
    market_overview.show()
elif page == "📈 Live Charts & Indicators":
    from pages_src import charts
    charts.show()
elif page == "🤖 AI Sentiment & Prediction":
    from pages_src import sentiment
    sentiment.show()
elif page == "⚙️ Strategy Builder & Backtest":
    from pages_src import strategy
    strategy.show()
elif page == "📋 Paper Trading":
    from pages_src import paper_trading
    paper_trading.show()
elif page == "ℹ️ About":
    from pages_src import about
    about.show()
