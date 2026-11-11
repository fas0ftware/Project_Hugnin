import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hugnin_bot as bot  # noqa: E402


def row(symbol, signal, rsi=25.0):
    return {"symbol": symbol, "price": 10.0, "change_pct": -1.5, "rsi": rsi, "signal": signal,
            "trend": "DOWN", "from_52w_high_pct": -20.0, "volume_ratio": 1.1}


def test_parse_allowed():
    assert bot.parse_allowed("123, -100456,abc,, 7") == {123, -100456, 7}
    assert bot.parse_allowed(None) == set() and bot.parse_allowed("") == set()


def test_report_escapes_html_and_lists_only_signals():
    rows = [row("<b>X</b>", "OVERSOLD", 20), row("AAPL", "NEUTRAL", 50), row("BTC-USD", "OVERBOUGHT", 80)]
    text = bot.build_report(rows, "all", 3, 3)
    assert "&lt;b&gt;X&lt;/b&gt;" in text and "<b>X</b>" not in text
    assert "AAPL" not in text and "BTC-USD" in text
    assert text.index("OVERSOLD") < text.index("OVERBOUGHT")  # sorted by RSI


def test_report_when_calm():
    assert "Market is calm" in bot.build_report([row("AAPL", "NEUTRAL", 50)], "us", 1, 1)


def test_chunk_message_respects_limit_and_keeps_blocks():
    blocks = [f"block {i} " + "x" * 50 for i in range(200)]
    text = "\n\n".join(blocks)
    parts = bot.chunk_message(text, limit=500)
    assert all(len(p) <= 500 for p in parts)
    assert "\n\n".join(parts) == text
    huge = "\n".join("line" * 10 for _ in range(100))
    assert all(len(p) <= 300 for p in bot.chunk_message(huge, limit=300))


def test_cooldown():
    now = [1000.0]
    cd = bot.Cooldown(60, clock=lambda: now[0])
    assert cd.hit(1) and not cd.hit(1) and cd.hit(2)
    now[0] += 30
    assert cd.remaining(1) == pytest.approx(30)
    now[0] += 31
    assert cd.hit(1)


def test_resolve_group():
    assert bot.resolve_group([], "all") == "all"
    assert bot.resolve_group(["BIST"], "all") == "bist"
    with pytest.raises(ValueError):
        bot.resolve_group(["nope"], "all")


def test_help_text_lists_commands():
    for cmd in ("/scan", "/subscribe", "/unsubscribe", "/groups", "/help"):
        assert cmd in bot.__doc__


def test_app_builds_with_handlers():
    pytest.importorskip("telegram")
    app = bot.build_app("123456:TEST-TOKEN-NOT-REAL", {1}, "all")
    names = {c for h in app.handlers[0] for c in h.commands}
    assert {"start", "help", "scan", "analiz", "groups", "subscribe", "unsubscribe"} <= names
    assert app.job_queue is not None
