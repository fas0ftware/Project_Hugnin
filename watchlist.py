"""Hugnin watchlist: 100+ liquid, well-established symbols in groups (Yahoo Finance symbols).

Edit the groups to track other assets. A symbol that Yahoo does not return data for
is skipped at scan time, so a delisted or renamed ticker never stops a scan.
"""

GROUPS = {
    "us-tech": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "ADBE",
        "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN", "IBM", "NOW", "INTU", "AMAT",
    ],
    "us-finance": [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "V", "MA", "BRK-B", "SCHW",
    ],
    "us-health": [
        "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "BMY", "AMGN", "GILD", "MDT",
    ],
    "us-consumer": [
        "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "KO", "PEP", "PG", "DIS", "NFLX", "TGT", "LOW",
    ],
    "us-industrial": [
        "CAT", "DE", "BA", "HON", "UPS", "GE", "LMT", "RTX", "MMM", "UNP",
    ],
    "us-energy-utilities": [
        "XOM", "CVX", "COP", "SLB", "OXY", "NEE", "DUK", "SO", "T", "VZ", "CMCSA", "LIN",
    ],
    "bist": [
        "THYAO.IS", "ASELS.IS", "GARAN.IS", "EREGL.IS", "AKBNK.IS", "ISCTR.IS", "YKBNK.IS",
        "KCHOL.IS", "SAHOL.IS", "BIMAS.IS", "TUPRS.IS", "SISE.IS", "FROTO.IS", "TOASO.IS",
        "PGSUS.IS", "TCELL.IS", "TTKOM.IS", "ARCLK.IS", "KRDMD.IS", "PETKM.IS", "EKGYO.IS",
        "HEKTS.IS", "TRALT.IS", "ASTOR.IS", "SASA.IS",
    ],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD"],
}


def group_names():
    return list(GROUPS)


def get_symbols(group="all"):
    """Symbols of one group, or every group for 'all' / 'us' (all US groups). No duplicates, order kept."""
    if group == "all":
        selected = [s for names in GROUPS.values() for s in names]
    elif group == "us":
        selected = [s for name, names in GROUPS.items() if name.startswith("us-") for s in names]
    elif group in GROUPS:
        selected = list(GROUPS[group])
    else:
        raise ValueError(f"Unknown group '{group}'. Choose from: all, us, {', '.join(GROUPS)}")
    return list(dict.fromkeys(selected))
