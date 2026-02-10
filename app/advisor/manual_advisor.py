from __future__ import annotations

from app.data.market_data import MarketDataService
from app.indicators.engine import IndicatorEngine
from app.models import TradeIdea
from app.risk.risk_engine import compute_levels


class TradeAdvisor:
    def __init__(self) -> None:
        self.market = MarketDataService()
        self.indicators = IndicatorEngine()

    def advise(self, symbol: str, direction: str, entry: float, timeframe: str = "15") -> TradeIdea:
        candles = self.market.fetch_candles(symbol, timeframe, 300)
        frame = self.indicators.calculate(candles)
        row = frame.iloc[-1]
        stop, tp1, tp2, tp3, rr = compute_levels(entry, float(row["atr"]), direction)

        trend_aligned = (direction == "LONG" and row["ema_21"] > row["ema_200"]) or (
            direction == "SHORT" and row["ema_21"] < row["ema_200"]
        )
        momentum_aligned = (direction == "LONG" and row["rsi"] >= 50) or (direction == "SHORT" and row["rsi"] <= 50)

        quality = 70.0
        quality += 15.0 if trend_aligned else -8.0
        quality += 10.0 if momentum_aligned else -5.0
        quality += min(float(row["adx"]) / 10.0, 8.0)
        quality = max(1.0, min(99.0, quality))

        confidence = max(1.0, min(99.0, quality + (3.0 if rr >= 2 else -8.0)))
        reasoning = (
            f"ATR-adaptive risk; trend={'yes' if trend_aligned else 'no'}; "
            f"momentum={'yes' if momentum_aligned else 'no'}; ADX={row['adx']:.1f}; RR={rr:.2f}"
        )

        return TradeIdea(
            symbol=symbol,
            direction=direction,
            entry=entry,
            stop_loss=float(stop),
            tp1=float(tp1),
            tp2=float(tp2),
            tp3=float(tp3),
            rr=float(rr),
            quality_score=float(quality),
            confidence=float(confidence),
            reasoning=reasoning,
        )
