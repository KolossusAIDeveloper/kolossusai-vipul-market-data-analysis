import { useState, useEffect, useRef, useCallback } from 'react';
import { createChart } from 'lightweight-charts';
import MetricCard from '../components/MetricCard';
import Disclaimer from '../components/Disclaimer';

const INDICES = {
  'Nifty 50': '^NSEI',
  'Sensex': '^BSESN',
  'Bank Nifty': '^NSEBANK',
  'Nifty IT': '^CNXIT',
  'Nifty Pharma': '^CNXPHARMA',
  'Midcap 100': '^NSEMDCP100',
};

const NSE_STOCKS_LIST = [
  ['Reliance', 'RELIANCE.NS'], ['TCS', 'TCS.NS'], ['HDFC Bank', 'HDFCBANK.NS'],
  ['Infosys', 'INFY.NS'], ['ICICI Bank', 'ICICIBANK.NS'], ['HUL', 'HINDUNILVR.NS'],
  ['ITC', 'ITC.NS'], ['Kotak', 'KOTAKBANK.NS'], ['L&T', 'LT.NS'], ['Axis Bank', 'AXISBANK.NS'],
  ['Bharti Airtel', 'BHARTIARTL.NS'], ['Wipro', 'WIPRO.NS'], ['HCL Tech', 'HCLTECH.NS'],
  ['Asian Paints', 'ASIANPAINT.NS'], ['Bajaj Finance', 'BAJFINANCE.NS'],
  ['Maruti', 'MARUTI.NS'], ['Sun Pharma', 'SUNPHARMA.NS'], ['Titan', 'TITAN.NS'],
  ['UltraTech', 'ULTRACEMCO.NS'], ['NTPC', 'NTPC.NS'],
];

const GLOBAL = {
  'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'Dow Jones': '^DJI', 'FTSE 100': '^FTSE',
  'Nikkei 225': '^N225', 'Hang Seng': '^HSI', 'Crude Oil': 'CL=F', 'Gold': 'GC=F',
  'USD/INR': 'USDINR=X', 'VIX': '^VIX',
};

const CHART_OPTS = {
  layout: { background: { color: '#0d1117' }, textColor: '#8b949e' },
  grid: { vertLines: { color: '#1f2937' }, horzLines: { color: '#1f2937' } },
  rightPriceScale: { borderColor: '#30363d' },
  timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
  crosshair: { mode: 1 },
};

function NiftyChart() {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      ...CHART_OPTS,
      width: containerRef.current.clientWidth,
      height: 320,
    });
    chartRef.current = chart;

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00ff88', downColor: '#ff4444',
      borderUpColor: '#00ff88', borderDownColor: '#ff4444',
      wickUpColor: '#00ff88', wickDownColor: '#ff4444',
    });
    const volSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'vol',
    });
    chart.priceScale('vol').applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } });

    fetch('/api/ohlcv/%5ENSEI?interval=5m&period=5d')
      .then(r => r.json())
      .then(d => {
        if (d.candles?.length) {
          candleSeries.setData(d.candles);
          volSeries.setData(d.volume || []);
          chart.timeScale().fitContent();
          // SMA 20
          if (d.indicators?.sma20?.length) {
            const sma = chart.addLineSeries({ color: '#ffa500', lineWidth: 1, priceLineVisible: false });
            sma.setData(d.indicators.sma20);
          }
        }
      })
      .catch(() => {});

    const ro = new ResizeObserver(entries => {
      if (chartRef.current && entries[0]) {
        chartRef.current.applyOptions({ width: entries[0].contentRect.width });
      }
    });
    ro.observe(containerRef.current);

    return () => { ro.disconnect(); chart.remove(); chartRef.current = null; };
  }, []);

  return <div ref={containerRef} className="w-full rounded-lg overflow-hidden" />;
}

export default function MarketOverview() {
  const [quotes, setQuotes] = useState({});
  const [stockQuotes, setStockQuotes] = useState({});
  const [globalQuotes, setGlobalQuotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const idxTickers = Object.values(INDICES);
      const stkTickers = NSE_STOCKS_LIST.map(([, t]) => t);
      const gblTickers = Object.values(GLOBAL);

      const [idxRes, stkRes, gblRes] = await Promise.all([
        fetch('/api/quotes/batch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tickers: idxTickers }) }),
        fetch('/api/quotes/batch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tickers: stkTickers }) }),
        fetch('/api/quotes/batch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tickers: gblTickers }) }),
      ]);
      const [idxData, stkData, gblData] = await Promise.all([idxRes.json(), stkRes.json(), gblRes.json()]);
      setQuotes(idxData);
      setStockQuotes(stkData);
      setGlobalQuotes(gblData);
      setLastUpdated(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  return (
    <div className="p-6 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-bull rounded block" />
          Market Overview
        </h1>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-muted">
              Updated: {lastUpdated.toLocaleTimeString('en-IN')} IST
            </span>
          )}
          <button
            onClick={fetchAll}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-muted hover:text-primary hover:border-accent transition-colors"
          >
            <span className={loading ? 'spin inline-block' : ''}>↻</span>
            Refresh
          </button>
        </div>
      </div>

      <Disclaimer />

      {/* Index cards */}
      <div className="grid grid-cols-6 gap-3 mb-6">
        {Object.entries(INDICES).map(([name, ticker]) => {
          const d = quotes[ticker];
          const isINR = ticker.includes('NSEI') || ticker.includes('BSESN') || ticker.includes('NSE');
          return (
            <MetricCard
              key={ticker}
              label={name}
              value={d?.price ?? '—'}
              change={d?.change ?? 0}
              changePct={d?.change_pct}
              loading={loading && !d}
              currency={d && isINR ? '₹' : ''}
            />
          );
        })}
      </div>

      {/* Chart + Heatmap */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="col-span-2 bg-surface border border-border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-muted mb-3">Nifty 50 — Intraday (5m)</h2>
          <NiftyChart />
        </div>

        <div className="bg-surface border border-border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-muted mb-3">Market Heatmap</h2>
          <div className="grid grid-cols-3 gap-1.5">
            {NSE_STOCKS_LIST.slice(0, 12).map(([name, ticker]) => {
              const d = stockQuotes[ticker];
              const pct = d?.change_pct ?? 0;
              const intensity = Math.min(Math.abs(pct) / 3, 1);
              const bg = pct > 0
                ? `rgba(0, 255, 136, ${0.15 + intensity * 0.35})`
                : pct < 0
                ? `rgba(255, 68, 68, ${0.15 + intensity * 0.35})`
                : 'rgba(48, 54, 61, 0.5)';
              const textColor = pct > 0 ? '#00ff88' : pct < 0 ? '#ff4444' : '#8b949e';
              return (
                <div
                  key={ticker}
                  className="rounded p-1.5 text-center"
                  style={{ background: bg }}
                >
                  <div className="text-[10px] font-bold text-primary truncate">{name}</div>
                  <div className="text-[10px] font-semibold" style={{ color: textColor }}>
                    {d ? `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%` : '—'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Stocks table */}
      <div className="bg-surface border border-border rounded-lg mb-6">
        <div className="px-4 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-primary">NSE Top Stocks</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border text-muted">
                <th className="text-left px-4 py-2">Stock</th>
                <th className="text-right px-3 py-2">LTP (₹)</th>
                <th className="text-right px-3 py-2">Change</th>
                <th className="text-right px-3 py-2">Change %</th>
                <th className="text-right px-3 py-2">High</th>
                <th className="text-right px-3 py-2">Low</th>
                <th className="text-right px-3 py-2">Volume</th>
              </tr>
            </thead>
            <tbody>
              {NSE_STOCKS_LIST.map(([name, ticker]) => {
                const d = stockQuotes[ticker];
                const isUp = d ? d.change >= 0 : null;
                const color = isUp === true ? 'text-bull' : isUp === false ? 'text-bear' : 'text-muted';
                return (
                  <tr key={ticker} className="border-b border-border/40 hover:bg-bg/50 transition-colors">
                    <td className="px-4 py-2 font-semibold text-primary">{name}</td>
                    <td className="px-3 py-2 text-right font-mono">
                      {d ? `₹${d.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : <span className="text-muted">—</span>}
                    </td>
                    <td className={`px-3 py-2 text-right font-mono ${color}`}>
                      {d ? `${isUp ? '▲' : '▼'} ${Math.abs(d.change).toFixed(2)}` : '—'}
                    </td>
                    <td className={`px-3 py-2 text-right font-mono font-semibold ${color}`}>
                      {d ? `${d.change_pct >= 0 ? '+' : ''}${d.change_pct.toFixed(2)}%` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-muted font-mono">
                      {d ? `₹${d.high.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-muted font-mono">
                      {d ? `₹${d.low.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="px-3 py-2 text-right text-muted font-mono">
                      {d ? d.volume.toLocaleString('en-IN') : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Global cues */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h2 className="text-sm font-semibold text-primary mb-3">Global Cues</h2>
        <div className="grid grid-cols-5 gap-3">
          {Object.entries(GLOBAL).map(([name, ticker]) => {
            const d = globalQuotes[ticker];
            const isUp = d ? d.change >= 0 : null;
            const color = isUp === true ? 'text-bull' : isUp === false ? 'text-bear' : 'text-muted';
            return (
              <div key={ticker} className="bg-bg rounded-lg p-3 border border-border/50">
                <div className="text-xs text-muted mb-1 truncate">{name}</div>
                <div className="text-sm font-bold text-primary font-mono">
                  {d ? d.price.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '—'}
                </div>
                <div className={`text-xs font-semibold ${color}`}>
                  {d ? `${isUp ? '▲' : '▼'} ${Math.abs(d.change_pct).toFixed(2)}%` : '—'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
