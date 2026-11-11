import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402
import scanner  # noqa: E402
import watchlist  # noqa: E402


def rising(n=260, start=100.0):
    return pd.Series(start + np.arange(n, dtype=float))


def falling(n=260, start=400.0):
    return pd.Series(start - np.arange(n, dtype=float))


def choppy(n=260):
    return pd.Series(100 + np.sin(np.arange(n) / 3.0) * 2)


def make_frame(series_by_symbol, volume=1000.0):
    columns = {}
    for symbol, close in series_by_symbol.items():
        columns[(symbol, "Close")] = close
        columns[(symbol, "Volume")] = pd.Series([volume] * len(close))
    return pd.DataFrame(columns)


# --- watchlist ---
def test_watchlist_has_at_least_100_unique_symbols():
    symbols = watchlist.get_symbols("all")
    assert len(symbols) >= 100
    assert len(symbols) == len(set(symbols))


def test_watchlist_groups_and_errors():
    assert set(watchlist.get_symbols("crypto")) <= set(watchlist.get_symbols("all"))
    assert all(not s.endswith(".IS") for s in watchlist.get_symbols("us"))
    assert all(s.endswith(".IS") for s in watchlist.get_symbols("bist"))
    try:
        watchlist.get_symbols("nope")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown group must raise")


# --- analysis ---
def test_classify_levels():
    assert scanner.classify(10) == "OVERSOLD"
    assert scanner.classify(29.9) == "OVERSOLD"
    assert scanner.classify(30) == "LOW"
    assert scanner.classify(50) == "NEUTRAL"
    assert scanner.classify(60) == "HIGH"
    assert scanner.classify(70) == "HIGH"
    assert scanner.classify(70.1) == "OVERBOUGHT"


def test_rising_series_is_overbought_uptrend_at_high():
    row = scanner.analyze_symbol("UP", rising(), pd.Series([1000.0] * 260))
    assert row["signal"] == "OVERBOUGHT"
    assert row["trend"] == "UP/long-UP"
    assert row["from_52w_high_pct"] == 0.0
    assert row["change_pct"] > 0
    assert row["volume_ratio"] == 1.0


def test_falling_series_is_oversold_downtrend():
    row = scanner.analyze_symbol("DN", falling())
    assert row["signal"] == "OVERSOLD"
    assert row["trend"] == "DOWN/long-DOWN"
    assert row["from_52w_high_pct"] < 0
    assert row["volume_ratio"] is None


def test_too_little_data_returns_none():
    assert scanner.analyze_symbol("X", rising(10)) is None
    assert scanner.analyze_symbol("X", pd.Series([np.nan] * 40)) is None


def test_short_history_has_no_trend():
    assert scanner.analyze_symbol("S", rising(30))["trend"] == "n/a"


def test_analyze_frame_skips_missing_and_empty_symbols():
    frame = make_frame({"A": rising(), "B": falling()})
    frame[("C", "Close")] = pd.Series([np.nan] * 260)
    frame[("C", "Volume")] = pd.Series([np.nan] * 260)
    rows = scanner.analyze_frame(frame, ["A", "B", "C", "MISSING"])
    assert [r["symbol"] for r in rows] == ["A", "B"]


def test_analyze_frame_single_symbol_download():
    frame = pd.DataFrame({"Close": rising(), "Volume": [1000.0] * 260})
    rows = scanner.analyze_frame(frame, ["ONLY"])
    assert len(rows) == 1 and rows[0]["symbol"] == "ONLY"


def test_scan_reports_missing_symbols():
    frame = make_frame({"A": rising(), "B": choppy()})
    rows, missing = scanner.scan(["A", "B", "ZZZ"], downloader=lambda symbols, period: frame)
    assert len(rows) == 2 and missing == ["ZZZ"]


def test_scan_handles_empty_download():
    rows, missing = scanner.scan(["A"], downloader=lambda symbols, period: pd.DataFrame())
    assert rows == [] and missing == ["A"]


# --- selection / output ---
def sample_rows():
    frame = make_frame({"UP": rising(), "DN": falling(), "MID": choppy()})
    return scanner.analyze_frame(frame, ["UP", "DN", "MID"])


def test_select_sort_filter_top():
    rows = sample_rows()
    assert [r["symbol"] for r in scanner.select(rows, "rsi")][0] == "DN"
    assert [r["symbol"] for r in scanner.select(rows, "rsi", descending=True)][0] == "UP"
    assert {r["symbol"] for r in scanner.select(rows, signals_only=True)} == {"UP", "DN"}
    assert len(scanner.select(rows, top=1)) == 1
    try:
        scanner.select(rows, sort="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown sort must raise")


def test_summary_counts():
    counts = scanner.summary(sample_rows())
    assert counts["OVERSOLD"] == 1 and counts["OVERBOUGHT"] == 1 and sum(counts.values()) == 3


def test_csv_roundtrip():
    rows = sample_rows()
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "out.csv")
        scanner.write_csv(rows, path)
        lines = open(path, encoding="utf-8").read().strip().splitlines()
    assert lines[0].split(",") == scanner.FIELDS
    assert len(lines) == 4


# --- CLI ---
def test_cli_parse_args():
    args = main.parse_args(["-g", "bist", "--top", "5", "--signals-only"])
    assert args.group == "bist" and args.top == 5 and args.signals_only
    for bad in (["-g", "nope"], ["--top", "0"], ["--watch", "-1"]):
        try:
            main.parse_args(bad)
        except SystemExit:
            continue
        raise AssertionError(f"{bad} must be rejected")


def test_cli_table_contains_every_row():
    table = main.format_table(sample_rows())
    for symbol in ("UP", "DN", "MID"):
        assert symbol in table



# --- v3 -------------------------------------------------------------------------

import json  # noqa: E402

import pytest  # noqa: E402


def test_parse_symbols():
    assert scanner.parse_symbols("aapl, msft  btc-usd;THYAO.IS ^gspc aapl") == \
        ["AAPL", "MSFT", "BTC-USD", "THYAO.IS", "^GSPC"]
    for bad in ("", " , ", "AAPL;rm -rf /", "<b>", "A" * 30):
        with pytest.raises(ValueError):
            scanner.parse_symbols(bad)


def test_custom_levels_change_the_signal():
    assert scanner.classify(35) == "LOW"
    assert scanner.classify(35, oversold=40, overbought=60) == "OVERSOLD"
    assert scanner.classify(65, oversold=40, overbought=60) == "OVERBOUGHT"


def test_rsi_period_is_passed_through():
    close = choppy(60)
    a = scanner.analyze_symbol("X", close, rsi_period=14)
    b = scanner.analyze_symbol("X", close, rsi_period=5)
    assert a["rsi"] != b["rsi"]
    assert scanner.analyze_symbol("X", choppy(20), rsi_period=30) is None


def test_new_signals_only_reports_changes():
    prev = [{"symbol": "A", "signal": "OVERSOLD"}, {"symbol": "B", "signal": "NEUTRAL"},
            {"symbol": "C", "signal": "OVERBOUGHT"}]
    now = [{"symbol": "A", "signal": "OVERSOLD"}, {"symbol": "B", "signal": "OVERBOUGHT"},
           {"symbol": "C", "signal": "OVERSOLD"}, {"symbol": "D", "signal": "LOW"},
           {"symbol": "E", "signal": "OVERSOLD"}]
    assert [r["symbol"] for r in scanner.new_signals(prev, now)] == ["B", "C", "E"]
    assert [r["symbol"] for r in scanner.new_signals(None, now)] == ["A", "B", "C", "E"]


def test_json_export(tmp_path):
    path = tmp_path / "out.json"
    scanner.write_json(sample_rows(), str(path))
    assert json.loads(path.read_text(encoding="utf-8"))[0]["symbol"] == sample_rows()[0]["symbol"]


def fake_downloader(symbols, period):
    return make_frame({"UPP": rising(), "DWN": falling(), "MID": choppy()})


def test_cli_end_to_end_with_fake_data(tmp_path, capsys):
    out_csv, out_json = tmp_path / "r.csv", tmp_path / "r.json"
    code = main.main(["--symbols", "UPP,DWN,MID,GONE", "--csv", str(out_csv), "--json", str(out_json),
                      "--no-color"], downloader=fake_downloader)
    text = capsys.readouterr().out
    assert code == 0
    assert "UPP" in text and "OVERBOUGHT" in text and "OVERSOLD" in text
    assert "No data for 1: GONE" in text and "\033[" not in text
    assert len(json.loads(out_json.read_text())) == 3 and out_csv.exists()


def test_cli_validates_settings():
    for bad in (["--rsi-period", "1"], ["--oversold", "80"], ["--oversold", "40", "--overbought", "40"],
                ["--symbols", "bad symbol!"]):
        with pytest.raises(SystemExit):
            main.parse_args(bad)


def test_watch_mode_prints_new_signals_once(capsys, monkeypatch):
    calls = {"n": 0}

    def sleeper(_):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(main.time, "sleep", sleeper)
    assert main.main(["--symbols", "UPP,DWN", "--watch", "1", "--no-color"], downloader=fake_downloader) == 0
    out = capsys.readouterr().out
    assert out.count("No new signals since the last scan.") == 1  # second scan: nothing new
    assert "Hugnin stopped." in out
