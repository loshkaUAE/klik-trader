const symbolSelect = document.getElementById('symbolSelect');
const timeframeSelect = document.getElementById('timeframeSelect');
const candlesChart = document.getElementById('candlesChart');
const marketMeta = document.getElementById('marketMeta');
const orderbookMeta = document.getElementById('orderbookMeta');
const bidsEl = document.getElementById('bids');
const asksEl = document.getElementById('asks');
const historyEl = document.getElementById('history');
const statsEl = document.getElementById('stats');
const eventsEl = document.getElementById('events');
const scannerStateEl = document.getElementById('scannerState');

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
  const latest = candles[candles.length - 1] || { open: 0, close: 0, high: 0, low: 0 };

  const markerHistory = (history || []).filter(s => s.confidence >= 90).map(s => ({
    x: s.created_at,
    y: s.entry,
    text: `${s.direction} ${s.confidence.toFixed(1)}%`,
    symbol: s.direction === 'LONG' ? 'arrow-up' : 'arrow-down',
    color: s.direction === 'LONG' ? '#22c55e' : '#ef4444'
  }));

  Plotly.newPlot(candlesChart, [
    {
      x: candles.map(c => c.timestamp),
      open: candles.map(c => c.open),
      high: candles.map(c => c.high),
      low: candles.map(c => c.low),
      close: candles.map(c => c.close),
      type: 'candlestick',
      name: snapshot.symbol
    },
    {
      x: markerHistory.map(m => m.x),
      y: markerHistory.map(m => m.y),
      text: markerHistory.map(m => m.text),
      mode: 'markers+text',
      marker: { size: 16, symbol: markerHistory.map(m => m.symbol), color: markerHistory.map(m => m.color) },
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
    `Pattern: <b>${candlePattern(latest)}</b>`,
    `Liquidity High: <b>${snapshot.liquidity.swing_high.toFixed(2)}</b>`,
    `Liquidity Low: <b>${snapshot.liquidity.swing_low.toFixed(2)}</b>`
  ].map(v => `<div>${v}</div>`).join('');

  const ob = snapshot.orderbook || { bids: [], asks: [], spread: 0, imbalance: 0 };
  orderbookMeta.innerHTML = `Spread: <b>${ob.spread.toFixed(4)}</b> | Imbalance: <b>${(ob.imbalance * 100).toFixed(2)}%</b>`;
  bidsEl.innerHTML = (ob.bids || []).slice(0, 12).map(x => `<li>${x[0].toFixed(2)} · ${x[1].toFixed(3)}</li>`).join('');
  asksEl.innerHTML = (ob.asks || []).slice(0, 12).map(x => `<li>${x[0].toFixed(2)} · ${x[1].toFixed(3)}</li>`).join('');

  statsEl.innerHTML = `Signals total: <b>${stats.total_signals}</b> | Last 24h: <b>${stats.signals_last_24h}</b> | Avg conf: <b>${stats.avg_confidence.toFixed(2)}%</b>`;
  historyEl.innerHTML = (history || []).slice(0, 40).map(s => `<li>${s.created_at} | <b>${s.symbol} ${s.direction}</b> entry=${s.entry.toFixed(2)} conf=${s.confidence.toFixed(1)} rr=${s.rr.toFixed(2)}</li>`).join('');
}

async function load() {
  const res = await fetch(`/api/snapshot?symbol=${encodeURIComponent(symbolSelect.value)}&timeframe=${encodeURIComponent(timeframeSelect.value)}`);
  const data = await res.json();
  if (data.ok) render(data.snapshot, data.history, data.stats);
}

async function loadEvents() {
  const [eventsRes, statusRes] = await Promise.all([fetch('/api/events?limit=25'), fetch('/api/scanner/status')]);
  const eventsData = await eventsRes.json();
  const statusData = await statusRes.json();
  scannerStateEl.innerHTML = `Scanner: <b>${statusData.running ? 'running' : 'paused'}</b> | Symbols: <b>${(statusData.tracked_symbols || []).join(', ') || '-'}</b>`;
  eventsEl.innerHTML = (eventsData.items || []).map(e => `<li>${e.ts} | <b>${e.type}</b> | ${JSON.stringify(e.payload)}</li>`).join('');
}

symbolSelect.addEventListener('change', load);
timeframeSelect.addEventListener('change', load);
setInterval(() => { load(); loadEvents(); }, (window.APP_CONFIG?.pollSec || 8) * 1000);
load();
loadEvents();

const form = document.getElementById('advisorForm');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(form).entries());
  const res = await fetch('/advisor', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  document.getElementById('advisorResult').textContent = JSON.stringify(await res.json(), null, 2);
});

document.getElementById('pauseScannerBtn').addEventListener('click', async () => { await fetch('/api/scanner/pause', { method: 'POST' }); loadEvents(); });
document.getElementById('resumeScannerBtn').addEventListener('click', async () => { await fetch('/api/scanner/resume', { method: 'POST' }); loadEvents(); });
document.getElementById('runBacktestBtn').addEventListener('click', async () => {
  const payload = { symbol: symbolSelect.value, timeframe: timeframeSelect.value };
  const res = await fetch('/api/backtest/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const result = await res.json();
  eventsEl.insertAdjacentHTML('afterbegin', `<li><b>backtest_result</b> | ${JSON.stringify(result)}</li>`);
});
document.getElementById('exportHistoryBtn').addEventListener('click', () => window.open(`/api/history/export?symbol=${encodeURIComponent(symbolSelect.value)}&limit=500`, '_blank'));
