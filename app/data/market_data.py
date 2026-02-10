from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.data.bybit_client import BybitClient


class MarketDataService:
    def __init__(self) -> None:
        self.client = BybitClient()

    def fetch_candles(self, symbol: str, interval: str = "15", limit: int = 300) -> pd.DataFrame:
        raw = self.client.get_klines(symbol, interval, limit)
        if raw:
            rows = []
            for k in raw:
                rows.append(
                    {
                        "timestamp": pd.to_datetime(int(k[0]), unit="ms", utc=True),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                    }
                )
            return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
        return self._synthetic_data(limit)

    def fetch_last_price(self, symbol: str) -> float:
        px = self.client.get_last_price(symbol)
        if px is not None:
            return px
        return float(self._synthetic_data(1)["close"].iloc[-1])

    def fetch_orderbook(self, symbol: str, limit: int = 50) -> dict:
        raw = self.client.get_orderbook(symbol=symbol, limit=limit)
        if raw:
            bids = [[float(px), float(sz)] for px, sz in raw.get("b", [])]
            asks = [[float(px), float(sz)] for px, sz in raw.get("a", [])]
        else:
            mid = self.fetch_last_price(symbol)
            bids = [[mid - i, 10 + i * 2] for i in range(1, 21)]
            asks = [[mid + i, 9 + i * 2] for i in range(1, 21)]

        bid_notional = sum(px * sz for px, sz in bids)
        ask_notional = sum(px * sz for px, sz in asks)
        top_bid = bids[0][0] if bids else 0.0
        top_ask = asks[0][0] if asks else 0.0
        spread = max(top_ask - top_bid, 0.0)
        imbalance = (bid_notional - ask_notional) / (bid_notional + ask_notional) if (bid_notional + ask_notional) else 0.0

        return {
            "bids": bids[:20],
            "asks": asks[:20],
            "spread": spread,
            "bid_notional": bid_notional,
            "ask_notional": ask_notional,
            "imbalance": imbalance,
        }

    @staticmethod
    def _synthetic_data(limit: int) -> pd.DataFrame:
        np.random.seed(42)
        timestamps = [datetime.utcnow() - timedelta(minutes=(limit - i) * 15) for i in range(limit)]
        walk = np.cumsum(np.random.normal(0, 35, size=limit)) + 65000
        close = np.maximum(walk, 500)
        open_ = np.concatenate(([close[0]], close[:-1]))
        high = np.maximum(open_, close) + np.random.uniform(8, 55, size=limit)
        low = np.minimum(open_, close) - np.random.uniform(8, 55, size=limit)
        volume = np.random.uniform(100, 2500, size=limit)
        return pd.DataFrame(
            {
                "timestamp": pd.to_datetime(timestamps, utc=True),
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
