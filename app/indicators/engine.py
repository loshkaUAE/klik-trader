from __future__ import annotations

import numpy as np
import pandas as pd
import ta


class IndicatorEngine:
    """Calculates 30+ deterministic indicators on candle close only."""

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        high, low, close, volume = out["high"], out["low"], out["close"], out["volume"]

        # Trend
        out["sma_20"] = ta.trend.sma_indicator(close, 20)
        out["sma_50"] = ta.trend.sma_indicator(close, 50)
        out["ema_9"] = ta.trend.ema_indicator(close, 9)
        out["ema_21"] = ta.trend.ema_indicator(close, 21)
        out["ema_200"] = ta.trend.ema_indicator(close, 200)
        out["adx"] = ta.trend.adx(high, low, close, 14)
        out["adx_pos"] = ta.trend.adx_pos(high, low, close, 14)
        out["adx_neg"] = ta.trend.adx_neg(high, low, close, 14)
        out["ichimoku_a"] = ta.trend.ichimoku_a(high, low)
        out["ichimoku_b"] = ta.trend.ichimoku_b(high, low)
        out["macd"] = ta.trend.macd(close)
        out["macd_signal"] = ta.trend.macd_signal(close)
        out["macd_hist"] = out["macd"] - out["macd_signal"]

        # Momentum
        out["rsi"] = ta.momentum.rsi(close, 14)
        out["stoch_k"] = ta.momentum.stoch(high, low, close)
        out["stoch_d"] = ta.momentum.stoch_signal(high, low, close)
        out["cci"] = ta.trend.cci(high, low, close, 20)
        out["williams_r"] = ta.momentum.williams_r(high, low, close, 14)
        out["roc"] = ta.momentum.roc(close, 12)

        # Volatility
        out["atr"] = ta.volatility.average_true_range(high, low, close, 14)
        out["bb_mid"] = ta.volatility.bollinger_mavg(close)
        out["bb_high"] = ta.volatility.bollinger_hband(close)
        out["bb_low"] = ta.volatility.bollinger_lband(close)
        out["bb_width"] = (out["bb_high"] - out["bb_low"]) / out["bb_mid"].replace(0, np.nan)
        out["kc_mid"] = ta.volatility.keltner_channel_mband(high, low, close)
        out["kc_high"] = ta.volatility.keltner_channel_hband(high, low, close)
        out["kc_low"] = ta.volatility.keltner_channel_lband(high, low, close)
        out["donchian_high"] = ta.volatility.donchian_channel_hband(high, low, close)
        out["donchian_low"] = ta.volatility.donchian_channel_lband(high, low, close)

        # Volume / flow
        out["obv"] = ta.volume.on_balance_volume(close, volume)
        out["cmf"] = ta.volume.chaikin_money_flow(high, low, close, volume)
        out["mfi"] = ta.volume.money_flow_index(high, low, close, volume)
        out["vwap"] = ta.volume.volume_weighted_average_price(high, low, close, volume)
        out["adi"] = ta.volume.acc_dist_index(high, low, close, volume)

        # SuperTrend approximation + pivots/fib
        hl2 = (high + low) / 2
        out["supertrend_proxy"] = hl2 - (1.5 * out["atr"])
        out["pivot"] = (high.shift(1) + low.shift(1) + close.shift(1)) / 3
        out["pivot_r1"] = 2 * out["pivot"] - low.shift(1)
        out["pivot_s1"] = 2 * out["pivot"] - high.shift(1)
        swing_high = high.rolling(100).max()
        swing_low = low.rolling(100).min()
        out["fib_382"] = swing_low + 0.382 * (swing_high - swing_low)
        out["fib_618"] = swing_low + 0.618 * (swing_high - swing_low)

        # Liquidity & structure helpers
        out["eq_highs"] = (high.round(2).rolling(10).apply(lambda s: len(set(s)) < 8, raw=False)).fillna(0)
        out["eq_lows"] = (low.round(2).rolling(10).apply(lambda s: len(set(s)) < 8, raw=False)).fillna(0)
        out["fvg_up"] = (low.shift(1) > high.shift(2)).astype(int)
        out["fvg_down"] = (high.shift(1) < low.shift(2)).astype(int)

        out = out.dropna().reset_index(drop=True)
        return out
