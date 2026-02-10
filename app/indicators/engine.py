from __future__ import annotations

import pandas as pd


class IndicatorEngine:
    def calculate(self, candles: pd.DataFrame) -> pd.DataFrame:
        df = candles.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        df["ema_21"] = df["close"].ewm(span=21, adjust=False).mean()
        df["ema_200"] = df["close"].ewm(span=200, adjust=False).mean()

        diff = df["close"].diff()
        gain = diff.clip(lower=0).rolling(14).mean()
        loss = (-diff.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-9)
        df["rsi"] = 100 - (100 / (1 + rs))

        tr = pd.concat(
            [
                (df["high"] - df["low"]),
                (df["high"] - df["close"].shift()).abs(),
                (df["low"] - df["close"].shift()).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["atr"] = tr.rolling(14).mean().bfill()

        fast = df["close"].ewm(span=12, adjust=False).mean()
        slow = df["close"].ewm(span=26, adjust=False).mean()
        macd = fast - slow
        signal = macd.ewm(span=9, adjust=False).mean()
        df["macd_hist"] = macd - signal

        ma20 = df["close"].rolling(20).mean().bfill()
        std20 = df["close"].rolling(20).std().bfill()
        df["bb_width"] = ((ma20 + 2 * std20) - (ma20 - 2 * std20)) / ma20.replace(0, 1e-9)

        tp = (df["high"] + df["low"] + df["close"]) / 3
        df["vwap"] = (tp * df["volume"]).cumsum() / df["volume"].cumsum().replace(0, 1e-9)

        plus_dm = (df["high"].diff()).clip(lower=0)
        minus_dm = (-df["low"].diff()).clip(lower=0)
        plus_di = 100 * plus_dm.rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
        minus_di = 100 * minus_dm.rolling(14).sum() / tr.rolling(14).sum().replace(0, 1e-9)
        dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9) * 100
        df["adx"] = dx.rolling(14).mean().bfill()

        # Simple fair value gap helpers
        df["fvg_up"] = ((df["low"] > df["high"].shift(2)).astype(int)).fillna(0)
        df["fvg_down"] = ((df["high"] < df["low"].shift(2)).astype(int)).fillna(0)

        return df.bfill().ffill()
