from __future__ import annotations

import asyncio
from dataclasses import asdict

from app.config import settings
from app.core.events import EventService
from app.data.market_data import MarketDataService
from app.indicators.engine import IndicatorEngine
from app.storage.history_store import HistoryStore
from app.strategy.signal_engine import SignalEngine


class ScannerService:
    def __init__(self, history: HistoryStore, events: EventService) -> None:
        self.market = MarketDataService()
        self.indicators = IndicatorEngine()
        self.signal_engine = SignalEngine()
        self.history = history
        self.events = events
        self.running = False
        self.latest: dict[str, dict] = {}

    async def run_forever(self) -> None:
        self.running = True
        symbols = [s.strip() for s in settings.default_symbols.split(",") if s.strip()]
        while self.running:
            try:
                for symbol in symbols:
                    candles = self.market.fetch_candles(symbol, settings.default_timeframe, 300)
                    frame = self.indicators.calculate(candles)
                    last = frame.iloc[-1]
                    orderbook = self.market.fetch_orderbook(symbol)
                    liquidity = {
                        "swing_high": float(frame["high"].tail(50).max()),
                        "swing_low": float(frame["low"].tail(50).min()),
                        "fvg_up": bool(last["fvg_up"] > 0),
                        "fvg_down": bool(last["fvg_down"] > 0),
                    }
                    signal = self.signal_engine.evaluate(symbol, frame)

                    self.latest[symbol] = {
                        "symbol": symbol,
                        "timeframe": settings.default_timeframe,
                        "timestamp": last["timestamp"].isoformat(),
                        "price": float(last["close"]),
                        "bias": "bullish" if last["ema_21"] > last["ema_200"] else "bearish",
                        "orderbook": orderbook,
                        "liquidity": liquidity,
                        "indicators": {
                            "rsi": float(last["rsi"]),
                            "adx": float(last["adx"]),
                            "atr": float(last["atr"]),
                            "macd_hist": float(last["macd_hist"]),
                            "bb_width": float(last["bb_width"]),
                            "vwap": float(last["vwap"]),
                        },
                        "candles": candles.tail(200).to_dict(orient="records"),
                        "signal": asdict(signal) if signal else None,
                    }

                    if signal:
                        self.history.save_signal(signal, meta={"timeframe": settings.default_timeframe, "source": "scanner"})
                        self.events.publish("signal", {"symbol": signal.symbol, "direction": signal.direction, "confidence": signal.confidence})
            except Exception as exc:
                self.events.publish("error", {"message": str(exc)})
            await asyncio.sleep(settings.scan_interval_sec)

    def stop(self) -> None:
        self.running = False
