import { useState, useEffect, useRef, useCallback } from 'react';
import { createChart } from 'lightweight-charts';
import Disclaimer from '../components/Disclaimer';

const ALL_SYMBOLS = {
  'Nifty 50': '^NSEI', 'Sensex': '^BSESN', 'Bank Nifty': '^NSEBANK',
  'Nifty IT': '^CNXIT', 'Nifty Pharma': '^CNXPHARMA', 'Midcap 100': '^NSEMDCP100',
  'Reliance': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'HDFC Bank': 'HDFCBANK.NS',
  'Infosys': 'INFY.NS', 'ICICI Bank': 'ICICIBANK.NS', 'HUL': 'HINDUNILVR.NS',
  'ITC': 'ITC.NS', 'Kotak': 'KOTAKBANK.NS', 'L&T': 'LT.NS', 'Axis Bank': 'AXISBANK.NS',
  'Bharti Airtel': 'BHARTIARTL.NS', 'Wipro': 'WIPRO.NS', 'HCL Tech': 'HCLTECH.NS',
  'Asian Paints': 'ASIANPAINT.NS', 'Bajaj Finance': 'BAJFINANCE.NS',
  'Maruti': 'MARUTI.NS', 'Sun Pharma': 'SUNPHARMA.NS', 'Titan': 'TITAN.NS',
};

const TIMEFRAMES = [
  { label: '1m', interval: '1m', period: '5d' },
  { label: '5m', interval: '5m', period: '5d' },
  { label: '15m', interval: '15m', period: '10d' },
  { label: '1H', interval: '1h', period: '60d' },
  { label: '1D', interval: '1d', period: '1y' },
  { label: '1W', interval: '1wk', period: '5y' },
];

const BASE_CHART_OPTS = {
  layout: { background: { color: '#0d1117' }, textColor: '#8b949e' },
  grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
  rightPriceScale: { borderColor: '#30363d' },
  timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
  crosshair: { mode: 1 },
  handleScroll: true,
  handleScale: true,
};

function useChart(ref, height, extraOpts = {}) {
  const chartRef = useRef(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      ...BASE_CHART_OPTS, ...extraOpts,
      width: ref.current.clientWidth, height,
    });
    chartRef.current = chart;
    const ro = new ResizeObserver(entries => {
      if (chartRef.current && entries[0]) {
        chartRef.current.applyOptions({ width: entries[0].contentRect.width });
      }
    });
    ro.observe(ref.current);
    return () => { ro.disconnect(); chart.remove(); chartRef.current = null; };
  }, []);
  return chartRef;
}

export default function Charts() {
  const [symbol, setSymbol] = useState('Nifty 50');
  const [tf, setTf] = useState(TIMEFRAMES[4]);
  const [indicators, setIndicators] = useState({
    sma20: true, sma50: false, ema20: false, bb: false,
    vwap: false, supertrend: false, rsi: true, macd: false,
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Chart containers
  const priceRef = useRef(null);
  const volRef = useRef(null);
  const rsiRef = useRef(null);
  const macdRef = useRef(null);

  const priceChart = useChart(priceRef, 380);
  const volChart = useChart(volRef, 90, { rightPriceScale: { borderColor: '#30363d', scaleMargins: { top: 0.1, bottom: 0.1 } } });
  const rsiChart = useChart(rsiRef, 100);
  const macdChart = useChart(macdRef, 100);

  // Sync time scales
  useEffect(() => {
    const charts = [priceChart, volChart, rsiChart, macdChart].map(r => r.current).filter(Boolean);
    if (charts.length < 2) return;
    const handlers = charts.map((src, i) => {
      const handler = range => {
        if (!range) return;
        charts.forEach((dst, j) => { if (i !== j && dst) dst.timeScale().setVisibleLogicalRange(range); });
      };
      src.timeScale().subscribeVisibleLogicalRangeChange(handler);
      return { src, handler };
    });
    return () => handlers.forEach(({ src, handler }) => src.timeScale().unsubscribeVisibleLogicalRangeChange(handler));
  }, [data]);

  // Apply chart data
  useEffect(() => {
    if (!data || !priceChart.current) return;

    // Clear all series
    [priceChart, volChart, rsiChart, macdChart].forEach(cr => {
      if (cr.current) {
        try { cr.current.removeSeries && null; } catch (e) {}
      }
    });

    const pc = priceChart.current;
    const vc = volChart.current;

    // Candles
    if (data.candles?.length) {
      const cs = pc.addCandlestickSeries({
        upColor: '#00ff88', downColor: '#ff4444',
        borderUpColor: '#00ff88', borderDownColor: '#ff4444',
        wickUpColor: '#00ff88', wickDownColor: '#ff4444',
      });
      cs.setData(data.candles);

      // Overlays
      const ind = data.indicators || {};
      if (indicators.sma20 && ind.sma20?.length) {
        const s = pc.addLineSeries({ color: '#ffa500', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
        s.setData(ind.sma20);
      }
      if (indicators.sma50 && ind.sma50?.length) {
        const s = pc.addLineSeries({ color: '#a78bfa', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
        s.setData(ind.sma50);
      }
      if (indicators.ema20 && ind.ema20?.length) {
        const s = pc.addLineSeries({ color: '#38bdf8', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
        s.setData(ind.ema20);
      }
      if (indicators.vwap && ind.vwap?.length) {
        const s = pc.addLineSeries({ color: '#fb923c', lineWidth: 1.5, lineStyle: 1, priceLineVisible: false, lastValueVisible: false });
        s.setData(ind.vwap);
      }
      if (indicators.bb) {
        if (ind.bb_upper?.length) {
          const u = pc.addLineSeries({ color: '#64748b', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });
          u.setData(ind.bb_upper);
        }
        if (ind.bb_mid?.length) {
          const m = pc.addLineSeries({ color: '#475569', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });
          m.setData(ind.bb_mid);
        }
        if (ind.bb_lower?.length) {
          const l = pc.addLineSeries({ color: '#64748b', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });
          l.setData(ind.bb_lower);
        }
      }
      if (indicators.supertrend && ind.supertrend?.length) {
        const s = pc.addLineSeries({ color: '#00ff88', lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
        s.setData(ind.supertrend);
      }

      pc.timeScale().fitContent();
    }

    // Volume
    if (vc && data.volume?.length) {
      const vs = vc.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' });
      vc.priceScale('').applyOptions({ scaleMargins: { top: 0.1, bottom: 0 } });
      vs.setData(data.volume);
      vc.timeScale().fitContent();
    }

    // RSI
    if (indicators.rsi && rsiChart.current && data.indicators?.rsi?.length) {
      const rc = rsiChart.current;
      const rs = rc.addLineSeries({ color: '#38bdf8', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: true });
      rs.setData(data.indicators.rsi);
      rc.addLineSeries({ color: '#ff4444', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false }).setData(
        data.indicators.rsi.map(p => ({ ...p, value: 70 }))
      );
      rc.addLineSeries({ color: '#00ff88', lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false }).setData(
        data.indicators.rsi.map(p => ({ ...p, value: 30 }))
      );
      rc.priceScale('right').applyOptions({ scaleMargins: { top: 0.1, bottom: 0.1 } });
      rc.timeScale().fitContent();
    }

    // MACD
    if (indicators.macd && macdChart.current && data.indicators?.macd?.length) {
      const mc = macdChart.current;
      const ms = mc.addLineSeries({ color: '#38bdf8', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
      ms.setData(data.indicators.macd);
      if (data.indicators.macd_signal?.length) {
        const sig = mc.addLineSeries({ color: '#ffa500', lineWidth: 1.5, priceLineVisible: false, lastValueVisible: false });
        sig.setData(data.indicators.macd_signal);
      }
      if (data.indicators.macd_hist?.length) {
        const hist = mc.addHistogramSeries({ priceLineVisible: false, lastValueVisible: false });
        hist.setData(data.indicators.macd_hist.map(p => ({
          ...p, color: p.value >= 0 ? '#00ff8866' : '#ff444466',
        })));
      }
      mc.timeScale().fitContent();
    }
  }, [data, indicators]);

  const loadChart = useCallback(async () => {
    const ticker = ALL_SYMBOLS[symbol];
    if (!ticker) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const url = `/api/ohlcv/${encodeURIComponent(ticker)}?interval=${tf.interval}&period=${tf.period}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('No data available');
      setData(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [symbol, tf]);

  useEffect(() => { loadChart(); }, [loadChart]);

  const toggleInd = key => setIndicators(prev => ({ ...prev, [key]: !prev[key] }));
  const stats = data?.stats;

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-1 h-6 bg-accent rounded block" />
        <h1 className="text-xl font-bold text-primary">Charts & Technical Indicators</h1>
      </div>

      <Disclaimer text="Technical indicators are computational tools for analysis only. They do not predict future prices." />

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <select
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          className="bg-surface border border-border text-primary text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-accent"
        >
          {Object.keys(ALL_SYMBOLS).map(s => <option key={s}>{s}</option>)}
        </select>

        <div className="flex rounded-lg overflow-hidden border border-border">
          {TIMEFRAMES.map(t => (
            <button
              key={t.label}
              onClick={() => setTf(t)}
              className={`px-3 py-1.5 text-xs font-semibold transition-colors ${tf.label === t.label ? 'bg-accent text-bg' : 'bg-surface text-muted hover:text-primary'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <button
          onClick={loadChart}
          disabled={loading}
          className="px-3 py-1.5 bg-accent/10 border border-accent/30 text-accent rounded-lg text-xs font-semibold hover:bg-accent/20 transition-colors disabled:opacity-50"
        >
          {loading ? <span className="spin inline-block">↻</span> : '↻'} Reload
        </button>
      </div>

      {/* Indicator toggles */}
      <div className="flex flex-wrap gap-2 mb-4">
        {[
          ['sma20', 'SMA 20', '#ffa500'], ['sma50', 'SMA 50', '#a78bfa'],
          ['ema20', 'EMA 20', '#38bdf8'], ['bb', 'Bollinger Bands', '#64748b'],
          ['vwap', 'VWAP', '#fb923c'], ['supertrend', 'Supertrend', '#00ff88'],
          ['rsi', 'RSI', '#38bdf8'], ['macd', 'MACD', '#ffa500'],
        ].map(([key, label, color]) => (
          <button
            key={key}
            onClick={() => toggleInd(key)}
            className={`px-3 py-1 text-xs rounded-full border transition-all ${indicators[key]
              ? 'border-current text-white font-semibold'
              : 'border-border text-muted hover:text-primary'
            }`}
            style={indicators[key] ? { borderColor: color, color, background: `${color}22` } : {}}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Charts */}
      {loading && (
        <div className="flex items-center justify-center h-96 text-muted">
          <span className="spin inline-block mr-2">↻</span> Loading chart data…
        </div>
      )}
      {error && (
        <div className="bg-bear/10 border border-bear/30 rounded-lg p-4 text-bear text-sm mb-4">
          {error} — Markets may be closed or data unavailable.
        </div>
      )}

      {!loading && !error && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden mb-4">
          {/* Symbol header */}
          <div className="px-4 py-2 border-b border-border flex items-center justify-between">
            <span className="text-sm font-semibold text-primary">{symbol} — {tf.label}</span>
            {stats && (
              <span className={`text-sm font-bold ${stats.change >= 0 ? 'text-bull' : 'text-bear'}`}>
                ₹{stats.last_close.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                <span className="text-xs ml-2">
                  {stats.change >= 0 ? '▲' : '▼'} {Math.abs(stats.change_pct).toFixed(2)}%
                </span>
              </span>
            )}
          </div>
          {/* Price chart */}
          <div ref={priceRef} className="w-full" />
          {/* Volume chart */}
          <div className="border-t border-border/40">
            <div className="px-3 pt-1 text-[10px] text-muted">VOLUME</div>
            <div ref={volRef} className="w-full" />
          </div>
          {/* RSI chart */}
          {indicators.rsi && (
            <div className="border-t border-border/40">
              <div className="px-3 pt-1 text-[10px] text-muted">RSI (14)</div>
              <div ref={rsiRef} className="w-full" />
            </div>
          )}
          {/* MACD chart */}
          {indicators.macd && (
            <div className="border-t border-border/40">
              <div className="px-3 pt-1 text-[10px] text-muted">MACD (12, 26, 9)</div>
              <div ref={macdRef} className="w-full" />
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-6 gap-3">
          {[
            { label: 'Last Close', value: `₹${stats.last_close.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, color: stats.change >= 0 ? 'text-bull' : 'text-bear' },
            { label: 'Period High', value: `₹${stats.period_high.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, color: 'text-primary' },
            { label: 'Period Low', value: `₹${stats.period_low.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`, color: 'text-primary' },
            { label: 'RSI (14)', value: stats.rsi != null ? stats.rsi.toFixed(1) : '—', color: stats.rsi > 70 ? 'text-bear' : stats.rsi < 30 ? 'text-bull' : 'text-accent' },
            { label: 'ATR (14)', value: stats.atr != null ? `₹${stats.atr.toFixed(2)}` : '—', color: 'text-primary' },
            { label: 'Avg Volume', value: Math.round(stats.avg_volume).toLocaleString('en-IN'), color: 'text-muted' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-surface border border-border rounded-lg p-3">
              <div className="text-xs text-muted mb-1">{label}</div>
              <div className={`text-sm font-bold font-mono ${color}`}>{value}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
