import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from pages_src.data_utils import INDICES, NSE_STOCKS, get_quote

ALL_SYMBOLS = {**INDICES, **NSE_STOCKS}


def init_session():
    if "pt_portfolio" not in st.session_state:
        st.session_state["pt_portfolio"] = {
            "cash": 500000.0,
            "positions": {},
            "orders": [],
            "pnl_history": [{"time": datetime.now().strftime("%H:%M:%S"), "pnl": 0.0, "equity": 500000.0}],
        }
    if "pt_log" not in st.session_state:
        st.session_state["pt_log"] = []


def show():
    init_session()
    pt = st.session_state["pt_portfolio"]

    st.markdown('<div class="module-header"><h2 style="margin:0">📋 Paper Trading Simulator</h2></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
    ⚠️ <b>Paper Trading Mode — Simulated Fills Only.</b> Orders placed here are NOT real. No real money is at risk.
    This is a simulation to test strategies before deploying real capital. Fills are at last traded price (no slippage simulation).
    By SEBI's retail algo framework (effective April 1, 2026), paper trading is a mandatory staging step before live algo deployment.
    </div>
    """, unsafe_allow_html=True)

    # Portfolio summary
    positions = pt["positions"]
    cash = pt["cash"]

    total_market_value = 0.0
    position_data = []
    for sym, pos in positions.items():
        q = get_quote(pos["ticker"])
        ltp = q.get("price", pos["avg_price"]) if q else pos["avg_price"]
        mkt_val = ltp * pos["qty"]
        cost = pos["avg_price"] * pos["qty"]
        unrealized_pnl = mkt_val - cost
        unrealized_pct = (unrealized_pnl / cost) * 100 if cost > 0 else 0
        total_market_value += mkt_val
        position_data.append({
            "Symbol": sym,
            "Qty": pos["qty"],
            "Avg Price": f"₹{pos['avg_price']:,.2f}",
            "LTP": f"₹{ltp:,.2f}",
            "Market Value": f"₹{mkt_val:,.2f}",
            "Unrealized P&L": f"{'▲' if unrealized_pnl >= 0 else '▼'} ₹{abs(unrealized_pnl):,.2f}",
            "P&L %": f"{unrealized_pct:+.2f}%",
            "_pnl": unrealized_pnl,
        })

    total_equity = cash + total_market_value
    initial_capital = 500000.0
    total_pnl = total_equity - initial_capital
    total_pnl_pct = (total_pnl / initial_capital) * 100

    # Dashboard metrics
    m_cols = st.columns(5)
    m_cols[0].metric("Total Equity", f"₹{total_equity:,.0f}",
                      f"{total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)",
                      delta_color="normal" if total_pnl >= 0 else "inverse")
    m_cols[1].metric("Available Cash", f"₹{cash:,.0f}")
    m_cols[2].metric("Market Value", f"₹{total_market_value:,.0f}")
    m_cols[3].metric("Open Positions", len(positions))
    m_cols[4].metric("Total Orders", len(pt["orders"]))

    st.divider()

    col_order, col_positions = st.columns([1, 2])

    with col_order:
        st.subheader("Place Order")

        order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True)
        symbol_name = st.selectbox("Symbol", list(ALL_SYMBOLS.keys()), key="pt_sym")
        ticker = ALL_SYMBOLS[symbol_name]

        q = get_quote(ticker)
        if q:
            st.markdown(f"""
            <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:8px 12px; margin-bottom:8px;">
                <span style="color:#8b949e; font-size:12px;">LTP:</span>
                <span style="font-size:18px; font-weight:bold; color:#e6edf3;"> ₹{q['price']:,.2f}</span>
                <span style="font-size:12px; color:{'#00ff88' if q['change'] >= 0 else '#ff4444'};">
                    {q['change']:+.2f} ({q['change_pct']:+.2f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
            ltp = q["price"]
        else:
            st.warning("Price unavailable")
            ltp = 0.0

        qty = st.number_input("Quantity", min_value=1, max_value=10000, value=10, step=1)
        order_price_type = st.radio("Price Type", ["Market", "Limit"], horizontal=True)

        limit_price = ltp
        if order_price_type == "Limit":
            limit_price = st.number_input("Limit Price (₹)", min_value=0.01, value=float(ltp), step=0.05)

        # Risk checks
        order_value = qty * (limit_price if order_price_type == "Limit" else ltp)
        st.markdown(f"**Order Value:** ₹{order_value:,.2f}")

        daily_loss_limit = 0.05
        if total_pnl < -(initial_capital * daily_loss_limit):
            st.error(f"⛔ Daily max-loss kill switch triggered! ({daily_loss_limit*100:.0f}% loss reached). Trading disabled for today.")
            return

        col_buy, col_reset = st.columns(2)
        with col_buy:
            place = st.button(f"{'🟢 BUY' if order_type == 'BUY' else '🔴 SELL'}",
                               use_container_width=True, type="primary")
        with col_reset:
            reset = st.button("🔄 Reset Portfolio", use_container_width=True)

        if reset:
            st.session_state["pt_portfolio"] = {
                "cash": 500000.0,
                "positions": {},
                "orders": [],
                "pnl_history": [{"time": datetime.now().strftime("%H:%M:%S"), "pnl": 0.0, "equity": 500000.0}],
            }
            st.session_state["pt_log"] = []
            st.rerun()

        if place and ltp > 0:
            fill_price = limit_price if order_price_type == "Limit" else ltp
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if order_type == "BUY":
                cost = qty * fill_price
                if cost > pt["cash"]:
                    st.error(f"Insufficient cash! Need ₹{cost:,.2f}, have ₹{pt['cash']:,.2f}")
                else:
                    pt["cash"] -= cost
                    if symbol_name in pt["positions"]:
                        pos = pt["positions"][symbol_name]
                        total_qty = pos["qty"] + qty
                        avg = (pos["avg_price"] * pos["qty"] + fill_price * qty) / total_qty
                        pt["positions"][symbol_name] = {"ticker": ticker, "qty": total_qty, "avg_price": avg}
                    else:
                        pt["positions"][symbol_name] = {"ticker": ticker, "qty": qty, "avg_price": fill_price}
                    pt["orders"].append({"time": now, "type": "BUY", "symbol": symbol_name,
                                         "qty": qty, "price": fill_price, "value": cost, "status": "FILLED"})
                    st.session_state["pt_log"].append(f"[{now}] BUY {qty} {symbol_name} @ ₹{fill_price:,.2f}")
                    st.success(f"✅ BUY order filled: {qty} × {symbol_name} @ ₹{fill_price:,.2f}")
                    st.rerun()

            elif order_type == "SELL":
                if symbol_name not in pt["positions"] or pt["positions"][symbol_name]["qty"] < qty:
                    st.error("Insufficient holdings to sell!")
                else:
                    pos = pt["positions"][symbol_name]
                    proceeds = qty * fill_price
                    realized_pnl = (fill_price - pos["avg_price"]) * qty
                    pt["cash"] += proceeds
                    if pos["qty"] == qty:
                        del pt["positions"][symbol_name]
                    else:
                        pt["positions"][symbol_name]["qty"] -= qty
                    pt["orders"].append({"time": now, "type": "SELL", "symbol": symbol_name,
                                         "qty": qty, "price": fill_price, "value": proceeds,
                                         "realized_pnl": realized_pnl, "status": "FILLED"})
                    st.session_state["pt_log"].append(
                        f"[{now}] SELL {qty} {symbol_name} @ ₹{fill_price:,.2f} | P&L: ₹{realized_pnl:+,.0f}")
                    color = "✅" if realized_pnl >= 0 else "❌"
                    st.success(f"{color} SELL order filled: {qty} × {symbol_name} @ ₹{fill_price:,.2f} | P&L: ₹{realized_pnl:+,.0f}")
                    st.rerun()

    with col_positions:
        st.subheader("Open Positions")
        if position_data:
            pos_df = pd.DataFrame(position_data)

            def pnl_color(val):
                if "▲" in str(val):
                    return "color: #00ff88; font-weight: bold"
                elif "▼" in str(val):
                    return "color: #ff4444; font-weight: bold"
                return ""

            styled_pos = pos_df.drop(columns=["_pnl"]).style.applymap(
                pnl_color, subset=["Unrealized P&L", "P&L %"])
            st.dataframe(styled_pos, use_container_width=True, hide_index=True)

            # Positions pie chart
            if len(position_data) > 0:
                pvals = [p["_pnl"] + float(p["Market Value"].replace("₹", "").replace(",", ""))
                         for p in position_data]
                fig_pie = go.Figure(go.Pie(
                    labels=[p["Symbol"] for p in position_data],
                    values=[float(p["Market Value"].replace("₹", "").replace(",", ""))
                            for p in position_data],
                    hole=0.4,
                    textfont=dict(color="white"),
                ))
                fig_pie.update_layout(
                    height=250, template="plotly_dark",
                    paper_bgcolor="#0d1117",
                    margin=dict(l=0, r=0, t=10, b=0),
                    title=dict(text="Portfolio Allocation", font=dict(color="#8b949e", size=13)),
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No open positions. Place a BUY order to start paper trading.")

    st.divider()
    st.subheader("Order History")
    if pt["orders"]:
        ord_df = pd.DataFrame(pt["orders"])
        ord_df["price"] = ord_df["price"].apply(lambda x: f"₹{x:,.2f}")
        ord_df["value"] = ord_df["value"].apply(lambda x: f"₹{x:,.2f}")
        if "realized_pnl" in ord_df.columns:
            ord_df["realized_pnl"] = ord_df["realized_pnl"].fillna(0).apply(
                lambda x: f"₹{x:+,.0f}" if x != 0 else "—")

        def type_color(val):
            if val == "BUY":
                return "color: #00ff88; font-weight: bold"
            elif val == "SELL":
                return "color: #ff4444; font-weight: bold"
            return ""

        styled_ord = ord_df.style.applymap(type_color, subset=["type"])
        st.dataframe(styled_ord, use_container_width=True, hide_index=True)
    else:
        st.info("No orders yet.")

    st.divider()
    st.subheader("Activity Log")
    if st.session_state["pt_log"]:
        log_text = "\n".join(reversed(st.session_state["pt_log"][-20:]))
        st.code(log_text, language=None)
    else:
        st.info("No activity yet.")

    # Risk controls info
    st.divider()
    st.subheader("⚡ Risk Controls (SEBI-Compliant)")
    r_cols = st.columns(3)
    with r_cols[0]:
        st.markdown(f"""
        <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:12px;">
            <div style="color:#8b949e; font-size:12px;">Daily Max-Loss Kill Switch</div>
            <div style="color:#ffa500; font-size:16px; font-weight:bold; margin-top:4px;">5% of Capital</div>
            <div style="color:#8b949e; font-size:11px; margin-top:4px;">= ₹{initial_capital * 0.05:,.0f} | Used: ₹{abs(min(total_pnl, 0)):,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with r_cols[1]:
        st.markdown(f"""
        <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:12px;">
            <div style="color:#8b949e; font-size:12px;">Max Positions</div>
            <div style="color:#38bdf8; font-size:16px; font-weight:bold; margin-top:4px;">{len(positions)} / 10</div>
            <div style="color:#8b949e; font-size:11px; margin-top:4px;">Open positions vs limit</div>
        </div>
        """, unsafe_allow_html=True)
    with r_cols[2]:
        st.markdown("""
        <div style="background:#161b22; border: 1px solid #30363d; border-radius:8px; padding:12px;">
            <div style="color:#8b949e; font-size:12px;">Auth Mode</div>
            <div style="color:#00ff88; font-size:16px; font-weight:bold; margin-top:4px;">Manual Confirm</div>
            <div style="color:#8b949e; font-size:11px; margin-top:4px;">Full-auto: OFF | SEBI requirement: 2FA</div>
        </div>
        """, unsafe_allow_html=True)
