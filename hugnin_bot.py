import os
import logging
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

import scanner
import watchlist

# --- AYARLAR ---
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("HATA: .env dosyasında TELEGRAM_TOKEN bulunamadı!")

# Tarama listesi watchlist.py içinde (gruplar). Bot grubu .env'deki HUGNIN_GROUP ile seçilir (varsayılan: all).
GROUP = os.getenv("HUGNIN_GROUP", "all")

# Loglama
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ANALİZ MOTORU ---
def format_signal(row):
    if row["signal"] == "OVERSOLD":
        title = "🟢 **AL (Oversold)**"
    else:
        title = "🔴 **SAT (Overbought)**"
    return (f"{title} | {row['symbol']}\n"
            f"   └ Fiyat: {row['price']:.2f} ({row['change_pct']:+.2f}%) | RSI: {row['rsi']:.1f} | Trend: {row['trend']}")


def analyze_market():
    """Piyasayı tek toplu istekle tarar ve AL/SAT sinyallerini metin olarak döndürür."""
    rows, _missing = scanner.scan(watchlist.get_symbols(GROUP))
    flagged = scanner.select(rows, sort="rsi", signals_only=True)
    return [format_signal(row) for row in flagged]


# --- BOT KOMUTLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başladığında otomatik tarama yapar."""
    user = update.effective_user.first_name
    await update.message.reply_text(f"Merhaba {user}! 🦅\n\nPiyasa taranıyor, fırsatlar analiz ediliyor...")
    
    # Analizi çalıştır
    loop = asyncio.get_event_loop()
    signals = await loop.run_in_executor(None, analyze_market)
    
    if signals:
        report = "🚨 **ACİL SİNYAL RAPORU** 🚨\n\n" + "\n\n".join(signals)
        report += "\n\n_Bu bir yatırım tavsiyesi değildir, algoritma çıktısıdır._"
    else:
        report = "✅ **Piyasa Sakin.**\nŞu an aşırı alım veya satım bölgesinde (RSI 30-70 dışı) hisse/coin yok."
        
    await update.message.reply_text(report, parse_mode=constants.ParseMode.MARKDOWN)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manuel tarama komutu."""
    await start(update, context)

# --- BAŞLATMA ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("analiz", scan)) # Türkçesi de olsun
    
    print("Hugnin Sinyal Botu Aktif... 🚀")
    app.run_polling()