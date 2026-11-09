"""
Hugnin | RSI Market Scanner (demo version)
------------------------------------------
FA Software - Developer: Anıl
Version: 1.5 (shared Wilder RSI, colored output, demo limit)
"""

import sys
import time
from datetime import datetime

import yfinance as yf

from rsi import OVERBOUGHT_LEVEL, OVERSOLD_LEVEL, RSI_PERIOD, latest_rsi

# --- AYARLAR ---
WATCHLIST = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD", "COIN"]
DEMO_LIMIT = 5  # Bot kaç tur çalışıp kapansın? (5 tur idealdir)

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header():
    print(GREEN)
    print(r"""
  _   _ _   _  ____ _   _ ___ _   _
 | | | | | | |/ ___| \ | |_ _| \ | |
 | |_| | | | | |  _|  \| || ||  \| |
 |  _  | |_| | |_| | |\  || || |\  |
 |_| |_|\___/ \____|_| \_|___|_| \_|
     >>> RSI MARKET SCANNER v1.5 (DEMO) <<<
    """)
    print(RESET)


def fetch_rsi(ticker):
    """Returns (rsi, last_price) for a ticker, or (None, 0) when data is missing."""
    try:
        # Period 1y: Garanti veri
        df = yf.Ticker(ticker).history(period="1y", interval="1d")

        if df.empty:
            return None, 0

        rsi = latest_rsi(df['Close'], RSI_PERIOD)
        if rsi is None:
            return None, 0

        return rsi, df['Close'].iloc[-1]

    except Exception:
        return None, 0


def analyze_market():
    print("-" * 75)
    print(f"🕒 TARAMA ZAMANI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 75)
    print(f"{'SEMBOL':<10} {'FİYAT ($)':<12} {'RSI':<10} {'DURUM / SİNYAL'}")
    print("-" * 75)

    for symbol in WATCHLIST:
        rsi, price = fetch_rsi(symbol)

        if rsi is None:
            continue

        signal = "Nötr"
        icon = "⚪"
        color = ""

        if rsi < OVERSOLD_LEVEL:
            signal = "AŞIRI SATIM"
            icon = "🟢"
            color = GREEN
        elif rsi > OVERBOUGHT_LEVEL:
            signal = "AŞIRI ALIM"
            icon = "🔴"
            color = RED
        elif OVERSOLD_LEVEL <= rsi < 45:
            signal = "Düşük Bölge"
            icon = "📉"
        elif 55 < rsi <= OVERBOUGHT_LEVEL:
            signal = "Yüksek Bölge"
            icon = "📈"

        print(f"{color}{symbol:<10} {price:<12.2f} {rsi:<10.1f} {icon} {signal}{RESET}")
        time.sleep(0.2)

    print("-" * 75)
    print("\n")


if __name__ == "__main__":
    try:
        print_header()
        print(f"Sistem başlatılıyor... (Demo Modu: {DEMO_LIMIT} Tarama ile sınırlıdır)")
        time.sleep(2)

        loop_count = 0

        while loop_count < DEMO_LIMIT:
            loop_count += 1
            print(f"🔄 Döngü: {loop_count}/{DEMO_LIMIT}")

            analyze_market()

            # Son turdaysa beklemeye gerek yok, direkt bitir
            if loop_count == DEMO_LIMIT:
                break

            for i in range(10, 0, -1):  # Demo olduğu için bekleme süresi 10 sn
                sys.stdout.write(f"\r⏳ Sıradaki tarama: {i} sn...   ")
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\r" + " " * 40 + "\r")

        # --- KAPANIŞ MESAJI ---
        print("\n" + "=" * 50)
        print("✅ DEMO SÜRECİ BAŞARIYLA TAMAMLANDI.")
        print("💡 Bu sadece bir önizlemedir (Preview).")
        print("🦅 FA Software | Developer: Anıl")
        print("=" * 50 + "\n")

    except KeyboardInterrupt:
        print("\n\n🦅 Hugnin kullanıcı tarafından kapatıldı.")
