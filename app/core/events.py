from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any


class EventService:
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
        events = list(self._events)
        if event_type:
            events = [x for x in events if x["type"] == event_type]
        return events[:limit]
