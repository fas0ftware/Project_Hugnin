"""Shared RSI helpers for the Hugnin terminal scanner and Telegram bot."""

import pandas as pd

RSI_PERIOD = 14
OVERSOLD_LEVEL = 30
OVERBOUGHT_LEVEL = 70


def calculate_rsi_series(prices: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Relative Strength Index using Wilder's smoothing (same as Project_Heimdall).

    The first `period` values are NaN because there is not enough history yet.
    """
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    # No losses at all in the window means RSI is 100 by definition.
    return rsi.where(~((avg_loss == 0) & (avg_gain > 0)), 100.0)


def latest_rsi(prices: pd.Series, period: int = RSI_PERIOD):
    """Most recent RSI value, or None when there is not enough data."""
    if len(prices) <= period:
        return None
    value = calculate_rsi_series(prices, period).iloc[-1]
    return None if pd.isna(value) else float(value)
