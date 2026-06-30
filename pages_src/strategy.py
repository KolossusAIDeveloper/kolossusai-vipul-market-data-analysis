import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pages_src.data_utils import INDICES, NSE_STOCKS, get_ohlcv, compute_indicators

ALL_SYMBOLS = {**INDICES, **NSE_STOCKS}


def run_backtest(df: pd.DataFrame, strategy: dict, capital: float) -> dict:
    df = df.copy()
    df = compute_indicators(df)
    df = df.dropna()

    if df.empty or len(df) < 50:
        return {}

    positions = []
    cash = capital
    holdings = 0
    entry_price = 0.0
    equity_curve = []
    trades = []

    rule = strategy.get("rule", "rsi_oversold")
    rsi_buy = strategy.get("rsi_buy", 30)
    rsi_sell = strategy.get("rsi_sell", 70)
    sl_pct = strategy.get("sl_pct", 2.0) / 100
    target_pct = strategy.get("target_pct", 4.0) / 100

    for i in range(len(df)):
        row = df.iloc[i]
        price = row["close"]
        portfolio_val = cash + holdings * price
        equity_curve.append({"date": df.index[i], "equity": portfolio_val})

        if holdings > 0:
            if price <= entry_price * (1 - sl_pct):
                cash += holdings * price
                trades.append({"date": df.index[i], "type": "SELL (SL)", "price": price,
                                "pnl": (price - entry_price) * holdings, "reason": "Stop Loss"})
                holdings = 0
                entry_price = 0.0
                continue
            elif price >= entry_price * (1 + target_pct):
                cash += holdings * price
                trades.append({"date": df.index[i], "type": "SELL (TP)", "price": price,
                                "pnl": (price - entry_price) * holdings, "reason": "Target Hit"})
                holdings = 0
                entry_price = 0.0
                continue

        if holdings == 0:
            buy_signal = False
            sell_signal = False

            if rule == "rsi_oversold":
                buy_signal = row["rsi"] < rsi_buy
            elif rule == "macd_crossover":
                if i > 0:
                    prev = df.iloc[i - 1]
                    buy_signal = (prev["macd"] < prev["macd_signal"]) and (row["macd"] > row["macd_signal"])
            elif rule == "sma_crossover":
                if i > 0:
                    prev = df.iloc[i - 1]
                    buy_signal = (prev["sma20"] < prev["sma50"]) and (row["sma20"] > row["sma50"])
            elif rule == "supertrend":
                buy_signal = row["supertrend_dir"] == 1
            elif rule == "rsi_bb":
                buy_signal = (row["rsi"] < rsi_buy) and (price <= row["bb_lower"])

            if buy_signal and cash > price:
                qty = int(cash * 0.95 / price)
                if qty > 0:
                    cost = qty * price
                    cash -= cost
                    holdings = qty
                    entry_price = price
                    trades.append({"date": df.index[i], "type": "BUY", "price": price,
                                   "pnl": 0, "reason": "Entry Signal"})

        if holdings > 0 and rule == "rsi_oversold" and row["rsi"] > rsi_sell:
            cash += holdings * price
            trades.append({"date": df.index[i], "type": "SELL (RSI)", "price": price,
                            "pnl": (price - entry_price) * holdings, "reason": "RSI Overbought"})
            holdings = 0
            entry_price = 0.0

    # Final close
    if holdings > 0:
        final_price = df.iloc[-1]["close"]
        cash += holdings * final_price
        trades.append({"date": df.index[-1], "type": "SELL (EOD)", "price": final_price,
                        "pnl": (final_price - entry_price) * holdings, "reason": "Period End"})
        holdings = 0

    eq_df = pd.DataFrame(equity_curve)
    final_equity = cash
    total_return = (final_equity - capital) / capital * 100
    n_years = len(df) / 252
    cagr = ((final_equity / capital) ** (1 / max(n_years, 0.1)) - 1) * 100

    returns = eq_df["equity"].pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    roll_max = eq_df["equity"].cummax()
    drawdown = (eq_df["equity"] - roll_max) / roll_max * 100
    max_dd = drawdown.min()

    trade_df = pd.DataFrame(trades)
    wins = trade_df[trade_df["pnl"] > 0] if not trade_df.empty else pd.DataFrame()
    losses = trade_df[trade_df["pnl"] < 0] if not trade_df.empty else pd.DataFrame()
    sell_trades = [t for t in trades if "SELL" in t["type"]]
    win_rate = len(wins) / max(len(sell_trades), 1) * 100

    return {
        "final_equity": final_equity,
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "n_trades": len(sell_trades),
        "avg_win": wins["pnl"].mean() if not wins.empty else 0,
        "avg_loss": losses["pnl"].mean() if not losses.empty else 0,
        "equity_curve": eq_df,
        "trades": trade_df,
        "drawdown": drawdown.values,
    }


def show():
    st.markdown('<div class="module-header"><h2 style="margin:0">⚙️ Strategy Builder & Backtesting</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
    ⚠️ <b>Backtesting Disclaimer:</b> Historical backtest results do NOT guarantee future performance. Backtests do not account for slippage, market impact, brokerage fees, or execution delays. Results are for research only.
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔧 Strategy Builder", "📊 Backtest Results"])

    with tab1:
        st.subheader("Build Your Strategy")

        col_s, col_t = st.columns([2, 1])
        with col_s:
            symbol_name = st.selectbox("Symbol", list(ALL_SYMBOLS.keys()), index=0, key="bt_sym")
        with col_t:
            capital = st.number_input("Starting Capital (₹)", min_value=10000, max_value=10000000,
                                       value=100000, step=10000)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            period_map = {"6 Months": "6mo", "1 Year": "1y", "2 Years": "2y", "5 Years": "5y"}
            period_label = st.selectbox("Backtest Period", list(period_map.keys()), index=1)
        with col_d2:
            interval_map = {"Daily": "1d", "Weekly": "1wk"}
            interval_label = st.selectbox("Bar Interval", list(interval_map.keys()), index=0)

        st.divider()
        st.subheader("Strategy Rules")

        strategy_map = {
            "RSI Oversold/Overbought": "rsi_oversold",
            "MACD Crossover": "macd_crossover",
            "SMA 20/50 Crossover": "sma_crossover",
            "Supertrend": "supertrend",
            "RSI + Bollinger Band Combo": "rsi_bb",
        }

        strat_label = st.selectbox("Entry Strategy", list(strategy_map.keys()), index=0)
        rule = strategy_map[strat_label]

        col_r1, col_r2, col_r3, col_r4 = st.columns(4)

        with col_r1:
            rsi_buy = st.slider("RSI Buy Level", 10, 40, 30, disabled=(rule not in ["rsi_oversold", "rsi_bb"]))
        with col_r2:
            rsi_sell = st.slider("RSI Sell Level", 60, 90, 70, disabled=(rule not in ["rsi_oversold"]))
        with col_r3:
            sl_pct = st.slider("Stop Loss %", 0.5, 10.0, 2.0, 0.5)
        with col_r4:
            target_pct = st.slider("Target %", 1.0, 20.0, 4.0, 0.5)

        # Visual strategy display
        st.markdown("**Strategy Logic (Visual)**")
        st.markdown(f"""
        <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:16px; font-family:monospace; font-size:13px; color:#e6edf3;">
        <span style="color:#38bdf8">STRATEGY:</span> {strat_label}<br>
        <span style="color:#38bdf8">SYMBOL:</span> {symbol_name}<br>
        <span style="color:#38bdf8">ENTRY:</span> {'RSI < ' + str(rsi_buy) if 'rsi' in rule else ('MACD crosses above Signal' if rule == 'macd_crossover' else ('SMA20 crosses above SMA50' if rule == 'sma_crossover' else 'Supertrend = Bullish'))}<br>
        <span style="color:#38bdf8">EXIT:</span> {'RSI > ' + str(rsi_sell) + ' OR ' if rule == 'rsi_oversold' else ''}<span style="color:#ff4444">Stop Loss @ -{sl_pct:.1f}%</span> | <span style="color:#00ff88">Target @ +{target_pct:.1f}%</span><br>
        <span style="color:#38bdf8">POSITION SIZE:</span> 95% of available capital (full position)<br>
        <span style="color:#38bdf8">RISK MGMT:</span> Hard SL + Target exit
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Run Backtest", use_container_width=True, type="primary")

        if run_btn:
            ticker = ALL_SYMBOLS[symbol_name]
            period = period_map[period_label]
            interval = interval_map[interval_label]
            strategy = {
                "rule": rule,
                "rsi_buy": rsi_buy,
                "rsi_sell": rsi_sell,
                "sl_pct": sl_pct,
                "target_pct": target_pct,
            }
            with st.spinner("Running backtest..."):
                df = get_ohlcv(ticker, interval=interval, period=period)
                bt = run_backtest(df, strategy, float(capital))

            if bt:
                st.session_state["bt_result"] = bt
                st.session_state["bt_symbol"] = symbol_name
                st.success("Backtest complete! View results in the 'Backtest Results' tab.")
            else:
                st.error("Insufficient data for backtest. Try a longer period.")

    with tab2:
        if "bt_result" not in st.session_state:
            st.info("Run a backtest from the Strategy Builder tab to see results here.")
            return

        bt = st.session_state["bt_result"]
        symbol_name = st.session_state.get("bt_symbol", "")
        st.subheader(f"Backtest Results — {symbol_name}")

        # Metrics
        m_cols = st.columns(5)
        m_cols[0].metric("Total Return", f"{bt['total_return']:+.2f}%",
                          delta_color="normal" if bt["total_return"] >= 0 else "inverse")
        m_cols[1].metric("CAGR", f"{bt['cagr']:+.2f}%")
        m_cols[2].metric("Sharpe Ratio", f"{bt['sharpe']:.2f}")
        m_cols[3].metric("Max Drawdown", f"{bt['max_drawdown']:.2f}%",
                          delta_color="inverse")
        m_cols[4].metric("Win Rate", f"{bt['win_rate']:.1f}%")

        m_cols2 = st.columns(4)
        m_cols2[0].metric("Total Trades", bt["n_trades"])
        m_cols2[1].metric("Final Equity", f"₹{bt['final_equity']:,.0f}")
        m_cols2[2].metric("Avg Win", f"₹{bt['avg_win']:,.0f}" if bt["avg_win"] else "—")
        m_cols2[3].metric("Avg Loss", f"₹{bt['avg_loss']:,.0f}" if bt["avg_loss"] else "—")

        st.divider()

        # Equity curve
        eq_df = bt["equity_curve"]
        fig_eq = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.7, 0.3], vertical_spacing=0.05,
                                subplot_titles=["Equity Curve", "Drawdown %"])
        fig_eq.add_trace(go.Scatter(
            x=eq_df["date"], y=eq_df["equity"], name="Portfolio Value",
            line=dict(color="#38bdf8", width=2),
            fill="tozeroy", fillcolor="rgba(56,189,248,0.1)",
        ), row=1, col=1)

        # Mark trades
        trade_df = bt["trades"]
        if not trade_df.empty:
            buys = trade_df[trade_df["type"] == "BUY"]
            sells = trade_df[trade_df["type"].str.contains("SELL")]
            if not buys.empty:
                buy_eq = eq_df[eq_df["date"].isin(buys["date"])]["equity"].values
                fig_eq.add_trace(go.Scatter(
                    x=buys["date"], y=buy_eq[:len(buys)],
                    mode="markers", name="Buy", marker=dict(symbol="triangle-up", size=10, color="#00ff88"),
                ), row=1, col=1)
            if not sells.empty:
                sell_eq = eq_df[eq_df["date"].isin(sells["date"])]["equity"].values
                fig_eq.add_trace(go.Scatter(
                    x=sells["date"], y=sell_eq[:len(sells)],
                    mode="markers", name="Sell", marker=dict(symbol="triangle-down", size=10, color="#ff4444"),
                ), row=1, col=1)

        fig_eq.add_trace(go.Scatter(
            x=eq_df["date"], y=bt["drawdown"], name="Drawdown",
            fill="tozeroy", fillcolor="rgba(255,68,68,0.3)",
            line=dict(color="#ff4444", width=1),
        ), row=2, col=1)

        fig_eq.update_layout(
            height=500, template="plotly_dark",
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0.5)", font=dict(size=11)),
        )
        fig_eq.update_xaxes(gridcolor="#1f2937")
        fig_eq.update_yaxes(gridcolor="#1f2937")
        st.plotly_chart(fig_eq, use_container_width=True)

        # Trade log
        st.subheader("Trade Log")
        if not trade_df.empty:
            display_trades = trade_df.copy()
            display_trades["price"] = display_trades["price"].apply(lambda x: f"₹{x:,.2f}")
            display_trades["pnl"] = display_trades["pnl"].apply(
                lambda x: f"{'▲' if x > 0 else '▼' if x < 0 else '—'} ₹{abs(x):,.0f}" if x != 0 else "—")

            def trade_color(val):
                if "▲" in str(val):
                    return "color: #00ff88"
                elif "▼" in str(val):
                    return "color: #ff4444"
                return ""

            styled_trades = display_trades.style.applymap(trade_color, subset=["pnl"])
            st.dataframe(styled_trades, use_container_width=True, hide_index=True)
        else:
            st.info("No trades executed in this backtest period.")
