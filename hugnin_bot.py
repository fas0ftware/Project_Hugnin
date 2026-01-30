import os
import logging
import yfinance as yf
import pandas as pd
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

# --- AYARLAR ---
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("HATA: .env dosyasında TELEGRAM_TOKEN bulunamadı!")

# Tarama Listesi (İstediğini ekle/çıkar)
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
    "AAPL", "TSLA", "NVDA", "AMZN", "GOOGL",
    "THYAO.IS", "ASELS.IS", "GARAN.IS", "EREGL.IS"
]

# Loglama
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- ANALİZ MOTORU ---
def analyze_market():
    """Piyasayı tarar ve AL/SAT sinyallerini metin olarak döndürür."""
    signals = []
    
    for symbol in WATCHLIST:
        try:
            # Sadece son 3 aylık veriyi çek (Hız için yeterli)
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="3mo")
            
            if data.empty:
                continue

            # RSI Hesaplama (Manuel Formül)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            current_price = data['Close'].iloc[-1]
            
            # --- KARAR MEKANİZMASI ---
            # RSI 30'un altındaysa AL, 70'in üstündeyse SAT
            if current_rsi < 30:
                signals.append(f"🟢 **AL (Oversold)** | {symbol}\n   └ Fiyat: {current_price:.2f} | RSI: {current_rsi:.1f}")
            elif current_rsi > 70:
                signals.append(f"🔴 **SAT (Overbought)** | {symbol}\n   └ Fiyat: {current_price:.2f} | RSI: {current_rsi:.1f}")
                
        except Exception as e:
            print(f"Hata ({symbol}): {e}")
            continue

    return signals

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