import { useState } from 'react';
import Disclaimer from '../components/Disclaimer';

const INDICATORS = ['RSI', 'MACD', 'SMA 20', 'SMA 50', 'EMA 20', 'VWAP', 'Supertrend', 'Close Price'];
const CONDITIONS = ['<', '>', '<=', '>=', 'crosses above', 'crosses below'];
const ACTIONS = ['BUY', 'SELL'];

const MOCK_RESULTS = {
  total_return: 18.7,
  cagr: 12.3,
  sharpe: 1.42,
  max_drawdown: -8.4,
  win_rate: 57.3,
  total_trades: 42,
  avg_win: 2.1,
  avg_loss: -1.3,
  equity_curve: Array.from({ length: 52 }, (_, i) => ({
    week: i + 1,
    equity: 100000 * Math.pow(1 + 0.003 + Math.sin(i * 0.5) * 0.01, i),
  })),
};

export default function Strategy() {
  const [rules, setRules] = useState([
    { id: 1, indicator: 'RSI', condition: '<', value: '30', action: 'BUY' },
  ]);
  const [backtestConfig, setBacktestConfig] = useState({
    symbol: 'Nifty 50', startDate: '2023-01-01', endDate: '2024-01-01',
    capital: 100000, interval: '1d',
  });
  const [showResults, setShowResults] = useState(false);
  const [running, setRunning] = useState(false);

  const addRule = () => setRules(prev => [
    ...prev,
    { id: Date.now(), indicator: 'SMA 20', condition: 'crosses above', value: 'SMA 50', action: 'BUY' },
  ]);
  const removeRule = id => setRules(prev => prev.filter(r => r.id !== id));
  const updateRule = (id, field, value) => setRules(prev => prev.map(r => r.id === id ? { ...r, [field]: value } : r));

  const runBacktest = () => {
    setRunning(true);
    setShowResults(false);
    setTimeout(() => { setRunning(false); setShowResults(true); }, 2000);
  };

  const metricColor = v => v > 0 ? 'text-bull' : v < 0 ? 'text-bear' : 'text-primary';

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1 h-6 bg-orange rounded block" />
        <h1 className="text-xl font-bold text-primary">Strategy Builder & Backtesting</h1>
      </div>

      <Disclaimer text="Backtests use historical data. Past backtest performance does NOT guarantee future results. Always paper-trade before going live." />

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Rule Builder */}
        <div>
          <div className="bg-surface border border-border rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-primary">Strategy Rules</h2>
              <button
                onClick={addRule}
                className="text-xs px-3 py-1 bg-bull/10 border border-bull/30 text-bull rounded-lg hover:bg-bull/20 transition-colors"
              >
                + Add Rule
              </button>
            </div>

            <div className="space-y-3">
              {rules.map((rule, idx) => (
                <div key={rule.id} className="bg-bg border border-border rounded-lg p-3">
                  <div className="flex items-center gap-1 mb-2">
                    <span className="text-xs text-muted font-semibold">RULE {idx + 1}</span>
                    <button onClick={() => removeRule(rule.id)} className="ml-auto text-muted hover:text-bear text-xs">✕</button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <div>
                      <label className="text-[10px] text-muted block mb-1">IF</label>
                      <select
                        value={rule.indicator}
                        onChange={e => updateRule(rule.id, 'indicator', e.target.value)}
                        className="w-full bg-surface border border-border text-primary text-xs rounded px-2 py-1 focus:outline-none"
                      >
                        {INDICATORS.map(i => <option key={i}>{i}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted block mb-1">CONDITION</label>
                      <select
                        value={rule.condition}
                        onChange={e => updateRule(rule.id, 'condition', e.target.value)}
                        className="w-full bg-surface border border-border text-primary text-xs rounded px-2 py-1 focus:outline-none"
                      >
                        {CONDITIONS.map(c => <option key={c}>{c}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] text-muted block mb-1">VALUE</label>
                      <input
                        value={rule.value}
                        onChange={e => updateRule(rule.id, 'value', e.target.value)}
                        className="w-full bg-surface border border-border text-primary text-xs rounded px-2 py-1 focus:outline-none focus:border-accent"
                        placeholder="30"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted block mb-1">THEN</label>
                      <select
                        value={rule.action}
                        onChange={e => updateRule(rule.id, 'action', e.target.value)}
                        className={`w-full bg-surface border border-border text-xs rounded px-2 py-1 focus:outline-none font-bold ${rule.action === 'BUY' ? 'text-bull' : 'text-bear'}`}
                      >
                        {ACTIONS.map(a => <option key={a}>{a}</option>)}
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {rules.length === 0 && (
              <div className="text-center py-6 text-muted text-sm">
                Click "Add Rule" to build your strategy
              </div>
            )}
          </div>

          {/* Strategy summary */}
          <div className="bg-surface border border-border rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-primary mb-2">Strategy Logic</h3>
            <div className="space-y-1">
              {rules.map((rule, i) => (
                <div key={rule.id} className="text-xs bg-bg rounded p-2 font-mono">
                  <span className="text-muted">IF </span>
                  <span className="text-accent">{rule.indicator}</span>
                  <span className="text-muted"> {rule.condition} </span>
                  <span className="text-orange">{rule.value}</span>
                  <span className="text-muted"> → </span>
                  <span className={rule.action === 'BUY' ? 'text-bull font-bold' : 'text-bear font-bold'}>{rule.action}</span>
                </div>
              ))}
              {rules.length === 0 && <span className="text-xs text-muted italic">No rules defined</span>}
            </div>
          </div>
        </div>

        {/* Right: Backtest config */}
        <div>
          <div className="bg-surface border border-border rounded-lg p-4 mb-4">
            <h2 className="text-sm font-semibold text-primary mb-4">Backtest Configuration</h2>
            <div className="space-y-3">
              {[
                { label: 'Symbol', key: 'symbol', type: 'text' },
                { label: 'Start Date', key: 'startDate', type: 'date' },
                { label: 'End Date', key: 'endDate', type: 'date' },
                { label: 'Initial Capital (₹)', key: 'capital', type: 'number' },
              ].map(({ label, key, type }) => (
                <div key={key}>
                  <label className="text-xs text-muted block mb-1">{label}</label>
                  <input
                    type={type}
                    value={backtestConfig[key]}
                    onChange={e => setBacktestConfig(prev => ({ ...prev, [key]: e.target.value }))}
                    className="w-full bg-bg border border-border text-primary text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
                  />
                </div>
              ))}
              <div>
                <label className="text-xs text-muted block mb-1">Timeframe</label>
                <select
                  value={backtestConfig.interval}
                  onChange={e => setBacktestConfig(prev => ({ ...prev, interval: e.target.value }))}
                  className="w-full bg-bg border border-border text-primary text-sm rounded-lg px-3 py-2 focus:outline-none"
                >
                  {['1m', '5m', '15m', '1h', '1d', '1wk'].map(i => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
            </div>

            <button
              onClick={runBacktest}
              disabled={running || rules.length === 0}
              className="w-full mt-4 py-2.5 bg-accent text-bg font-bold text-sm rounded-lg hover:bg-accent/90 disabled:opacity-50 transition-colors"
            >
              {running ? <><span className="spin inline-block mr-2">↻</span>Running Backtest…</> : '▶ Run Backtest'}
            </button>
          </div>

          {/* Results */}
          {showResults && (
            <div className="bg-surface border border-border rounded-lg p-4 fade-in">
              <h2 className="text-sm font-semibold text-primary mb-4">📊 Backtest Results</h2>

              <div className="grid grid-cols-2 gap-3 mb-4">
                {[
                  { label: 'Total Return', value: `+${MOCK_RESULTS.total_return}%`, positive: true },
                  { label: 'CAGR', value: `+${MOCK_RESULTS.cagr}%`, positive: true },
                  { label: 'Sharpe Ratio', value: MOCK_RESULTS.sharpe.toFixed(2), positive: true },
                  { label: 'Max Drawdown', value: `${MOCK_RESULTS.max_drawdown}%`, positive: false },
                  { label: 'Win Rate', value: `${MOCK_RESULTS.win_rate}%`, positive: true },
                  { label: 'Total Trades', value: MOCK_RESULTS.total_trades, positive: null },
                ].map(({ label, value, positive }) => (
                  <div key={label} className="bg-bg border border-border rounded-lg p-3">
                    <div className="text-xs text-muted mb-1">{label}</div>
                    <div className={`text-base font-bold ${positive === true ? 'text-bull' : positive === false ? 'text-bear' : 'text-primary'}`}>
                      {value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Equity curve (ASCII-style bars) */}
              <div className="bg-bg border border-border rounded-lg p-3">
                <div className="text-xs text-muted mb-2">Equity Curve (simulated)</div>
                <div className="flex items-end gap-px h-20">
                  {MOCK_RESULTS.equity_curve.map((p, i) => {
                    const maxEq = Math.max(...MOCK_RESULTS.equity_curve.map(x => x.equity));
                    const minEq = Math.min(...MOCK_RESULTS.equity_curve.map(x => x.equity));
                    const pct = ((p.equity - minEq) / (maxEq - minEq)) * 100;
                    const isUp = i === 0 || p.equity >= MOCK_RESULTS.equity_curve[i - 1].equity;
                    return (
                      <div
                        key={i}
                        className="flex-1 rounded-sm"
                        style={{ height: `${Math.max(pct, 5)}%`, background: isUp ? '#00ff8888' : '#ff444488' }}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between text-[10px] text-muted mt-1">
                  <span>₹{(100000).toLocaleString('en-IN')}</span>
                  <span>₹{Math.round(100000 * (1 + MOCK_RESULTS.total_return / 100)).toLocaleString('en-IN')}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
