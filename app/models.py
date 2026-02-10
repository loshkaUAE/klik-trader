from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Signal:
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    rr: float
    confidence: float
    why: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class TradeIdea:
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    rr: float
    quality_score: float
    confidence: float
    reasoning: str


@dataclass(slots=True)
class Position:
    symbol: str
    direction: str
    entry: float
    size: float
    stop_loss: float
    tp1: float
    tp2: float
    tp3: float
    opened_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "open"
    realized_pnl: Optional[float] = None
