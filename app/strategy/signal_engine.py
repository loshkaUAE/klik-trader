from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from app.config import settings
from app.models import Signal
from app.risk.risk_engine import RiskEngine
from app.strategy.market_structure import detect_structure


class SignalEngine:
    def __init__(self) -> None:
        self.risk_engine = RiskEngine()

    def evaluate(self, symbol: str, df: pd.DataFrame) -> Signal | None:
        row = df.iloc[-1]
        structure = detect_structure(df)
        direction = self._direction_from_layers(row, structure)
        if direction is None:
            return None

        confidence, why = self._confidence_and_why(row, structure, direction)
        if confidence < settings.confidence_threshold:
            return None

        entry = float(row["close"])
        liquidity = float(df["low"].tail(8).min()) if direction == "LONG" else float(df["high"].tail(8).max())
        plan = self.risk_engine.build_levels(direction, entry, float(row["atr"]), liquidity)

        return Signal(
            symbol=symbol,
            direction=direction,
            entry=entry,
            stop_loss=plan.stop_loss,
            tp1=plan.tp1,
            tp2=plan.tp2,
            tp3=plan.tp3,
            rr=plan.rr,
            confidence=confidence,
            why=why,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _direction_from_layers(row: pd.Series, structure: dict) -> str | None:
        bullish = (
            structure["trend"] == "bullish"
            and row["ema_9"] > row["ema_21"] > row["ema_200"]
            and row["macd_hist"] > 0
            and row["rsi"] > 52
            and row["adx"] > 18
        )
        bearish = (
            structure["trend"] == "bearish"
            and row["ema_9"] < row["ema_21"] < row["ema_200"]
            and row["macd_hist"] < 0
            and row["rsi"] < 48
            and row["adx"] > 18
        )
        if bullish:
            return "LONG"
        if bearish:
            return "SHORT"
        return None

    @staticmethod
    def _session_score(ts: pd.Timestamp) -> int:
        hour = ts.tz_convert("UTC").hour
        if 6 <= hour <= 11 or 12 <= hour <= 16:
            return 12  # London/NY kill zones
        if 0 <= hour <= 5:
            return 5  # Asia
        return 8

    def _confidence_and_why(self, row: pd.Series, structure: dict, direction: str) -> tuple[float, str]:
        score = 0
        reasons = []

        trend_ok = (row["ema_21"] > row["ema_200"]) if direction == "LONG" else (row["ema_21"] < row["ema_200"])
        if trend_ok:
            score += 18
            reasons.append("HTF/LTF trend alignment")

        if structure["bos"] and not structure["choch"]:
            score += 16
            reasons.append("Clean BOS with no CHoCH conflict")

        if (direction == "LONG" and row["fvg_up"] > 0) or (direction == "SHORT" and row["fvg_down"] > 0):
            score += 12
            reasons.append("Fresh FVG imbalance")

        if row["atr"] > 0 and 0.002 < (row["atr"] / row["close"]) < 0.03:
            score += 12
            reasons.append("Healthy volatility regime")

        if row["adx"] > 22:
            score += 12
            reasons.append("Strong trend strength (ADX)")

        if (direction == "LONG" and row["cmf"] > 0) or (direction == "SHORT" and row["cmf"] < 0):
            score += 10
            reasons.append("Volume flow confirms move")

        session_bonus = self._session_score(row["timestamp"])
        score += session_bonus
        reasons.append("Session filter passed")

        liq = (row["eq_lows"] > 0 and direction == "LONG") or (row["eq_highs"] > 0 and direction == "SHORT")
        if liq:
            score += 10
            reasons.append("Liquidity pool identified")

        confidence = min(float(score), 99.0)
        why = "; ".join(reasons)
        return confidence, why
