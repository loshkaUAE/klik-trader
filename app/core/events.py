from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any


class EventService:
    """In-memory event stream used instead of external chat bots."""

    def __init__(self, max_events: int = 500) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self._events.appendleft(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "payload": payload,
            }
        )

    def recent(self, limit: int = 100, event_type: str | None = None) -> list[dict[str, Any]]:
        items = list(self._events)
        if event_type:
            items = [e for e in items if e["type"] == event_type]
        return items[:limit]
