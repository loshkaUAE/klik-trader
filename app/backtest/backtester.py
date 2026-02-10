from __future__ import annotations

import pandas as pd

from app.indicators.engine import IndicatorEngine
from app.strategy.signal_engine import SignalEngine


class Backtester:
    def __init__(self) -> None:
        self.indicators = IndicatorEngine()
        self.engine = SignalEngine()

    def run(self, symbol: str, candles: pd.DataFrame) -> dict:
        df = self.indicators.calculate(candles)
        trades = 0
        equity = 100.0
        for i in range(220, len(df)):
            sig = self.engine.evaluate(symbol, df.iloc[: i + 1])
            if sig:
                trades += 1
                equity += 0.8
        return {"symbol": symbol, "trades": trades, "ending_equity": round(equity, 2)}
