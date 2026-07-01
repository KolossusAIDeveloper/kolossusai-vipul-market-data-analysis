import { useState, useEffect } from 'react';
import Disclaimer from '../components/Disclaimer';

const POSITIVE_WORDS = new Set([
  'rally', 'surge', 'gain', 'rise', 'high', 'bull', 'profit', 'growth', 'strong',
  'positive', 'outperform', 'record', 'boost', 'recovery', 'optimism', 'upgrade',
  'buy', 'accumulate', 'upside', 'breakout', 'support',
]);
const NEGATIVE_WORDS = new Set([
  'fall', 'drop', 'decline', 'loss', 'bear', 'weak', 'sell', 'downgrade', 'crash',
  'slump', 'concern', 'risk', 'uncertainty', 'outflow', 'pressure', 'volatility',
  'warning', 'cut', 'negative', 'pullback', 'resistance',
]);

function SentimentBar({ score }) {
  const pct = ((score + 1) / 2) * 100;
  const color = score > 0.1 ? '#00ff88' : score < -0.1 ? '#ff4444' : '#ffa500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-border rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs font-mono w-12 text-right" style={{ color }}>
        {score >= 0 ? '+' : ''}{score.toFixed(2)}
      </span>
    </div>
  );
}

export default function Sentiment() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [prediction, setPrediction] = useState(null);

  useEffect(() => {
    fetch('/api/news')
      .then(r => r.json())
      .then(data => {
        setNews(data);
        // Compute aggregate prediction
        if (data.length > 0) {
          const avgScore = data.reduce((sum, n) => sum + n.score, 0) / data.length;
          const bullCount = data.filter(n => n.score > 0.1).length;
          const bearCount = data.filter(n => n.score < -0.1).length;
          const total = data.length;
          setPrediction({
            score: avgScore,
            direction: avgScore > 0.05 ? 'BULLISH' : avgScore < -0.05 ? 'BEARISH' : 'SIDEWAYS',
            confidence: Math.round(Math.min(Math.abs(avgScore) * 200, 85)),
            bullPct: Math.round((bullCount / total) * 100),
            bearPct: Math.round((bearCount / total) * 100),
            neutralPct: Math.round(((total - bullCount - bearCount) / total) * 100),
          });
        }
      })
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  }, []);

  const dirColor = d => d === 'BULLISH' ? '#00ff88' : d === 'BEARISH' ? '#ff4444' : '#ffa500';
  const sentColor = s => s === 'Bullish' ? 'text-bull' : s === 'Bearish' ? 'text-bear' : 'text-orange';
  const sentBg = s => s === 'Bullish' ? 'bg-bull/10 border-bull/30' : s === 'Bearish' ? 'bg-bear/10 border-bear/30' : 'bg-orange/10 border-orange/30';

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1 h-6 bg-purple rounded block" />
        <h1 className="text-xl font-bold text-primary">AI Sentiment & Market Prediction</h1>
      </div>

      <Disclaimer text="All signals are probabilistic research tools only — not investment advice. Sentiment is derived from news headlines using keyword analysis." />

      {/* Prediction Signal */}
      {prediction && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="col-span-1 bg-surface border border-border rounded-lg p-5 flex flex-col items-center justify-center gap-3">
            <div className="text-xs text-muted uppercase tracking-widest">Market Signal</div>
            <div className="text-4xl font-black" style={{ color: dirColor(prediction.direction) }}>
              {prediction.direction === 'BULLISH' ? '↑' : prediction.direction === 'BEARISH' ? '↓' : '→'}
            </div>
            <div className="text-xl font-bold" style={{ color: dirColor(prediction.direction) }}>
              {prediction.direction}
            </div>
            <div className="text-xs text-muted">
              Confidence: <span className="text-primary font-bold">{prediction.confidence}%</span>
            </div>
            <div className="w-full bg-border rounded-full h-2 mt-1">
              <div className="h-2 rounded-full" style={{ width: `${prediction.confidence}%`, background: dirColor(prediction.direction) }} />
            </div>
          </div>

          <div className="col-span-2 bg-surface border border-border rounded-lg p-5">
            <h3 className="text-sm font-semibold text-muted mb-4">Sentiment Breakdown</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-bull text-sm w-20">🟢 Bullish</span>
                <div className="flex-1 h-3 bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-bull rounded-full" style={{ width: `${prediction.bullPct}%` }} />
                </div>
                <span className="text-bull font-bold text-sm w-12 text-right">{prediction.bullPct}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-orange text-sm w-20">⚪ Neutral</span>
                <div className="flex-1 h-3 bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-orange rounded-full" style={{ width: `${prediction.neutralPct}%` }} />
                </div>
                <span className="text-orange font-bold text-sm w-12 text-right">{prediction.neutralPct}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-bear text-sm w-20">🔴 Bearish</span>
                <div className="flex-1 h-3 bg-border rounded-full overflow-hidden">
                  <div className="h-full bg-bear rounded-full" style={{ width: `${prediction.bearPct}%` }} />
                </div>
                <span className="text-bear font-bold text-sm w-12 text-right">{prediction.bearPct}%</span>
              </div>

              <div className="border-t border-border pt-3 mt-2">
                <div className="text-xs text-muted mb-1">Aggregate Sentiment Score</div>
                <SentimentBar score={prediction.score} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* News Table */}
      <div className="bg-surface border border-border rounded-lg">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <h2 className="text-sm font-semibold text-primary">News Sentiment Analysis</h2>
          <span className="text-xs text-muted">{news.length} articles • Auto-refreshed</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-muted">
            <span className="spin inline-block mr-2">↻</span> Fetching market news…
          </div>
        ) : news.length === 0 ? (
          <div className="p-8 text-center text-muted">
            Unable to fetch news. Check your network connection.
          </div>
        ) : (
          <div className="divide-y divide-border/40">
            {news.map((item, i) => (
              <div key={i} className="px-4 py-3 hover:bg-bg/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <p className="text-sm text-primary leading-snug mb-1">{item.headline}</p>
                    <div className="flex items-center gap-3 text-xs text-muted">
                      <span>📰 {item.source}</span>
                      {item.published && <span>🕐 {item.published.slice(0, 25)}</span>}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0 w-36">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${sentBg(item.sentiment)} ${sentColor(item.sentiment)}`}>
                      {item.sentiment}
                    </span>
                    <SentimentBar score={item.score} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Model info */}
      <div className="mt-4 bg-surface border border-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-primary mb-3">How the Prediction Works</h3>
        <div className="grid grid-cols-3 gap-4 text-xs text-muted">
          <div>
            <div className="text-accent font-semibold mb-1">📰 News Sentiment</div>
            <p>Headlines from financial RSS feeds (Economic Times, Moneycontrol, Business Standard) are scored using positive/negative keyword matching.</p>
          </div>
          <div>
            <div className="text-orange font-semibold mb-1">📊 Technical Signals</div>
            <p>RSI, MACD, Bollinger Bands, Supertrend and other indicators from price data feed into the directional signal.</p>
          </div>
          <div>
            <div className="text-purple font-semibold mb-1">🤖 AI Aggregation</div>
            <p>Signals are combined to produce a probabilistic direction (Bullish / Bearish / Sideways) with a confidence score. This is NOT financial advice.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
