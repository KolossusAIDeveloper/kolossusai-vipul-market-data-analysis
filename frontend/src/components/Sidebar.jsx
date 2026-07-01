const NAV = [
  { id: 'overview', icon: '📊', label: 'Market Overview' },
  { id: 'charts', icon: '📈', label: 'Charts & Indicators' },
  { id: 'sentiment', icon: '🤖', label: 'AI Sentiment' },
  { id: 'strategy', icon: '⚙️', label: 'Strategy Builder' },
  { id: 'trading', icon: '📋', label: 'Paper Trading' },
  { id: 'about', icon: 'ℹ️', label: 'About' },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="w-56 flex-shrink-0 bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-2xl">📈</span>
          <div>
            <div className="text-sm font-bold text-primary leading-tight">Market Data</div>
            <div className="text-xs text-muted">AI-Powered</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3">
        {NAV.map(({ id, icon, label }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm transition-all duration-150
              ${activePage === id
                ? 'bg-[#1f2937] text-primary border-l-2 border-bull'
                : 'text-muted hover:text-primary hover:bg-[#1f2937]/50 border-l-2 border-transparent'
              }`}
          >
            <span className="text-base leading-none">{icon}</span>
            <span className="font-medium">{label}</span>
          </button>
        ))}
      </nav>

      {/* Disclaimer */}
      <div className="p-3 border-t border-border">
        <p className="text-[10px] text-muted leading-relaxed">
          ⚠️ All signals are probabilistic research tools, not financial advice. Past performance doesn't guarantee future results.
        </p>
      </div>
    </aside>
  );
}
