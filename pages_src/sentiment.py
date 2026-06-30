import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import feedparser
import requests
from datetime import datetime, timedelta
from pages_src.data_utils import get_ohlcv, get_quote, compute_indicators


RSS_FEEDS = {
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rss.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
}

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


def score_headline(text: str) -> float:
    words = text.lower().split()
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total


@st.cache_data(ttl=900)
def fetch_news() -> list:
    articles = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                published = entry.get("published", "")
                score = score_headline(title)
                articles.append({
                    "Source": source,
                    "Headline": title,
                    "Published": published,
                    "Sentiment Score": round(score, 3),
                    "Sentiment": "Positive 📈" if score > 0.1 else ("Negative 📉" if score < -0.1 else "Neutral ➡️"),
                    "Link": entry.get("link", "#"),
                })
        except Exception:
            continue
    return articles


def compute_prediction(ticker: str) -> dict:
    df = get_ohlcv(ticker, interval="1d", period="6mo")
    if df.empty or len(df) < 30:
        return {}
    df = compute_indicators(df)
    last = df.iloc[-1]

    signals = []
    score = 0

    # RSI signal
    rsi = last.get("rsi", 50)
    if not pd.isna(rsi):
        if rsi < 30:
            signals.append({"Indicator": "RSI", "Signal": "Bullish", "Detail": f"RSI={rsi:.1f} (Oversold)"})
            score += 2
        elif rsi > 70:
            signals.append({"Indicator": "RSI", "Signal": "Bearish", "Detail": f"RSI={rsi:.1f} (Overbought)"})
            score -= 2
        else:
            signals.append({"Indicator": "RSI", "Signal": "Neutral", "Detail": f"RSI={rsi:.1f}"})

    # MACD
    macd = last.get("macd", 0)
    macd_sig = last.get("macd_signal", 0)
    if not pd.isna(macd) and not pd.isna(macd_sig):
        if macd > macd_sig:
            signals.append({"Indicator": "MACD", "Signal": "Bullish", "Detail": "MACD above signal line"})
            score += 1.5
        else:
            signals.append({"Indicator": "MACD", "Signal": "Bearish", "Detail": "MACD below signal line"})
            score -= 1.5

    # SMA cross
    sma20 = last.get("sma20")
    sma50 = last.get("sma50")
    price = last["close"]
    if sma20 and sma50:
        if price > sma20 > sma50:
            signals.append({"Indicator": "SMA Cross", "Signal": "Bullish", "Detail": "Price > SMA20 > SMA50"})
            score += 2
        elif price < sma20 < sma50:
            signals.append({"Indicator": "SMA Cross", "Signal": "Bearish", "Detail": "Price < SMA20 < SMA50"})
            score -= 2
        else:
            signals.append({"Indicator": "SMA Cross", "Signal": "Neutral", "Detail": "Mixed MA signals"})

    # Supertrend
    st_dir = last.get("supertrend_dir", 0)
    if st_dir == 1:
        signals.append({"Indicator": "Supertrend", "Signal": "Bullish", "Detail": "Supertrend trending up"})
        score += 1.5
    elif st_dir == -1:
        signals.append({"Indicator": "Supertrend", "Signal": "Bearish", "Detail": "Supertrend trending down"})
        score -= 1.5

    # Stochastic
    stoch = last.get("stoch_k", 50)
    if not pd.isna(stoch):
        if stoch < 20:
            signals.append({"Indicator": "Stochastic", "Signal": "Bullish", "Detail": f"Stoch K={stoch:.1f} (Oversold)"})
            score += 1
        elif stoch > 80:
            signals.append({"Indicator": "Stochastic", "Signal": "Bearish", "Detail": f"Stoch K={stoch:.1f} (Overbought)"})
            score -= 1

    # Volume trend
    recent_vol = df["volume"].tail(5).mean()
    avg_vol = df["volume"].tail(20).mean()
    recent_return = (price - df["close"].iloc[-5]) / df["close"].iloc[-5] * 100
    if recent_vol > avg_vol * 1.3 and recent_return > 0:
        signals.append({"Indicator": "Volume", "Signal": "Bullish", "Detail": "High volume on up move"})
        score += 1
    elif recent_vol > avg_vol * 1.3 and recent_return < 0:
        signals.append({"Indicator": "Volume", "Signal": "Bearish", "Detail": "High volume on down move"})
        score -= 1
    else:
        signals.append({"Indicator": "Volume", "Signal": "Neutral", "Detail": "Normal volume"})

    # Normalize confidence
    max_score = 9.0
    confidence = min(abs(score) / max_score * 100, 95)

    if score > 1.5:
        direction = "UP ▲"
        direction_color = "#00ff88"
    elif score < -1.5:
        direction = "DOWN ▼"
        direction_color = "#ff4444"
    else:
        direction = "SIDEWAYS ➡️"
        direction_color = "#ffa500"

    # Generate rationale
    bull_signals = [s for s in signals if s["Signal"] == "Bullish"]
    bear_signals = [s for s in signals if s["Signal"] == "Bearish"]

    if direction == "UP ▲":
        rationale = f"Bullish bias with {confidence:.0f}% confidence. Key drivers: {', '.join([s['Detail'] for s in bull_signals[:2]])}. "
        if bear_signals:
            rationale += f"Caution: {bear_signals[0]['Detail']}."
    elif direction == "DOWN ▼":
        rationale = f"Bearish bias with {confidence:.0f}% confidence. Key drivers: {', '.join([s['Detail'] for s in bear_signals[:2]])}. "
        if bull_signals:
            rationale += f"Caution: {bull_signals[0]['Detail']}."
    else:
        rationale = f"Mixed signals with {confidence:.0f}% confidence. No clear directional bias — {len(bull_signals)} bullish vs {len(bear_signals)} bearish signals. Sideways or consolidation phase likely."

    return {
        "direction": direction,
        "direction_color": direction_color,
        "confidence": confidence,
        "score": score,
        "signals": signals,
        "rationale": rationale,
    }


def show():
    st.markdown('<div class="module-header"><h2 style="margin:0">🤖 AI Sentiment & Market Prediction</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
    ⚠️ <b>Important Disclaimer:</b> All predictions shown here are probabilistic research signals generated from technical indicators and news sentiment analysis. They are NOT financial advice and do NOT guarantee returns. SEBI explicitly penalizes "guaranteed return" claims. Use these signals for research purposes only.
    </div>
    """, unsafe_allow_html=True)

    from pages_src.data_utils import INDICES, NSE_STOCKS
    ALL_SYMBOLS = {**INDICES, **NSE_STOCKS}

    col1, col2 = st.columns([2, 1])
    with col1:
        symbol_name = st.selectbox("Select Symbol for Prediction", list(ALL_SYMBOLS.keys()), index=0)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_predict = st.button("🤖 Generate AI Signal", use_container_width=True)

    ticker = ALL_SYMBOLS[symbol_name]

    # Prediction
    with st.spinner("Computing technical signals..."):
        result = compute_prediction(ticker)

    if result:
        st.subheader(f"Prediction: {symbol_name}")

        p_col1, p_col2, p_col3 = st.columns([1, 1, 2])

        with p_col1:
            st.markdown(f"""
            <div style="background:#161b22; border: 2px solid {result['direction_color']}; border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#8b949e; margin-bottom:8px;">Predicted Direction</div>
                <div style="font-size:32px; font-weight:bold; color:{result['direction_color']};">{result['direction']}</div>
            </div>
            """, unsafe_allow_html=True)

        with p_col2:
            conf = result["confidence"]
            color = "#00ff88" if conf > 70 else ("#ffa500" if conf > 50 else "#ff4444")
            st.markdown(f"""
            <div style="background:#161b22; border: 2px solid {color}; border-radius:12px; padding:20px; text-align:center;">
                <div style="font-size:14px; color:#8b949e; margin-bottom:8px;">Model Confidence</div>
                <div style="font-size:32px; font-weight:bold; color:{color};">{conf:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with p_col3:
            st.markdown(f"""
            <div style="background:#161b22; border: 1px solid #30363d; border-radius:12px; padding:20px;">
                <div style="font-size:14px; color:#8b949e; margin-bottom:8px;">AI Rationale</div>
                <div style="font-size:14px; color:#e6edf3; line-height:1.6;">{result['rationale']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Signal breakdown
        st.subheader("Signal Breakdown")
        sig_df = pd.DataFrame(result["signals"])

        def signal_style(val):
            if val == "Bullish":
                return "color: #00ff88; font-weight: bold"
            elif val == "Bearish":
                return "color: #ff4444; font-weight: bold"
            return "color: #ffa500"

        styled_sig = sig_df.style.applymap(signal_style, subset=["Signal"])
        st.dataframe(styled_sig, use_container_width=True, hide_index=True)

        # Gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=result["score"],
            title={"text": "Signal Score", "font": {"color": "#e6edf3"}},
            gauge={
                "axis": {"range": [-9, 9], "tickcolor": "#8b949e"},
                "bar": {"color": result["direction_color"]},
                "bgcolor": "#161b22",
                "bordercolor": "#30363d",
                "steps": [
                    {"range": [-9, -3], "color": "#3d0000"},
                    {"range": [-3, 3], "color": "#1a1a00"},
                    {"range": [3, 9], "color": "#003d00"},
                ],
                "threshold": {
                    "line": {"color": "#e6edf3", "width": 2},
                    "thickness": 0.75,
                    "value": result["score"],
                },
            },
            number={"font": {"color": result["direction_color"]}},
        ))
        fig_gauge.update_layout(
            height=250, template="plotly_dark",
            paper_bgcolor="#0d1117",
            margin=dict(l=20, r=20, t=30, b=0),
            font=dict(color="#e6edf3"),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # News & Sentiment
    st.subheader("📰 News Sentiment Analysis")
    col_news, col_sentiment = st.columns([1, 1])

    with col_news:
        st.markdown("**Latest Financial News Headlines**")
        with st.spinner("Fetching news feeds..."):
            articles = fetch_news()

        if articles:
            for a in articles[:15]:
                color = "#00ff88" if "Positive" in a["Sentiment"] else ("#ff4444" if "Negative" in a["Sentiment"] else "#ffa500")
                score_bar = "█" * int(abs(a["Sentiment Score"]) * 10) if a["Sentiment Score"] != 0 else "—"
                st.markdown(f"""
                <div style="background:#161b22; border-left: 3px solid {color}; border-radius: 0 6px 6px 0; padding:8px 12px; margin-bottom:6px;">
                    <div style="font-size:13px; color:#e6edf3;">{a['Headline'][:90]}{'...' if len(a['Headline']) > 90 else ''}</div>
                    <div style="font-size:11px; color:#8b949e; margin-top:4px;">{a['Source']} | <span style="color:{color}">{a['Sentiment']}</span> | Score: {a['Sentiment Score']:+.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("News feeds unavailable. Check your internet connection.")

    with col_sentiment:
        if articles:
            st.markdown("**Sentiment Distribution**")
            sent_counts = pd.Series([a["Sentiment"] for a in articles]).value_counts()
            fig_pie = go.Figure(go.Pie(
                labels=sent_counts.index,
                values=sent_counts.values,
                marker_colors=["#00ff88", "#ff4444", "#ffa500"],
                hole=0.4,
                textfont=dict(color="white"),
            ))
            fig_pie.update_layout(
                height=250, template="plotly_dark",
                paper_bgcolor="#0d1117",
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=True,
                legend=dict(font=dict(color="#e6edf3")),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("**Sentiment Score Distribution**")
            scores = [a["Sentiment Score"] for a in articles]
            fig_hist = go.Figure(go.Histogram(
                x=scores, nbinsx=20,
                marker_color="#38bdf8",
                opacity=0.8,
            ))
            fig_hist.add_vline(x=np.mean(scores), line_dash="dash",
                               line_color="#ffa500",
                               annotation_text=f"Avg: {np.mean(scores):.2f}",
                               annotation_font_color="#ffa500")
            fig_hist.update_layout(
                height=200, template="plotly_dark",
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="Sentiment Score",
                yaxis_title="Count",
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            avg_score = np.mean(scores)
            overall = "Positive 📈" if avg_score > 0.05 else ("Negative 📉" if avg_score < -0.05 else "Neutral ➡️")
            st.metric("Overall Market Sentiment", overall, f"Avg score: {avg_score:+.3f}")

    # Option Chain PCR simulation
    st.divider()
    st.subheader("📊 Option Chain Insights (Simulated PCR)")
    st.info("💡 Connect a broker API (Zerodha Kite / Upstox / Angel One) for live option chain data. Shown below is a simulated example.")

    np.random.seed(42)
    strikes = list(range(23000, 25001, 100))
    ce_oi = np.random.exponential(50000, len(strikes)) + np.random.randint(10000, 30000, len(strikes))
    pe_oi = np.random.exponential(60000, len(strikes)) + np.random.randint(10000, 30000, len(strikes))
    pcr = pe_oi.sum() / ce_oi.sum()

    pcr_col1, pcr_col2 = st.columns([1, 2])
    with pcr_col1:
        color = "#00ff88" if pcr > 1 else "#ff4444"
        st.markdown(f"""
        <div style="background:#161b22; border: 2px solid {color}; border-radius:12px; padding:24px; text-align:center;">
            <div style="font-size:14px; color:#8b949e;">Put-Call Ratio (PCR)</div>
            <div style="font-size:48px; font-weight:bold; color:{color}; margin:8px 0;">{pcr:.2f}</div>
            <div style="font-size:13px; color:{color};">{'Bullish Signal (PCR > 1)' if pcr > 1 else 'Bearish Signal (PCR < 1)'}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        max_pain_idx = np.argmin(np.abs(np.cumsum(pe_oi) - np.cumsum(ce_oi)))
        st.metric("Max Pain Strike", f"₹{strikes[max_pain_idx]:,}")

    with pcr_col2:
        fig_oc = go.Figure()
        fig_oc.add_trace(go.Bar(x=strikes, y=ce_oi, name="Call OI", marker_color="#ff4444", opacity=0.8))
        fig_oc.add_trace(go.Bar(x=strikes, y=pe_oi, name="Put OI", marker_color="#00ff88", opacity=0.8))
        fig_oc.update_layout(
            height=300, template="plotly_dark",
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            barmode="group",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title="Strike Price",
            yaxis_title="Open Interest",
            legend=dict(font=dict(color="#e6edf3")),
        )
        st.plotly_chart(fig_oc, use_container_width=True)
