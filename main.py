"""
Hugnin | RSI Market Scanner
---------------------------
FA Software - Developer: Anıl
Version: 3.0 (custom symbols, tunable RSI, JSON export, new-signal alerts in watch mode)
"""

import argparse
import os
import sys
import time
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import scanner
import watchlist

GREEN = "\033[92m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

__version__ = "3.0.0"

BANNER = r"""
  _   _ _   _  ____ _   _ ___ _   _
 | | | | | | |/ ___| \ | |_ _| \ | |
 | |_| | | | | |  _|  \| || ||  \| |
 |  _  | |_| | |_| | |\  || || |\  |
 |_| |_|\___/ \____|_| \_|___|_| \_|
        >>> RSI MARKET SCANNER v3.0 <<<
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Scan 100+ blue-chip stocks and crypto by RSI.")
    parser.add_argument("-g", "--group", default=os.environ.get("HUGNIN_GROUP", "all"),
                        help=f"all, us or one of: {', '.join(watchlist.group_names())} (default: all)")
    parser.add_argument("--symbols", metavar="LIST",
                        help="scan these symbols instead of a group, e.g. 'AAPL,MSFT,THYAO.IS,BTC-USD'")
    parser.add_argument("-s", "--sort", default="rsi", choices=list(scanner.SORT_KEYS))
    parser.add_argument("--desc", action="store_true", help="sort descending")
    parser.add_argument("--signals-only", action="store_true", help="show only OVERSOLD / OVERBOUGHT")
    parser.add_argument("--top", type=int, default=None, help="show only the first N rows")
    parser.add_argument("--csv", metavar="FILE", help="also write the shown rows to a CSV file")
    parser.add_argument("--json", metavar="FILE", help="also write the shown rows to a JSON file")
    parser.add_argument("--rsi-period", type=int, default=scanner.RSI_PERIOD, help="RSI length (default 14)")
    parser.add_argument("--oversold", type=float, default=scanner.OVERSOLD_LEVEL, help="oversold level (default 30)")
    parser.add_argument("--overbought", type=float, default=scanner.OVERBOUGHT_LEVEL,
                        help="overbought level (default 70)")
    parser.add_argument("--no-color", action="store_true", help="plain output (also when NO_COLOR is set)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--watch", type=int, metavar="SECONDS", default=0,
                        help="repeat the scan every N seconds (Ctrl+C to stop); default: scan once")
    parser.add_argument("--list-groups", action="store_true", help="print the groups and exit")
    args = parser.parse_args(argv)
    try:
        args.symbol_list = (scanner.parse_symbols(args.symbols) if args.symbols
                            else watchlist.get_symbols(args.group))
    except ValueError as error:
        parser.error(str(error))
    if not 2 <= args.rsi_period <= 100:
        parser.error("--rsi-period must be between 2 and 100")
    if not 0 < args.oversold < args.overbought < 100:
        parser.error("levels must satisfy 0 < oversold < overbought < 100")
    if args.top is not None and args.top < 1:
        parser.error("--top must be at least 1")
    if args.watch < 0:
        parser.error("--watch must not be negative")
    return args


def color_for(signal):
    return {"OVERSOLD": GREEN, "OVERBOUGHT": RED}.get(signal, "")


def format_table(rows):
    """Plain-text table (with ANSI colors for the two signal states)."""
    header = f"{'SYMBOL':<10}{'PRICE':>12}{'CHG %':>8}{'RSI':>7}  {'SIGNAL':<11}{'TREND':<14}{'vs 52W HIGH':>12}{'VOL x':>7}"
    lines = [header, "-" * len(header)]
    for r in rows:
        volume = "-" if r["volume_ratio"] is None else f"{r['volume_ratio']:.2f}"
        line = (f"{r['symbol']:<10}{r['price']:>12.2f}{r['change_pct']:>+8.2f}{r['rsi']:>7.1f}  "
                f"{r['signal']:<11}{r['trend']:<14}{r['from_52w_high_pct']:>11.1f}%{volume:>7}")
        color = color_for(r["signal"])
        lines.append(f"{color}{line}{RESET}" if color else line)
    return "\n".join(lines)


def settings(args):
    return {"rsi_period": args.rsi_period, "oversold": args.oversold, "overbought": args.overbought}


def run_once(args, previous=None, downloader=scanner.download):
    symbols = args.symbol_list
    source = "custom list" if args.symbols else args.group
    print(f"{DIM}Scanning {len(symbols)} symbols ({source}) at "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ...{RESET}")
    rows, missing = scanner.scan(symbols, downloader=downloader, **settings(args))
    shown = scanner.select(rows, args.sort, args.desc, args.signals_only, args.top)

    print(format_table(shown) if shown else "No symbols match.")
    counts = scanner.summary(rows)
    print(f"\nScanned {len(rows)}/{len(symbols)}  |  "
          f"{GREEN}oversold {counts['OVERSOLD']}{RESET}  {RED}overbought {counts['OVERBOUGHT']}{RESET}  "
          f"neutral zone {counts['NEUTRAL'] + counts['LOW'] + counts['HIGH']}")
    if missing:
        print(f"{DIM}No data for {len(missing)}: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}{RESET}")
    if previous is not None:
        fresh = scanner.new_signals(previous, rows)
        for r in fresh:
            print(f"{BOLD}{color_for(r['signal'])}NEW {r['signal']}: {r['symbol']} "
                  f"(RSI {r['rsi']:.1f}, {r['price']:.2f}){RESET}")
        if not fresh:
            print(f"{DIM}No new signals since the last scan.{RESET}")
    if args.csv:
        scanner.write_csv(shown, args.csv)
        print(f"CSV written: {args.csv}")
    if args.json:
        scanner.write_json(shown, args.json)
        print(f"JSON written: {args.json}")
    print("Not investment advice. FA Software | Developer: Anıl")
    return rows


def disable_colors():
    global GREEN, RED, DIM, BOLD, RESET
    GREEN = RED = DIM = BOLD = RESET = ""


def main(argv=None, downloader=scanner.download):
    args = parse_args(argv)
    if args.no_color or os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        disable_colors()
    if args.list_groups:
        for name in ["all", "us"] + watchlist.group_names():
            print(f"{name:<22}{len(watchlist.get_symbols(name))} symbols")
        return 0
    print(GREEN + BANNER + RESET)
    previous = None
    try:
        while True:
            rows = run_once(args, previous, downloader)
            if not args.watch:
                return 0 if rows else 1
            previous = rows
            print(f"\nNext scan in {args.watch}s (Ctrl+C to stop)\n")
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nHugnin stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
