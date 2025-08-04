import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

# --- Input file for symbols ---
file_path = "../darvas-box.txt"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

with open(file_path, "r") as file:
    symbols = [line.strip() for line in file if line.strip()]

print("✅ Symbols loaded:", symbols)

# --- Output directory ---
output_dir = "../data"
os.makedirs(output_dir, exist_ok=True)

# --- Parameters ---
lookback_days = 90
box_length = 5          # days to confirm a high/low
buffer_pct = 1.5        # Pre-breakout buffer range
stop_loss_pct = 3       # Backtest use only

# --- Fetch OHLCV data ---
def get_data(symbol, days):
    end = datetime.now()
    start = end - timedelta(days=days)
    return yf.download(symbol, start=start, end=end, auto_adjust=False)

# --- Detect Darvas boxes ---
def find_darvas_boxes(df, box_length=5):
    highs = df['High'].rolling(window=box_length).max()
    lows = df['Low'].rolling(window=box_length).min()

    boxes = []
    for i in range(box_length, len(df)):
        recent_highs = df['High'].iloc[i - box_length:i]
        recent_lows = df['Low'].iloc[i - box_length:i]
        box_high = highs.iloc[i - 1]
        box_low = lows.iloc[i - 1]

        if all(recent_highs <= box_high) and all(recent_lows >= box_low):
            boxes.append((df.index[i], box_low, box_high))

    return boxes

# --- Signal Detection ---
def check_breakout(df, boxes, buffer_pct=1.0):
    if not boxes:
        return "No", None, None, None

    _, box_low, box_high = boxes[-1]

    last_close = df['Close'].iloc[-1]
    last_close = float(last_close)

    box_high = float(box_high)
    buffer_price = box_high * (1 - buffer_pct / 100)

    if last_close >= box_high:
        return "Confirmed", last_close, box_high, box_low
    elif last_close >= buffer_price:
        return "Pre-breakout", last_close, box_high, box_low
    else:
        return "No", last_close, box_high, box_low

# --- Run Screener ---
def run_screener(symbols):
    results = []

    for symbol in symbols:
        df = get_data(symbol, lookback_days)
        if df.empty or len(df) < box_length:
            print(f"⚠️ Skipping {symbol} (insufficient data)")
            continue

        boxes = find_darvas_boxes(df, box_length)
        signal_type, price, box_high, box_low = check_breakout(df, boxes, buffer_pct)

        if signal_type in ["Pre-breakout", "Confirmed"]:
            results.append({
                'Symbol': symbol,
                'Close': round(float(price), 2),
                'Box High': round(float(box_high), 2),
                'Box Low': round(float(box_low), 2),
                'Signal': "✅ Confirmed breakout" if signal_type == "Confirmed" else "🔼 Pre-breakout"
            })


    return pd.DataFrame(results)

# --- Run script ---
if __name__ == "__main__":
    df_results = run_screener(symbols)

    if not df_results.empty:
        print("\n📊 Darvas Box Screener Signals:")
        print(df_results)

        output_path = os.path.join(output_dir, "darvas_breakouts.json")
        # Convert any Series or numpy types to plain Python types
        records = json.loads(df_results.to_json(orient="records"))

        with open(output_path, "w") as f:
            json.dump(records, f, indent=2)

        print(f"\n✅ Saved to {output_path}")
    else:
        print("❌ No breakout signals found today.")
