from __future__ import annotations

import asyncio
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Query, Request, WebSocket
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.advisor.manual_advisor import TradeAdvisor
from app.backtest.backtester import Backtester
from app.config import settings
from app.core.events import EventService
from app.core.scanner import ScannerService
from app.data.market_data import MarketDataService
from app.indicators.engine import IndicatorEngine
from app.storage.history_store import HistoryStore
from app.strategy.signal_engine import SignalEngine

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

advisor = TradeAdvisor()
history = HistoryStore()
events = EventService()
market = MarketDataService()
indicators = IndicatorEngine()
signal_engine = SignalEngine()
backtester = Backtester()
scanner = ScannerService(history=history, events=events)
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
    scanner_task = asyncio.create_task(scanner.run_forever())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    scanner.stop()
    if scanner_task:
        scanner_task.cancel()


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
    snap = build_snapshot(symbol, timeframe)
    return {
        "ok": True,
        "symbol": symbol,
        "snapshot": snap,
        "history": history.fetch_signals(symbol=symbol, limit=50),
        "stats": history.stats(),
    }


@app.get("/api/history")
async def signal_history(symbol: str | None = None, limit: int = 100) -> dict:
    return {"items": history.fetch_signals(symbol=symbol, limit=limit)}


@app.get("/api/history/export", response_class=PlainTextResponse)
async def export_history_csv(symbol: str | None = None, limit: int = 500) -> PlainTextResponse:
    rows = history.fetch_signals(symbol=symbol, limit=limit)
    headers = ["created_at", "symbol", "direction", "entry", "stop_loss", "tp1", "tp2", "tp3", "rr", "confidence", "why"]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join([str(row[h]).replace("\n", " ").replace(",", ";") for h in headers]))
    return PlainTextResponse("\n".join(lines), media_type="text/csv")


@app.get("/api/events")
async def recent_events(limit: int = 100, event_type: str | None = None) -> dict:
    return {"items": events.recent(limit=limit, event_type=event_type)}


@app.post("/api/backtest/run")
async def run_backtest(payload: dict) -> dict:
    symbol = payload.get("symbol", "BTCUSDT")
    timeframe = payload.get("timeframe", settings.default_timeframe)
    candles = market.fetch_candles(symbol, timeframe, 800)
    result = backtester.run(symbol=symbol, candles=candles)
    events.publish("backtest", result)
    return result


@app.post("/api/scanner/pause")
async def pause_scanner() -> dict:
    scanner.stop()
    events.publish("system", {"action": "scanner_paused"})
    return {"ok": True}


@app.post("/api/scanner/resume")
async def resume_scanner() -> dict:
    global scanner_task
    if scanner_task is None or scanner_task.done():
        scanner_task = asyncio.create_task(scanner.run_forever())
    events.publish("system", {"action": "scanner_resumed"})
    return {"ok": True}


@app.get("/api/scanner/status")
async def scanner_status() -> dict:
    return {"running": scanner.running, "tracked_symbols": list(scanner.latest.keys())}


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "mode": settings.mode, "time": datetime.now(timezone.utc).isoformat()}


@app.websocket("/ws")
async def websocket_feed(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            await ws.send_json(
                {
                    "type": "state",
                    "symbols": list(scanner.latest.keys()),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            await asyncio.sleep(settings.dashboard_poll_sec)
    except Exception:
        await ws.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
