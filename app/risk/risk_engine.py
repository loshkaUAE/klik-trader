from __future__ import annotations


def compute_levels(entry: float, atr: float, direction: str) -> tuple[float, float, float, float, float]:
    stop_dist = max(atr * 1.6, entry * 0.003)
    if direction == "LONG":
        stop = entry - stop_dist
        tp1 = entry + stop_dist * 2
        tp2 = entry + stop_dist * 3
        tp3 = entry + stop_dist * 4
    else:
        stop = entry + stop_dist
        tp1 = entry - stop_dist * 2
        tp2 = entry - stop_dist * 3
        tp3 = entry - stop_dist * 4
    rr = abs(tp1 - entry) / abs(entry - stop)
    return stop, tp1, tp2, tp3, rr
