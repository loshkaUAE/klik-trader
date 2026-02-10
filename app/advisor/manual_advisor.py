from __future__ import annotations

from app.data.market_data import MarketDataService
from app.indicators.engine import IndicatorEngine
from app.models import TradeIdea
from app.risk.risk_engine import RiskEngine
from app.strategy.market_structure import detect_structure


class TradeAdvisor:
    def __init__(self) -> None:
        self.market_data = MarketDataService()
        self.indicators = IndicatorEngine()
        self.risk = RiskEngine()

    def advise(self, symbol: str, direction: str, entry: float, timeframe: str = "15") -> TradeIdea:
        candles = self.market_data.fetch_candles(symbol=symbol, interval=timeframe, limit=300)
        frame = self.indicators.calculate(candles)
        last = frame.iloc[-1]
        structure = detect_structure(frame)

        liquidity_level = float(frame["low"].tail(12).min()) if direction == "LONG" else float(frame["high"].tail(12).max())
        plan = self.risk.build_levels(direction, entry, float(last["atr"]), liquidity_level)

        score = 50.0
        if structure["trend"] == "bullish" and direction == "LONG":
            score += 18
        if structure["trend"] == "bearish" and direction == "SHORT":
            score += 18
        if plan.rr >= 2.0:
            score += 15
        if last["adx"] > 20:
            score += 10
        if (direction == "LONG" and last["rsi"] > 50) or (direction == "SHORT" and last["rsi"] < 50):
            score += 7

        confidence = min(score, 99.0)
        reasoning = (
            f"Structure={structure['trend']}, ADX={last['adx']:.1f}, RSI={last['rsi']:.1f}, "
            f"ATR={last['atr']:.2f}, Liquidity anchor={liquidity_level:.2f}."
        )

        return TradeIdea(
            symbol=symbol,
            direction=direction,
            entry=entry,
            stop_loss=plan.stop_loss,
            tp1=plan.tp1,
            tp2=plan.tp2,
            tp3=plan.tp3,
            rr=plan.rr,
            quality_score=confidence,
            confidence=confidence,
            reasoning=reasoning,
        )
