import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rsi import calculate_rsi_series, latest_rsi  # noqa: E402


def test_all_gains_is_100():
    assert latest_rsi(pd.Series(range(1, 40), dtype=float)) == 100


def test_all_losses_is_0():
    assert latest_rsi(pd.Series(range(40, 1, -1), dtype=float)) < 1e-9


def test_too_little_data_returns_none():
    assert latest_rsi(pd.Series(range(1, 10), dtype=float)) is None


def test_warmup_is_nan():
    rsi = calculate_rsi_series(pd.Series(range(1, 40), dtype=float))
    assert rsi.iloc[:14].isna().all()


def test_stays_in_range():
    prices = pd.Series([10, 11, 10.5, 12, 11.8, 13, 12.2, 12.9, 11, 10, 9.5, 10.2,
                        11.1, 12.4, 12.0, 13.3, 12.7, 13.9, 14.2, 13.1], dtype=float)
    rsi = calculate_rsi_series(prices).dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
