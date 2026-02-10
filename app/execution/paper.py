from __future__ import annotations

from app.models import Position, Signal


class PaperExecutionEngine:
    def __init__(self) -> None:
        self.positions: list[Position] = []

    def open_from_signal(self, signal: Signal, size: float = 1.0) -> Position:
        position = Position(
            symbol=signal.symbol,
            direction=signal.direction,
            entry=signal.entry,
            size=size,
            stop_loss=signal.stop_loss,
            tp1=signal.tp1,
            tp2=signal.tp2,
            tp3=signal.tp3,
        )
        self.positions.append(position)
        return position
