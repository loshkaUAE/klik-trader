from __future__ import annotations

import pandas as pd


def detect_structure(df: pd.DataFrame) -> dict:
    highs = df["high"].tail(6).tolist()
    lows = df["low"].tail(6).tolist()

    hh = highs[-1] > highs[-3] > highs[-5]
    hl = lows[-1] > lows[-3] > lows[-5]
    lh = highs[-1] < highs[-3] < highs[-5]
    ll = lows[-1] < lows[-3] < lows[-5]

    if hh and hl:
        trend = "bullish"
    elif lh and ll:
        trend = "bearish"
    else:
        trend = "range"

    bos = (df["close"].iloc[-1] > max(highs[:-1])) or (df["close"].iloc[-1] < min(lows[:-1]))
    choch = (hh and ll) or (lh and hl)

    return {
        "trend": trend,
        "hh": hh,
        "hl": hl,
        "lh": lh,
        "ll": ll,
        "bos": bos,
        "choch": choch,
    }
