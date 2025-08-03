import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime
# === SETTINGS ===
# symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]  # Add more symbols as needed
interval = "15m"
period = "1d"

# -- List of F&O stocks to analyze --
file_path = "../darvas-box.txt"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

with open(file_path, "r") as file:
    symbols = [line.strip() for line in file if line.strip()]

print("✅ Symbols loaded:", symbols) # Add more if needed




for symbol in symbols:
    print(f"\n📊 Fetching intraday data for {symbol} ({interval}, {period})...")

    # === DOWNLOAD DATA ===
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"❌ Error downloading data for {symbol}: {e}")
        continue

    if df.empty:
        print("❌ No data returned.")
        continue

    # === VALIDATE 'Close' column ===
    if 'Close' not in df.columns or df['Close'].dropna().empty:
        print("❌ 'Close' prices missing or all NaN.")
        continue

    # === CALCULATE EMAs ===
    df['EMA5'] = df['Close'].ewm(span=5).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()

    # === SAFELY CHECK EMA COLUMNS ===
    if not set(['EMA5', 'EMA20']).issubset(df.columns):
        print("❌ EMA columns not created.")
        continue

    if df[['EMA5', 'EMA20']].dropna().empty:
        print("❌ EMA values are all NaN.")
        continue

    # === DROP ROWS WHERE EMAs ARE NaN ===
    df = df.dropna(subset=['EMA5', 'EMA20'])

    if df.empty:
        print("❌ Dataframe became empty after dropping NaNs.")
        continue

    # === SIGNAL LOGIC ===
    df['Signal'] = np.where(df['EMA5'] > df['EMA20'], 1, -1)
    df['Crossover'] = df['Signal'].diff()

    crossovers = df[df['Crossover'].abs() == 2]

    # === ICON OUTPUT ===
    if crossovers.empty:
        print("⚠️ No Golden or Death Crossovers found.")
    else:
        print("🔁 Detected Crossovers (latest last):")
        for idx, row in crossovers.iterrows():
            ts = idx.strftime('%Y-%m-%d %H:%M')
            if row['Crossover'] == 2:
                print(f"{ts} 🟢 Golden Cross (EMA5 ↑ EMA20)")
            elif row['Crossover'] == -2:
                print(f"{ts} 🔴 Death Cross (EMA5 ↓ EMA20)")
