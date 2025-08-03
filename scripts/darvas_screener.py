import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
# List of stock symbols (use NSE symbols like "RELIANCE.NS" or US like "AAPL")
# symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS", "SBIN.NS", "TATAMOTORS.NS", "MARUTI.NS"]

# -- List of F&O stocks to analyze --
file_path = "../darvas-box.txt"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

with open(file_path, "r") as file:
    symbols = [line.strip() for line in file if line.strip()]

print("✅ Symbols loaded:", symbols) # Add more if needed

# -- Output directory --
output_dir = "../data"
os.makedirs(output_dir, exist_ok=True)

# Parameters
lookback_days = 90
box_length = 5  # days to confirm a high/low
buffer_pct = 1.0  # price within X% of box high = potential breakout

def get_data(symbol, days):
    end = datetime.now()
    start = end - timedelta(days=days)
    return yf.download(symbol, start=start, end=end, auto_adjust=False)


def find_darvas_boxes(df, box_length=5):
    highs = df['High'].rolling(window=box_length).max()
    lows = df['Low'].rolling(window=box_length).min()

    boxes = []
    for i in range(box_length, len(df)):
        box_high = highs.iloc[i - 1]
        box_low = lows.iloc[i - 1]

        recent_highs = df['High'].iloc[i - box_length:i]
        recent_lows = df['Low'].iloc[i - box_length:i]

        if all(recent_highs <= box_high) and all(recent_lows >= box_low):
            boxes.append((df.index[i], box_low, box_high))

    return boxes


def check_breakout(df, boxes, buffer_pct=1.0):
    if not boxes:
        return False, None, None

    last_box_date, box_low, box_high = boxes[-1]

    # Ensure both are scalar floats
    last_close = df['Close'].iloc[-1]
    if isinstance(last_close, (pd.Series, np.ndarray)):
        last_close = last_close.iloc[0] if isinstance(last_close, pd.Series) else last_close[0]
    last_close = float(last_close)

    if isinstance(box_high, (pd.Series, np.ndarray)):
        box_high = box_high.iloc[0] if isinstance(box_high, pd.Series) else box_high[0]
    box_high = float(box_high)

    # Breakout condition
    if last_close >= box_high * (1 - buffer_pct / 100):
        return True, last_close, box_high
    return False, last_close, box_high




def run_screener(symbols):
    results = []

    for symbol in symbols:
        df = get_data(symbol, lookback_days)
        if df.empty:
            print(f"No data for {symbol}")
            continue

        boxes = find_darvas_boxes(df, box_length)
        breakout, price, box_high = check_breakout(df, boxes, buffer_pct)

        if breakout:
            results.append({
                'Symbol': symbol,
                'Close': round(price, 2),
                'Box High': round(box_high, 2),
                'Signal': '🔼 Breakout'
            })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df_results = run_screener(symbols)

if not df_results.empty:
    print("\n📊 Darvas Box Breakout Screener:")
    print(df_results)

    # Define output file path
    json_file = os.path.join(output_dir, "darvas_breakouts.json")

    # Convert to flat list (no date key)
    all_data = df_results.to_dict(orient="records")

    # Save to JSON
    with open(json_file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"\n✅ Saved to {json_file}")
else:
    print("No breakout signals found today.")

