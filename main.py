"""
Hugnin | RSI Market Scanner
---------------------------
FA Software - Developer: Anıl
Version: 2.0 (100+ symbol watchlist, trend / 52-week / volume columns, filters, CSV export)
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
RESET = "\033[0m"

BANNER = r"""
  _   _ _   _  ____ _   _ ___ _   _
 | | | | | | |/ ___| \ | |_ _| \ | |
 | |_| | | | | |  _|  \| || ||  \| |
 |  _  | |_| | |_| | |\  || || |\  |
 |_| |_|\___/ \____|_| \_|___|_| \_|
        >>> RSI MARKET SCANNER v2.0 <<<
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Scan 100+ blue-chip stocks and crypto by RSI.")
    parser.add_argument("-g", "--group", default=os.environ.get("HUGNIN_GROUP", "all"),
                        help=f"all, us or one of: {', '.join(watchlist.group_names())} (default: all)")
    parser.add_argument("-s", "--sort", default="rsi", choices=list(scanner.SORT_KEYS))
    parser.add_argument("--desc", action="store_true", help="sort descending")
    parser.add_argument("--signals-only", action="store_true", help="show only OVERSOLD / OVERBOUGHT")
    parser.add_argument("--top", type=int, default=None, help="show only the first N rows")
    parser.add_argument("--csv", metavar="FILE", help="also write the shown rows to a CSV file")
    parser.add_argument("--watch", type=int, metavar="SECONDS", default=0,
                        help="repeat the scan every N seconds (Ctrl+C to stop); default: scan once")
    parser.add_argument("--list-groups", action="store_true", help="print the groups and exit")
    args = parser.parse_args(argv)
    try:
        watchlist.get_symbols(args.group)
    except ValueError as error:
        parser.error(str(error))
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


def run_once(args):
    symbols = watchlist.get_symbols(args.group)
    print(f"{DIM}Scanning {len(symbols)} symbols ({args.group}) at "
          f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ...{RESET}")
    rows, missing = scanner.scan(symbols)
    shown = scanner.select(rows, args.sort, args.desc, args.signals_only, args.top)

    print(format_table(shown) if shown else "No symbols match.")
    counts = scanner.summary(rows)
    print(f"\nScanned {len(rows)}/{len(symbols)}  |  "
          f"{GREEN}oversold {counts['OVERSOLD']}{RESET}  {RED}overbought {counts['OVERBOUGHT']}{RESET}  "
          f"neutral zone {counts['NEUTRAL'] + counts['LOW'] + counts['HIGH']}")
    if missing:
        print(f"{DIM}No data for {len(missing)}: {', '.join(missing[:10])}{'...' if len(missing) > 10 else ''}{RESET}")
    if args.csv:
        scanner.write_csv(shown, args.csv)
        print(f"CSV written: {args.csv}")
    print("Not investment advice. FA Software | Developer: Anıl")
    return len(rows)


def main(argv=None):
    args = parse_args(argv)
    if args.list_groups:
        for name in ["all", "us"] + watchlist.group_names():
            print(f"{name:<22}{len(watchlist.get_symbols(name))} symbols")
        return 0
    print(GREEN + BANNER + RESET)
    try:
        while True:
            scanned = run_once(args)
            if not args.watch:
                return 0 if scanned else 1
            print(f"\nNext scan in {args.watch}s (Ctrl+C to stop)\n")
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nHugnin stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
