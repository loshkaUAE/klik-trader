from __future__ import annotations

from app.config import settings


class BybitClient:
    """Tiny wrapper state for whether live Bybit credentials are configured."""

    @property
    def enabled(self) -> bool:
        return bool(settings.bybit_api_key and settings.bybit_api_secret)
