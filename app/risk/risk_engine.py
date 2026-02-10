from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RiskPlan:
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    rr: float


class RiskEngine:
    def build_levels(self, direction: str, entry: float, atr: float, liquidity_level: float) -> RiskPlan:
        atr_buffer = max(atr * 0.9, entry * 0.002)
        if direction.upper() == "LONG":
            stop = min(liquidity_level, entry - atr_buffer)
            risk = entry - stop
            tp1, tp2, tp3 = entry + 2 * risk, entry + 3 * risk, entry + 4 * risk
        else:
            stop = max(liquidity_level, entry + atr_buffer)
            risk = stop - entry
            tp1, tp2, tp3 = entry - 2 * risk, entry - 3 * risk, entry - 4 * risk
        rr = abs((tp2 - entry) / (entry - stop)) if entry != stop else 0.0
        return RiskPlan(stop_loss=stop, tp1=tp1, tp2=tp2, tp3=tp3, rr=rr)
