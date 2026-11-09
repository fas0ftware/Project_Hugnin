# Hugnin | RSI Market Scanner

> *"Data is merely noise until logic gives it a voice."*

A terminal scanner and Telegram bot that check major assets and flag overbought and oversold conditions using the 14-day Relative Strength Index (RSI).

## ◼ Overview

**Hugnin** analyzes market data and applies a technical indicator, RSI, to spot assets that may be overbought or oversold. It comes in two forms that share the same RSI code (`rsi.py`):

- **Terminal scanner** (`main.py`): a quick, color-coded check from the command line. This is the public demo version.
- **Telegram bot** (`hugnin_bot.py`): sends a signal report to your chat on `/start` or `/scan`.

For a visual, interactive version with charts, see the companion project [Project_Heimdall](https://github.com/fas0ftware/Project_Heimdall).

## ◼ Preview

Telegram bot report:

<img src="docs/telegram_preview.jpeg" alt="Hugnin Telegram bot signal report" width="320">

## ◼ Features

- **Live market data:** Fetches data through the Yahoo Finance library (`yfinance`).
- **RSI analysis:** Calculates the 14-day RSI (Wilder's smoothing) from daily prices. The same method is used in Project_Heimdall, so both projects report the same values.
- **Color-coded terminal output:**
  - RSI below 30: oversold (green)
  - RSI above 70: overbought (red)
  - Everything else is printed in the default color
- **Telegram bot:** Scans a watchlist of crypto, US stocks and Borsa Istanbul stocks and reports only the assets outside the 30 to 70 RSI range.
- **Error handling:** Skips symbols with missing or too little data (for example around market holidays).
- **Demo behavior:** The terminal scanner stops automatically after 5 scans.

## ◼ Project structure

```
Project_Hugnin/
├── main.py                # Terminal scanner (demo)
├── hugnin_bot.py          # Telegram bot
├── rsi.py                 # Shared RSI calculation
├── tests/
│   └── test_rsi.py
├── docs/
│   └── telegram_preview.jpeg
├── requirements.txt       # Terminal scanner dependencies
├── requirements-bot.txt   # Scanner + Telegram bot dependencies
└── .env.example           # Template for the bot token
```

## ◼ Requirements

- Python 3.9 or newer
- pip
- An internet connection (market data is fetched online)
- For the bot: a Telegram bot token from [@BotFather](https://t.me/BotFather)

## ◼ Installation

```bash
git clone https://github.com/fas0ftware/Project_Hugnin.git
cd Project_Hugnin
```

Create and activate a virtual environment.

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies for the terminal scanner:

```bash
pip install -r requirements.txt
```

Or, to also run the Telegram bot:

```bash
pip install -r requirements-bot.txt
```

## ◼ Usage

**Terminal scanner**

```bash
python main.py
```

**Telegram bot**

1. Copy `.env.example` to `.env` and put your own token in it. The `.env` file is ignored by git, so the token stays private.
2. Start the bot:

```bash
python hugnin_bot.py
```

3. Send `/start`, `/scan` or `/analiz` to the bot in Telegram. All three run the same scan.

The bot's watchlist is the `WATCHLIST` list at the top of `hugnin_bot.py`; edit it to track other symbols (use Yahoo Finance symbols, such as `BTC-USD` or `THYAO.IS`).

**Tests**

```bash
python tests/test_rsi.py
```

## ◼ Notes and limitations

- `yfinance` is an unofficial client for Yahoo Finance. Data can be delayed, incomplete or unavailable at times.
- RSI is a single indicator. An oversold or overbought reading is not a buy or sell signal on its own. The bot's "AL" and "SAT" labels only describe the RSI zone.
- The bot scans only when you message it; it does not send scheduled alerts.

## ◼ Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice.

---

Part of the **FA Software** projects.
