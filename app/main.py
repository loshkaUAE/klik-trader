from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.advisor.manual_advisor import TradeAdvisor
from app.config import settings
from app.core.scanner import ScannerService
from app.data.market_data import MarketDataService
from app.indicators.engine import IndicatorEngine
from app.storage.history_store import HistoryStore
from app.strategy.signal_engine import SignalEngine
from app.telegram.bot import TelegramNotifier

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

advisor = TradeAdvisor()
history = HistoryStore()
market = MarketDataService()
indicators = IndicatorEngine()
signal_engine = SignalEngine()

notifier = TelegramNotifier(
    status_provider=lambda: {
        "mode": settings.mode,
        "symbols": settings.default_symbols,
        "threshold": settings.confidence_threshold,
        "scan_interval_sec": settings.scan_interval_sec,
        "total_signals": history.stats()["total_signals"],
    },
    latest_signals_provider=lambda: history.fetch_signals(limit=5),
)
scanner = ScannerService(notifier=notifier, history=history)
scanner_task: asyncio.Task | None = None


def build_snapshot(symbol: str, timeframe: str) -> dict:
    candles = market.fetch_candles(symbol, timeframe, 300)
    frame = indicators.calculate(candles)
    row = frame.iloc[-1]
    signal = signal_engine.evaluate(symbol, frame)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "timestamp": row["timestamp"].isoformat(),
        "price": float(row["close"]),
        "bias": "bullish" if row["ema_21"] > row["ema_200"] else "bearish",
        "orderbook": market.fetch_orderbook(symbol),
        "liquidity": {
            "swing_high": float(frame["high"].tail(50).max()),
            "swing_low": float(frame["low"].tail(50).min()),
            "fvg_up": bool(row["fvg_up"] > 0),
            "fvg_down": bool(row["fvg_down"] > 0),
        },
        "indicators": {
            "rsi": float(row["rsi"]),
            "adx": float(row["adx"]),
            "atr": float(row["atr"]),
            "macd_hist": float(row["macd_hist"]),
            "bb_width": float(row["bb_width"]),
            "vwap": float(row["vwap"]),
        },
        "candles": candles.tail(220).to_dict(orient="records"),
        "signal": asdict(signal) if signal else None,
    }


@app.on_event("startup")
async def startup_event() -> None:
    global scanner_task
    await notifier.start_bot_host()
    scanner_task = asyncio.create_task(scanner.run_forever())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    scanner.stop()
    if scanner_task:
        scanner_task.cancel()
    await notifier.stop_bot_host()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "symbols": [s.strip() for s in settings.default_symbols.split(",") if s.strip()],
            "default_timeframe": settings.default_timeframe,
            "poll_sec": settings.dashboard_poll_sec,
        },
    )


@app.post("/advisor")
async def manual_advisor(payload: dict) -> dict:
    idea = advisor.advise(
        symbol=payload["symbol"],
        direction=payload["direction"].upper(),
        entry=float(payload["entry"]),
        timeframe=str(payload.get("timeframe", settings.default_timeframe)),
    )
    return asdict(idea)


@app.get("/api/snapshot")
async def snapshot(symbol: str = Query(default="BTCUSDT"), timeframe: str = Query(default="15")) -> dict:
    data = build_snapshot(symbol, timeframe)
    return {
        "ok": True,
        "symbol": symbol,
        "snapshot": data,
        "history": history.fetch_signals(symbol=symbol, limit=50),
        "stats": history.stats(),
    }


@app.get("/api/history")
async def signal_history(symbol: str | None = None, limit: int = 100) -> dict:
    return {"items": history.fetch_signals(symbol=symbol, limit=limit)}


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "mode": settings.mode, "time": datetime.now(timezone.utc).isoformat()}


@app.websocket("/ws")
async def websocket_feed(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            await ws.send_json({"type": "state", "symbols": list(scanner.latest.keys()), "updated_at": datetime.now(timezone.utc).isoformat()})
            await asyncio.sleep(settings.dashboard_poll_sec)
    except Exception:
        await ws.close()
