# Hugnin | RSI Market Scanner

> *"Data is merely noise until logic gives it a voice."*

A terminal tool that scans major stocks and flags overbought and oversold conditions using the 14-day Relative Strength Index (RSI).

## ◼ Overview

**Hugnin** analyzes stock market data and applies a technical indicator, RSI, to spot assets that may be overbought or oversold. It is built for quick checks from the terminal.

This repository contains the **public demo version**. For a visual, interactive version with charts, see the companion project [Project_Heimdall](https://github.com/fas0ftware/Project_Heimdall).

## ◼ Features

- **Live market data:** Fetches data through the Yahoo Finance library (`yfinance`).
- **RSI analysis:** Calculates the 14-day RSI from one year of price history.
- **Color-coded terminal output:**
  - RSI below 30: oversold (green)
  - RSI above 70: overbought (red)
- **Error handling:** Copes with missing data and market holidays.
- **Demo behavior:** The public version includes an automatic termination step for demonstration purposes.

## ◼ Project structure

```
Project_Hugnin/
├── main.py
├── hugnin_bot.py
└── requirements.txt   # Dependencies
```

## ◼ Requirements

- Python 3.9 or newer
- pip
- An internet connection (market data is fetched online)

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

Install dependencies:

```bash
pip install -r requirements.txt
```

## ◼ Usage

```bash
python main.py
```

## ◼ Notes and limitations

- `yfinance` is an unofficial client for Yahoo Finance. Data can be delayed, incomplete or unavailable at times.
- RSI is a single indicator. An oversold or overbought reading is not a buy or sell signal on its own.

## ◼ Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice.

---

Part of the **FA Software** projects.
