const symbolSelect = document.getElementById('symbolSelect');
const timeframeSelect = document.getElementById('timeframeSelect');
const candlesChart = document.getElementById('candlesChart');
const marketMeta = document.getElementById('marketMeta');
const orderbookMeta = document.getElementById('orderbookMeta');
const bidsEl = document.getElementById('bids');
const asksEl = document.getElementById('asks');
const historyEl = document.getElementById('history');
const statsEl = document.getElementById('stats');

function candlePattern(c) {
  const body = Math.abs(c.close - c.open);
  const range = c.high - c.low || 1;
  const upWick = c.high - Math.max(c.open, c.close);
  const lowWick = Math.min(c.open, c.close) - c.low;
  if (body / range < 0.12) return 'Doji';
  if (lowWick > body * 2 && upWick < body) return 'Hammer';
  if (upWick > body * 2 && lowWick < body) return 'Shooting Star';
  return 'Normal';
}

function render(snapshot, history, stats) {
  if (!snapshot) return;
  const candles = snapshot.candles || [];
  const x = candles.map(c => c.timestamp);
  const o = candles.map(c => c.open);
  const h = candles.map(c => c.high);
  const l = candles.map(c => c.low);
  const c = candles.map(c => c.close);

  const latest = candles[candles.length - 1] || { open: 0, close: 0, high: 0, low: 0 };
  const pattern = candlePattern(latest);

  const markerHistory = (history || []).filter(s => s.confidence >= 90).map(s => ({
    x: s.created_at,
    y: s.entry,
    text: `${s.direction} ${s.confidence.toFixed(1)}%`,
    symbol: s.direction === 'LONG' ? 'arrow-up' : 'arrow-down',
    color: s.direction === 'LONG' ? '#22c55e' : '#ef4444'
  }));

  Plotly.newPlot(candlesChart, [
    { x, open: o, high: h, low: l, close: c, type: 'candlestick', name: snapshot.symbol },
    {
      x: markerHistory.map(m => m.x),
      y: markerHistory.map(m => m.y),
      text: markerHistory.map(m => m.text),
      mode: 'markers+text',
      textposition: 'top center',
      marker: {
        size: 16,
        symbol: markerHistory.map(m => m.symbol),
        color: markerHistory.map(m => m.color)
      },
      name: '90%+ Signals'
    }
  ], {
    paper_bgcolor: '#111b2e',
    plot_bgcolor: '#111b2e',
    font: { color: '#e6eefc' },
    xaxis: { rangeslider: { visible: false } },
    margin: { t: 20, r: 10, l: 40, b: 30 }
  }, { displayModeBar: true, responsive: true });

  marketMeta.innerHTML = [
    `Price: <b>${snapshot.price.toFixed(2)}</b>`,
    `Bias: <b>${snapshot.bias}</b>`,
    `RSI: <b>${snapshot.indicators.rsi.toFixed(1)}</b>`,
    `ADX: <b>${snapshot.indicators.adx.toFixed(1)}</b>`,
    `ATR: <b>${snapshot.indicators.atr.toFixed(1)}</b>`,
    `Pattern: <b>${pattern}</b>`,
    `Liquidity High: <b>${snapshot.liquidity.swing_high.toFixed(2)}</b>`,
    `Liquidity Low: <b>${snapshot.liquidity.swing_low.toFixed(2)}</b>`
  ].map(x => `<div>${x}</div>`).join('');

  const ob = snapshot.orderbook || { bids: [], asks: [], spread: 0, imbalance: 0 };
  orderbookMeta.innerHTML = `Spread: <b>${ob.spread.toFixed(4)}</b> | Imbalance: <b>${(ob.imbalance * 100).toFixed(2)}%</b>`;
  bidsEl.innerHTML = (ob.bids || []).slice(0, 12).map(x => `<li>${x[0].toFixed(2)} · ${x[1].toFixed(3)}</li>`).join('');
  asksEl.innerHTML = (ob.asks || []).slice(0, 12).map(x => `<li>${x[0].toFixed(2)} · ${x[1].toFixed(3)}</li>`).join('');

  statsEl.innerHTML = `Signals total: <b>${stats.total_signals}</b> | Last 24h: <b>${stats.signals_last_24h}</b> | Avg conf: <b>${stats.avg_confidence.toFixed(2)}%</b>`;
  historyEl.innerHTML = (history || []).slice(0, 40).map(s =>
    `<li>${s.created_at} | <b>${s.symbol} ${s.direction}</b> entry=${s.entry.toFixed(2)} conf=${s.confidence.toFixed(1)} rr=${s.rr.toFixed(2)}</li>`
  ).join('');
}

async function load() {
  const symbol = symbolSelect.value;
  const res = await fetch(`/api/snapshot?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframeSelect.value)}`);
  const data = await res.json();
  if (!data.ok) return;
  render(data.snapshot, data.history, data.stats);
}

symbolSelect.addEventListener('change', load);
timeframeSelect.addEventListener('change', load);
setInterval(load, (window.APP_CONFIG?.pollSec || 8) * 1000);
load();

const form = document.getElementById('advisorForm');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(form);
  const body = Object.fromEntries(fd.entries());
  const res = await fetch('/advisor', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json();
  document.getElementById('advisorResult').textContent = JSON.stringify(data, null, 2);
});
