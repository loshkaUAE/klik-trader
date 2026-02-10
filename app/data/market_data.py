from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from app.data.bybit_client import BybitClient


class MarketDataService:
    def __init__(self) -> None:
        self.client = BybitClient()

    @staticmethod
    def _interval_minutes(timeframe: str) -> int:
        if timeframe == "D":
            return 24 * 60
        return int(timeframe)

    def _synthetic_candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        seed = abs(hash((symbol, timeframe))) % 2_000_000
        rng = np.random.default_rng(seed)
        interval = self._interval_minutes(timeframe)
        start = datetime.now(timezone.utc) - timedelta(minutes=interval * (limit - 1))

        drift = 0.0005 if "BTC" in symbol else 0.0003
        returns = rng.normal(drift, 0.008, size=limit)
        close = 100.0 * np.exp(np.cumsum(returns))
        open_ = np.concatenate([[close[0]], close[:-1]])
        high = np.maximum(open_, close) * (1 + rng.uniform(0.0002, 0.005, size=limit))
        low = np.minimum(open_, close) * (1 - rng.uniform(0.0002, 0.005, size=limit))
        volume = rng.uniform(50, 500, size=limit)

        rows = []
        for i in range(limit):
            ts = start + timedelta(minutes=interval * i)
            rows.append(
                {
                    "timestamp": ts.isoformat(),
                    "open": float(open_[i]),
                    "high": float(high[i]),
                    "low": float(low[i]),
                    "close": float(close[i]),
                    "volume": float(volume[i]),
                }
            )
        return pd.DataFrame(rows)

    def fetch_candles(self, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
        # Deterministic fallback-first implementation for robust local run.
        return self._synthetic_candles(symbol=symbol, timeframe=timeframe, limit=limit)

    def fetch_orderbook(self, symbol: str) -> dict:
        last = self.fetch_candles(symbol=symbol, timeframe="1", limit=1).iloc[-1]
        mid = float(last["close"])
        bids = [[mid - (i + 1) * 0.1, 1.2 + i * 0.3] for i in range(15)]
        asks = [[mid + (i + 1) * 0.1, 1.1 + i * 0.25] for i in range(15)]
        bid_vol = sum(x[1] for x in bids)
        ask_vol = sum(x[1] for x in asks)
        return {
            "bids": bids,
            "asks": asks,
            "spread": asks[0][0] - bids[0][0],
            "imbalance": (bid_vol - ask_vol) / max(bid_vol + ask_vol, 1e-9),
        }
