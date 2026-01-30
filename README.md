# 🦅 Aesthesius Project Hugnin

> **"Data is merely noise until logic gives it a voice."**

**Hugnin** is an algorithmic financial intelligence tool developed to analyze stock market data in real-time. Unlike simple price trackers, this system applies technical analysis indicators (specifically **RSI**) to identify potential "Overbought" or "Oversold" conditions for major assets.

![Build Status](https://img.shields.io/badge/Build-Passing-success)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Ecosystem](https://img.shields.io/badge/Aesthesius-Core-black)

## 🔮 Project Vision

In the volatile world of finance, timing is everything. This tool was architected by **Anıl** to automate the detection of market opportunities. It acts as a "Digital Sentinel," scanning the Nasdaq and NYSE exchanges to filter signal from noise.

The current repository hosts the **Demo / Public Version** of the Aesthesius Private Core system.

## ⚡ Key Features

* **Real-Time Data Acquisition:** Fetches live market data using the Yahoo Finance API (`yfinance`).
* **Algorithmic Analysis:** Automatically calculates the **14-Day Relative Strength Index (RSI)** based on 1-year historical data.
* **Visual Dashboard:** A clean, color-coded terminal interface that highlights opportunities:
    * 🟢 **RSI < 30:** Oversold (Potential Buy Opportunity)
    * 🔴 **RSI > 70:** Overbought (Potential Sell Risk)
* **Smart Error Handling:** Robust logic to handle missing data or market holidays.
* **Demo Protocol:** Includes an automatic termination sequence for demonstration purposes.

