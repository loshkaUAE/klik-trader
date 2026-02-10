from __future__ import annotations

import pandas as pd


def structure_bias(frame: pd.DataFrame) -> str:
    hh = frame["high"].iloc[-1] > frame["high"].iloc[-5]
    hl = frame["low"].iloc[-1] > frame["low"].iloc[-5]
    lh = frame["high"].iloc[-1] < frame["high"].iloc[-5]
    ll = frame["low"].iloc[-1] < frame["low"].iloc[-5]
    if hh and hl:
        return "bullish"
    if lh and ll:
        return "bearish"
    return "neutral"
