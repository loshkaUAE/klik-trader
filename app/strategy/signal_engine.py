from __future__ import annotations

from app.models import Signal
from app.risk.risk_engine import compute_levels
from app.strategy.market_structure import structure_bias


class SignalEngine:
    def evaluate(self, symbol: str, frame):
        row = frame.iloc[-1]

        trend_up = row["ema_21"] > row["ema_200"]
        momentum_up = row["rsi"] > 52 and row["macd_hist"] > 0
        trend_down = row["ema_21"] < row["ema_200"]
        momentum_down = row["rsi"] < 48 and row["macd_hist"] < 0

        bias = structure_bias(frame)
        direction = None
        confidence = 0.0

        if trend_up and momentum_up and bias == "bullish":
            direction = "LONG"
            confidence = 92.0 + min(row["adx"] / 25.0, 6.0)
        elif trend_down and momentum_down and bias == "bearish":
            direction = "SHORT"
            confidence = 92.0 + min(row["adx"] / 25.0, 6.0)

        if direction is None:
            return None

        entry = float(row["close"])
        stop, tp1, tp2, tp3, rr = compute_levels(entry, float(row["atr"]), direction)
        why = f"{bias} structure + trend/momentum alignment + ADX={row['adx']:.1f}"
        return Signal(
            symbol=symbol,
            direction=direction,
            entry=entry,
            stop_loss=float(stop),
            tp1=float(tp1),
            tp2=float(tp2),
            tp3=float(tp3),
            rr=float(rr),
            confidence=float(min(confidence, 99.9)),
            why=why,
        )
