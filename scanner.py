"""Hugnin scan engine: batch download, per-symbol metrics, signals, sorting and CSV export."""

import csv

import pandas as pd

from rsi import OVERBOUGHT_LEVEL, OVERSOLD_LEVEL, RSI_PERIOD, latest_rsi

MIN_BARS = RSI_PERIOD + 1
FIELDS = ["symbol", "price", "change_pct", "rsi", "signal", "trend", "from_52w_high_pct", "volume_ratio"]


def classify(rsi):
    """Signal label for an RSI value."""
    if rsi < OVERSOLD_LEVEL:
        return "OVERSOLD"
    if rsi > OVERBOUGHT_LEVEL:
        return "OVERBOUGHT"
    if rsi < 45:
        return "LOW"
    if rsi > 55:
        return "HIGH"
    return "NEUTRAL"


def trend_label(close):
    """UP when price is above its 50-day average, DOWN when below; adds the 200-day cross if known."""
    if len(close) < 50:
        return "n/a"
    price = close.iloc[-1]
    sma50 = close.tail(50).mean()
    label = "UP" if price >= sma50 else "DOWN"
    if len(close) >= 200:
        label += "/long-UP" if sma50 >= close.tail(200).mean() else "/long-DOWN"
    return label


def analyze_symbol(symbol, close, volume=None):
    """Metrics for one symbol from its daily closes (and optional volumes). None if too little data."""
    close = close.dropna()
    if len(close) < MIN_BARS:
        return None
    rsi = latest_rsi(close, RSI_PERIOD)
    if rsi is None:
        return None
    price = float(close.iloc[-1])
    previous = float(close.iloc[-2])
    high = float(close.tail(252).max())
    volume_ratio = None
    if volume is not None:
        volume = volume.dropna()
        if len(volume) > 21 and volume.tail(21).iloc[:-1].mean() > 0:
            volume_ratio = round(float(volume.iloc[-1] / volume.tail(21).iloc[:-1].mean()), 2)
    return {
        "symbol": symbol,
        "price": round(price, 4),
        "change_pct": round((price / previous - 1) * 100, 2) if previous else 0.0,
        "rsi": round(rsi, 1),
        "signal": classify(rsi),
        "trend": trend_label(close),
        "from_52w_high_pct": round((price / high - 1) * 100, 1) if high else 0.0,
        "volume_ratio": volume_ratio,
    }


def analyze_frame(frame, symbols):
    """Rows for every symbol present in a yfinance multi-ticker frame (group_by='ticker')."""
    rows = []
    for symbol in symbols:
        try:
            if isinstance(frame.columns, pd.MultiIndex):
                if symbol not in frame.columns.get_level_values(0):
                    continue
                part = frame[symbol]
            else:  # single symbol download
                part = frame
            close = part["Close"]
            volume = part["Volume"] if "Volume" in part else None
        except KeyError:
            continue
        row = analyze_symbol(symbol, close, volume)
        if row:
            rows.append(row)
    return rows


def download(symbols, period="1y"):
    """One batched Yahoo Finance request for all symbols."""
    import yfinance as yf  # imported here so the rest of the module works without it

    return yf.download(
        symbols, period=period, interval="1d", group_by="ticker",
        auto_adjust=True, threads=True, progress=False,
    )


def scan(symbols, period="1y", downloader=download):
    """Returns (rows, missing_symbols)."""
    frame = downloader(symbols, period)
    rows = analyze_frame(frame, symbols) if frame is not None and len(frame) else []
    found = {row["symbol"] for row in rows}
    return rows, [s for s in symbols if s not in found]


SORT_KEYS = {
    "rsi": lambda r: r["rsi"],
    "change": lambda r: r["change_pct"],
    "symbol": lambda r: r["symbol"],
    "high": lambda r: r["from_52w_high_pct"],
}


def select(rows, sort="rsi", descending=False, signals_only=False, top=None):
    """Filter (only OVERSOLD/OVERBOUGHT), sort and cut to the first `top` rows."""
    if sort not in SORT_KEYS:
        raise ValueError(f"Unknown sort '{sort}'. Choose from: {', '.join(SORT_KEYS)}")
    chosen = [r for r in rows if not signals_only or r["signal"] in ("OVERSOLD", "OVERBOUGHT")]
    chosen = sorted(chosen, key=SORT_KEYS[sort], reverse=descending)
    return chosen[:top] if top else chosen


def summary(rows):
    counts = {name: 0 for name in ("OVERSOLD", "OVERBOUGHT", "LOW", "HIGH", "NEUTRAL")}
    for row in rows:
        counts[row["signal"]] += 1
    return counts


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
