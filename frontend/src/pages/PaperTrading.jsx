import { useState, useEffect, useCallback } from 'react';
import Disclaimer from '../components/Disclaimer';

const ALL_SYMBOLS = {
  'Nifty 50': '^NSEI', 'Sensex': '^BSESN', 'Bank Nifty': '^NSEBANK',
  'Reliance': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'HDFC Bank': 'HDFCBANK.NS',
  'Infosys': 'INFY.NS', 'ICICI Bank': 'ICICIBANK.NS', 'ITC': 'ITC.NS',
  'Kotak': 'KOTAKBANK.NS', 'L&T': 'LT.NS', 'Axis Bank': 'AXISBANK.NS',
  'Bharti Airtel': 'BHARTIARTL.NS', 'Wipro': 'WIPRO.NS', 'HCL Tech': 'HCLTECH.NS',
  'Asian Paints': 'ASIANPAINT.NS', 'Bajaj Finance': 'BAJFINANCE.NS',
  'Maruti': 'MARUTI.NS', 'Sun Pharma': 'SUNPHARMA.NS', 'Titan': 'TITAN.NS',
};

const INITIAL_CAPITAL = 500000;

const INITIAL_STATE = {
  cash: INITIAL_CAPITAL,
  positions: {},
  orders: [],
};

function loadState() {
  try {
    const s = localStorage.getItem('pt_state');
    return s ? JSON.parse(s) : INITIAL_STATE;
  } catch { return INITIAL_STATE; }
}

function saveState(s) {
  try { localStorage.setItem('pt_state', JSON.stringify(s)); } catch {}
}

export default function PaperTrading() {
  const [state, setState] = useState(loadState);
  const [symbol, setSymbol] = useState('Reliance');
  const [orderType, setOrderType] = useState('BUY');
  const [qty, setQty] = useState(10);
  const [priceType, setPriceType] = useState('Market');
  const [limitPrice, setLimitPrice] = useState('');
  const [quote, setQuote] = useState(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [liveQuotes, setLiveQuotes] = useState({});

  // Save on every state change
  useEffect(() => { saveState(state); }, [state]);

  // Fetch selected symbol quote
  useEffect(() => {
    const ticker = ALL_SYMBOLS[symbol];
    if (!ticker) return;
    setQuoteLoading(true);
    fetch(`/api/quote/${encodeURIComponent(ticker)}`)
      .then(r => r.json())
      .then(d => { setQuote(d); if (priceType === 'Market') setLimitPrice(d.price.toFixed(2)); })
      .catch(() => setQuote(null))
      .finally(() => setQuoteLoading(false));
  }, [symbol]);

  // Fetch live quotes for open positions
  const refreshPositionQuotes = useCallback(async () => {
    const tickers = Object.values(state.positions).map(p => p.ticker);
    if (!tickers.length) return;
    const res = await fetch('/api/quotes/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers }),
    });
    setLiveQuotes(await res.json());
  }, [state.positions]);

  useEffect(() => { refreshPositionQuotes(); }, [refreshPositionQuotes]);

  const placeOrder = () => {
    const ticker = ALL_SYMBOLS[symbol];
    const fillPrice = parseFloat(priceType === 'Limit' ? limitPrice : quote?.price ?? 0);
    if (!fillPrice || fillPrice <= 0) { setMessage({ type: 'error', text: 'Price unavailable.' }); return; }

    const now = new Date().toLocaleString('en-IN');
    setState(prev => {
      const next = { ...prev, positions: { ...prev.positions }, orders: [...prev.orders] };

      if (orderType === 'BUY') {
        const cost = qty * fillPrice;
        if (cost > prev.cash) { setMessage({ type: 'error', text: `Insufficient cash! Need ₹${cost.toFixed(0)}, have ₹${prev.cash.toFixed(0)}` }); return prev; }
        next.cash = prev.cash - cost;
        const existing = prev.positions[symbol];
        if (existing) {
          const totalQty = existing.qty + qty;
          next.positions[symbol] = { ticker, qty: totalQty, avg_price: (existing.avg_price * existing.qty + fillPrice * qty) / totalQty };
        } else {
          next.positions[symbol] = { ticker, qty, avg_price: fillPrice };
        }
        next.orders.push({ time: now, type: 'BUY', symbol, qty, price: fillPrice, value: cost, status: 'FILLED' });
        setMessage({ type: 'success', text: `✅ BUY ${qty} × ${symbol} @ ₹${fillPrice.toFixed(2)}` });
      } else {
        const pos = prev.positions[symbol];
        if (!pos || pos.qty < qty) { setMessage({ type: 'error', text: 'Insufficient holdings!' }); return prev; }
        const proceeds = qty * fillPrice;
        const realizedPnl = (fillPrice - pos.avg_price) * qty;
        next.cash = prev.cash + proceeds;
        if (pos.qty === qty) {
          delete next.positions[symbol];
        } else {
          next.positions[symbol] = { ...pos, qty: pos.qty - qty };
        }
        next.orders.push({ time: now, type: 'SELL', symbol, qty, price: fillPrice, value: proceeds, pnl: realizedPnl, status: 'FILLED' });
        setMessage({ type: realizedPnl >= 0 ? 'success' : 'warning', text: `${realizedPnl >= 0 ? '✅' : '❌'} SELL ${qty} × ${symbol} @ ₹${fillPrice.toFixed(2)} | P&L: ₹${realizedPnl.toFixed(0)}` });
      }
      return next;
    });
    setTimeout(() => setMessage(null), 4000);
  };

  const resetPortfolio = () => {
    setState(INITIAL_STATE);
    setLiveQuotes({});
    setMessage({ type: 'info', text: 'Portfolio reset to ₹5,00,000' });
    setTimeout(() => setMessage(null), 3000);
  };

  // Portfolio calculations
  let totalMktVal = 0;
  const positionRows = Object.entries(state.positions).map(([sym, pos]) => {
    const lq = liveQuotes[pos.ticker];
    const ltp = lq?.price ?? pos.avg_price;
    const mktVal = ltp * pos.qty;
    const cost = pos.avg_price * pos.qty;
    const pnl = mktVal - cost;
    const pnlPct = (pnl / cost) * 100;
    totalMktVal += mktVal;
    return { sym, pos, ltp, mktVal, pnl, pnlPct };
  });

  const totalEquity = state.cash + totalMktVal;
  const totalPnl = totalEquity - INITIAL_CAPITAL;
  const totalPnlPct = (totalPnl / INITIAL_CAPITAL) * 100;
  const dailyLossLimit = INITIAL_CAPITAL * 0.05;
  const killSwitchTriggered = totalPnl < -dailyLossLimit;

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1 h-6 bg-accent rounded block" />
        <h1 className="text-xl font-bold text-primary">Paper Trading Simulator</h1>
        <span className="ml-2 text-xs px-2 py-0.5 bg-orange/10 border border-orange/30 text-orange rounded-full">Simulated Only</span>
      </div>

      <Disclaimer text="Paper Trading Mode — Simulated fills only. No real money at risk. By SEBI's algo framework (April 2026), paper trading is a mandatory staging step before live deployment." />

      {/* Message */}
      {message && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium border fade-in ${
          message.type === 'success' ? 'bg-bull/10 border-bull/30 text-bull' :
          message.type === 'error' ? 'bg-bear/10 border-bear/30 text-bear' :
          message.type === 'warning' ? 'bg-orange/10 border-orange/30 text-orange' :
          'bg-accent/10 border-accent/30 text-accent'
        }`}>
          {message.text}
        </div>
      )}

      {killSwitchTriggered && (
        <div className="mb-4 px-4 py-3 bg-bear/20 border border-bear rounded-lg text-bear font-bold text-sm">
          ⛔ Daily Max-Loss Kill Switch Triggered! (5% loss = ₹{dailyLossLimit.toFixed(0)}) Trading disabled for today. Reset portfolio to continue.
        </div>
      )}

      {/* Portfolio summary */}
      <div className="grid grid-cols-5 gap-3 mb-6">
        {[
          { label: 'Total Equity', value: `₹${totalEquity.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, sub: `${totalPnl >= 0 ? '+' : ''}₹${Math.abs(totalPnl).toFixed(0)} (${totalPnlPct.toFixed(2)}%)`, color: totalPnl >= 0 ? 'text-bull' : 'text-bear' },
          { label: 'Available Cash', value: `₹${state.cash.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, sub: '', color: 'text-primary' },
          { label: 'Market Value', value: `₹${totalMktVal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, sub: '', color: 'text-primary' },
          { label: 'Open Positions', value: Object.keys(state.positions).length, sub: 'of 10 max', color: 'text-accent' },
          { label: 'Total Orders', value: state.orders.length, sub: '', color: 'text-muted' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="bg-surface border border-border rounded-lg p-3">
            <div className="text-xs text-muted mb-1">{label}</div>
            <div className={`text-base font-bold ${color}`}>{value}</div>
            {sub && <div className={`text-xs ${color} opacity-80`}>{sub}</div>}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Order Form */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-primary mb-4">Place Order</h2>

          <div className="flex rounded-lg overflow-hidden border border-border mb-3">
            {['BUY', 'SELL'].map(t => (
              <button
                key={t}
                onClick={() => setOrderType(t)}
                className={`flex-1 py-2 text-sm font-bold transition-colors ${orderType === t
                  ? t === 'BUY' ? 'bg-bull text-bg' : 'bg-bear text-white'
                  : 'text-muted hover:text-primary'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-muted block mb-1">Symbol</label>
              <select
                value={symbol}
                onChange={e => setSymbol(e.target.value)}
                className="w-full bg-bg border border-border text-primary text-sm rounded-lg px-3 py-2 focus:outline-none"
              >
                {Object.keys(ALL_SYMBOLS).map(s => <option key={s}>{s}</option>)}
              </select>
            </div>

            {/* Live quote display */}
            {quote && !quoteLoading ? (
              <div className="bg-bg border border-border rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted">LTP</span>
                  <span className={`text-xs font-semibold ${quote.change >= 0 ? 'text-bull' : 'text-bear'}`}>
                    {quote.change >= 0 ? '▲' : '▼'} {Math.abs(quote.change_pct).toFixed(2)}%
                  </span>
                </div>
                <div className="text-xl font-bold text-primary mt-1">₹{quote.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</div>
              </div>
            ) : quoteLoading ? (
              <div className="bg-bg border border-border rounded-lg p-3 text-muted text-sm"><span className="spin inline-block">↻</span> Loading…</div>
            ) : null}

            <div>
              <label className="text-xs text-muted block mb-1">Quantity</label>
              <input
                type="number"
                value={qty}
                onChange={e => setQty(Math.max(1, parseInt(e.target.value) || 1))}
                min={1}
                className="w-full bg-bg border border-border text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
              />
            </div>

            <div>
              <label className="text-xs text-muted block mb-1">Price Type</label>
              <div className="flex rounded-lg overflow-hidden border border-border">
                {['Market', 'Limit'].map(t => (
                  <button
                    key={t}
                    onClick={() => { setPriceType(t); if (t === 'Market' && quote) setLimitPrice(quote.price.toFixed(2)); }}
                    className={`flex-1 py-1.5 text-xs font-semibold transition-colors ${priceType === t ? 'bg-accent text-bg' : 'text-muted hover:text-primary'}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {priceType === 'Limit' && (
              <div>
                <label className="text-xs text-muted block mb-1">Limit Price (₹)</label>
                <input
                  type="number"
                  value={limitPrice}
                  onChange={e => setLimitPrice(e.target.value)}
                  step="0.05"
                  className="w-full bg-bg border border-border text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
                />
              </div>
            )}

            <div className="bg-bg border border-border rounded-lg p-2 text-xs text-muted">
              Order Value: <span className="text-primary font-semibold">
                ₹{((parseFloat(priceType === 'Limit' ? limitPrice : quote?.price ?? 0) || 0) * qty).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </span>
            </div>

            <button
              onClick={placeOrder}
              disabled={killSwitchTriggered || !quote}
              className={`w-full py-2.5 font-bold text-sm rounded-lg transition-colors disabled:opacity-50 ${
                orderType === 'BUY' ? 'bg-bull text-bg hover:bg-bull/90' : 'bg-bear text-white hover:bg-bear/90'
              }`}
            >
              {orderType === 'BUY' ? '🟢 Place BUY Order' : '🔴 Place SELL Order'}
            </button>

            <button
              onClick={resetPortfolio}
              className="w-full py-2 text-xs text-muted border border-border rounded-lg hover:text-primary hover:border-muted transition-colors"
            >
              🔄 Reset Portfolio
            </button>
          </div>
        </div>

        {/* Positions */}
        <div className="col-span-2 bg-surface border border-border rounded-lg">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-semibold text-primary">Open Positions</h2>
            <button onClick={refreshPositionQuotes} className="text-xs text-muted hover:text-primary">↻ Refresh</button>
          </div>
          {positionRows.length === 0 ? (
            <div className="p-8 text-center text-muted text-sm">
              No open positions. Place a BUY order to start.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted">
                    <th className="text-left px-4 py-2">Symbol</th>
                    <th className="text-right px-3 py-2">Qty</th>
                    <th className="text-right px-3 py-2">Avg Price</th>
                    <th className="text-right px-3 py-2">LTP</th>
                    <th className="text-right px-3 py-2">Mkt Value</th>
                    <th className="text-right px-3 py-2">Unrealized P&L</th>
                    <th className="text-right px-3 py-2">P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {positionRows.map(({ sym, pos, ltp, mktVal, pnl, pnlPct }) => (
                    <tr key={sym} className="border-b border-border/40 hover:bg-bg/50">
                      <td className="px-4 py-2 font-semibold text-primary">{sym}</td>
                      <td className="px-3 py-2 text-right font-mono">{pos.qty}</td>
                      <td className="px-3 py-2 text-right font-mono text-muted">₹{pos.avg_price.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono">₹{ltp.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right font-mono">₹{mktVal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                      <td className={`px-3 py-2 text-right font-mono font-semibold ${pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                        {pnl >= 0 ? '▲' : '▼'} ₹{Math.abs(pnl).toFixed(0)}
                      </td>
                      <td className={`px-3 py-2 text-right font-mono font-semibold ${pnl >= 0 ? 'text-bull' : 'text-bear'}`}>
                        {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Order history */}
      <div className="bg-surface border border-border rounded-lg mb-4">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-primary">Order History ({state.orders.length})</h2>
        </div>
        {state.orders.length === 0 ? (
          <div className="p-6 text-center text-muted text-sm">No orders placed yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border text-muted">
                  <th className="text-left px-4 py-2">Time</th>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Symbol</th>
                  <th className="text-right px-3 py-2">Qty</th>
                  <th className="text-right px-3 py-2">Price</th>
                  <th className="text-right px-3 py-2">Value</th>
                  <th className="text-right px-3 py-2">Realized P&L</th>
                  <th className="text-right px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {[...state.orders].reverse().map((o, i) => (
                  <tr key={i} className="border-b border-border/40 hover:bg-bg/50">
                    <td className="px-4 py-2 text-muted">{o.time}</td>
                    <td className={`px-3 py-2 font-bold ${o.type === 'BUY' ? 'text-bull' : 'text-bear'}`}>{o.type}</td>
                    <td className="px-3 py-2 text-primary font-semibold">{o.symbol}</td>
                    <td className="px-3 py-2 text-right font-mono">{o.qty}</td>
                    <td className="px-3 py-2 text-right font-mono">₹{o.price.toFixed(2)}</td>
                    <td className="px-3 py-2 text-right font-mono">₹{o.value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</td>
                    <td className={`px-3 py-2 text-right font-mono ${o.pnl != null ? (o.pnl >= 0 ? 'text-bull' : 'text-bear') : 'text-muted'}`}>
                      {o.pnl != null ? `${o.pnl >= 0 ? '+' : ''}₹${o.pnl.toFixed(0)}` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right"><span className="text-bull">✓ {o.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Risk controls */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: '⚡ Daily Max-Loss Kill Switch', value: '5% of Capital', sub: `= ₹${dailyLossLimit.toFixed(0)} | Used: ₹${Math.abs(Math.min(totalPnl, 0)).toFixed(0)}`, color: 'text-orange' },
          { label: '📊 Max Positions', value: `${Object.keys(state.positions).length} / 10`, sub: 'Open positions vs limit', color: 'text-accent' },
          { label: '🔒 Auth Mode', value: 'Manual Confirm', sub: 'Full-auto: OFF | SEBI: 2FA required', color: 'text-bull' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="bg-surface border border-border rounded-lg p-3">
            <div className="text-xs text-muted mb-2">{label}</div>
            <div className={`text-sm font-bold ${color}`}>{value}</div>
            <div className="text-xs text-muted mt-1">{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
