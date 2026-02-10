from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(slots=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


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
class PerformanceSnapshot:
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    winrate: float = 0.0
    drawdown_pct: float = 0.0
    equity_curve: List[float] = field(default_factory=lambda: [100.0])
    last_signals: List[Signal] = field(default_factory=list)
    volatility_regime: str = "normal"
    market_bias: Dict[str, str] = field(default_factory=dict)
    active_setups: List[Signal] = field(default_factory=list)


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
