export default function MetricCard({ label, value, change, changePct, loading, currency = '' }) {
  const isPositive = change >= 0;
  const color = isPositive ? 'text-bull' : 'text-bear';
  const arrow = isPositive ? '▲' : '▼';

  return (
    <div className="bg-surface border border-border rounded-lg p-3 flex flex-col gap-1">
      <div className="text-xs text-muted font-medium uppercase tracking-wide truncate">{label}</div>
      {loading ? (
        <div className="h-6 w-20 bg-border rounded animate-pulse mt-1" />
      ) : (
        <>
          <div className="text-lg font-bold text-primary">
            {currency}{typeof value === 'number' ? value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : value}
          </div>
          <div className={`text-xs font-semibold ${color}`}>
            {arrow} {Math.abs(change).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            {changePct !== undefined && ` (${changePct >= 0 ? '+' : ''}${changePct.toFixed(2)}%)`}
          </div>
        </>
      )}
    </div>
  );
}
