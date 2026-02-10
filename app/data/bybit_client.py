from __future__ import annotations

from typing import Any, Dict, List

from pybit.unified_trading import HTTP

from app.config import settings


class BybitClient:
    def __init__(self) -> None:
        self.enabled = bool(settings.bybit_api_key and settings.bybit_api_secret)
        self.http = HTTP(
            testnet=settings.bybit_testnet,
            api_key=settings.bybit_api_key,
            api_secret=settings.bybit_api_secret,
        )

    def get_klines(self, symbol: str, interval: str = "15", limit: int = 300) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        response = self.http.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        return response.get("result", {}).get("list", [])

    def get_last_price(self, symbol: str) -> float | None:
        if not self.enabled:
            return None
        response = self.http.get_tickers(category="linear", symbol=symbol)
        result = response.get("result", {}).get("list", [])
        if not result:
            return None
        return float(result[0]["lastPrice"])

    def get_orderbook(self, symbol: str, limit: int = 50) -> dict[str, Any]:
        if not self.enabled:
            return {}
        response = self.http.get_orderbook(category="linear", symbol=symbol, limit=limit)
        return response.get("result", {})
