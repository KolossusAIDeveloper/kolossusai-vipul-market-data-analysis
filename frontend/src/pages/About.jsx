import Disclaimer from '../components/Disclaimer';

const INDICATORS = [
  ['SMA 20 / 50', 'Simple Moving Average'],
  ['EMA 20', 'Exponential Moving Average'],
  ['Bollinger Bands', 'Volatility bands (2σ)'],
  ['RSI (14)', 'Relative Strength Index'],
  ['MACD', 'Moving Average Convergence/Divergence'],
  ['Stochastic', 'Stochastic Oscillator K/D'],
  ['ATR (14)', 'Average True Range'],
  ['VWAP', 'Volume-Weighted Average Price'],
  ['Supertrend', 'Trend-following indicator'],
  ['Volume', 'Volume bar overlay'],
];

const BROKERS = [
  ['Zerodha', 'Kite Connect', '₹2000/mo'],
  ['Upstox', 'Upstox API', 'Free'],
  ['Angel One', 'SmartAPI', 'Free'],
  ['Fyers', 'Fyers API', 'Free'],
  ['5paisa', '5paisa API', 'Free'],
];

const MODULES = [
  ['📊', 'Market Overview', 'Live quotes, indices, heatmap, global cues', 'Live'],
  ['📈', 'Charts & Indicators', 'Candlestick charts with 10+ technical indicators', 'Live'],
  ['🤖', 'AI Sentiment', 'News sentiment + direction prediction', 'Live'],
  ['⚙️', 'Strategy Builder', 'Visual strategy builder + backtesting engine', 'Live'],
  ['📋', 'Paper Trading', 'Simulated order placement with risk controls', 'Live'],
];

export default function About() {
  return (
    <div className="p-6 fade-in max-w-5xl">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1 h-6 bg-muted rounded block" />
        <h1 className="text-xl font-bold text-primary">About Market Data Analysis</h1>
      </div>

      <Disclaimer text="MANDATORY: This platform is a research and educational tool only. All market predictions, signals, and sentiment scores are probabilistic estimates — not financial advice. Past backtest performance does NOT guarantee future results. You are solely responsible for your trading decisions and SEBI compliance." />

      {/* Modules table */}
      <div className="bg-surface border border-border rounded-lg mb-6">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-primary">Platform Modules</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-xs text-muted">
              <th className="text-left px-4 py-2">Module</th>
              <th className="text-left px-4 py-2">Description</th>
              <th className="text-left px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {MODULES.map(([icon, name, desc, status]) => (
              <tr key={name} className="border-b border-border/40">
                <td className="px-4 py-3 font-semibold text-primary">{icon} {name}</td>
                <td className="px-4 py-3 text-muted text-xs">{desc}</td>
                <td className="px-4 py-3"><span className="text-xs text-bull bg-bull/10 border border-bull/30 px-2 py-0.5 rounded-full">✓ {status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Tech stack */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[
          {
            title: 'Frontend / UI', color: 'text-accent',
            items: ['React 18 + Vite', 'TradingView Lightweight Charts', 'Tailwind CSS (dark theme)', 'Native Fetch API'],
          },
          {
            title: 'Backend / Data', color: 'text-bull',
            items: ['FastAPI (Python, async)', 'yfinance (market data)', 'Financial RSS feeds (news)', 'In-memory TTL caching'],
          },
          {
            title: 'AI / Analytics', color: 'text-purple',
            items: ['Keyword-based sentiment scoring', 'Technical indicator signals', 'RSI, MACD, Supertrend', 'Backtest engine (mock)'],
          },
        ].map(({ title, color, items }) => (
          <div key={title} className="bg-surface border border-border rounded-lg p-4">
            <h3 className={`text-sm font-semibold ${color} mb-3`}>{title}</h3>
            <ul className="space-y-1.5">
              {items.map(item => (
                <li key={item} className="text-xs text-muted flex items-start gap-2">
                  <span className="text-border mt-0.5">•</span> {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Indicators */}
      <div className="bg-surface border border-border rounded-lg p-4 mb-6">
        <h2 className="text-sm font-semibold text-primary mb-3">Available Technical Indicators</h2>
        <div className="grid grid-cols-5 gap-2">
          {INDICATORS.map(([name, desc]) => (
            <div key={name} className="bg-bg border border-border rounded-lg p-2.5">
              <div className="text-xs text-accent font-semibold">{name}</div>
              <div className="text-[10px] text-muted mt-0.5">{desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SEBI Compliance */}
      <div className="bg-surface border border-border rounded-lg p-4 mb-6">
        <h2 className="text-sm font-semibold text-primary mb-3">SEBI Compliance Notes</h2>
        <div className="space-y-2 text-xs text-muted">
          {[
            '🔐 OAuth + 2FA is mandatory for all broker API sessions (effective April 1, 2026)',
            '🌐 Static IP whitelisting is required for automated order placement',
            '🔄 Daily session reset — broker tokens must not persist indefinitely',
            '🏷️ Algo/Strategy ID tagging — all bot-placed orders must carry a broker-issued Algo-ID',
            '⛔ No guaranteed return claims — this platform makes none',
            '👤 Personal use only (< 10 orders/second) does not require separate strategy registration',
          ].map(item => (
            <div key={item} className="flex items-start gap-2 py-1.5 border-b border-border/30 last:border-0">
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Brokers */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h2 className="text-sm font-semibold text-primary mb-3">Broker APIs Supported (via BrokerAdapter pattern)</h2>
        <div className="grid grid-cols-5 gap-3">
          {BROKERS.map(([broker, api, cost]) => (
            <div key={broker} className="bg-bg border border-border rounded-lg p-3 text-center">
              <div className="text-sm font-bold text-primary">{broker}</div>
              <div className="text-xs text-muted mt-0.5">{api}</div>
              <div className="text-xs text-accent font-semibold mt-1">{cost}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
