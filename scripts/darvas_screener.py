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
buffer_pct = 1.5        # Pre-breakout/breakdown buffer (percent)
stop_loss_pct = 3       # Backtest only (not used here)

# --- Fetch OHLCV data ---
def get_data(symbol, days):
    end = datetime.now()
    start = end - timedelta(days=days)
    return yf.download(symbol, start=start, end=end, auto_adjust=False)

# --- Robust Darvas box detector ---
def find_darvas_boxes(df, box_length=5, debug=False):
    """
    Returns list of (timestamp_of_box, box_low, box_high)
    Defensive: finds High/Low columns case-insensitively, supports duplicated/MI columns.
    """
    # find column names containing 'high'/'low' (case-insensitive)
    def _find_col(df, keyword):
        for col in df.columns:
            if keyword in str(col).lower().strip():
                return col
        return None

    high_col = _find_col(df, 'high')
    low_col = _find_col(df, 'low')

    if high_col is None or low_col is None:
        if debug:
            print("DEBUG cols:", list(df.columns))
        raise KeyError("Could not find 'High' and 'Low' columns (case-insensitive).")

    high_series = df[high_col]
    low_series = df[low_col]
    if isinstance(high_series, pd.DataFrame):
        high_series = high_series.iloc[:, 0]
    if isinstance(low_series, pd.DataFrame):
        low_series = low_series.iloc[:, 0]

    highs_roll = high_series.rolling(window=box_length).max()
    lows_roll = low_series.rolling(window=box_length).min()

    highs_arr = highs_roll.to_numpy()
    lows_arr = lows_roll.to_numpy()

    boxes = []
    n = len(df)
    for i in range(box_length, n):
        recent_highs = high_series.iloc[i - box_length:i]
        recent_lows = low_series.iloc[i - box_length:i]

        try:
            box_high = highs_arr[i - 1]
            box_low = lows_arr[i - 1]
        except IndexError:
            continue

        if pd.isna(box_high) or pd.isna(box_low):
            continue

        box_high = float(box_high)
        box_low = float(box_low)

        highs_ok = (recent_highs.le(box_high)).all()
        lows_ok  = (recent_lows.ge(box_low)).all()

        if highs_ok and lows_ok:
            boxes.append((df.index[i], box_low, box_high))

    return boxes

# --- Breakout & breakdown checker ---
def check_box_signal(df, boxes, buffer_pct=1.5):
    """
    Returns (signal_type, direction, last_close, box_high, box_low)
    signal_type: "Confirmed breakout", "Pre-breakout", "Confirmed breakdown", "Pre-breakdown", "No"
    direction: "up" / "down" / None
    """
    if not boxes:
        return "No", None, None, None, None

    _, box_low, box_high = boxes[-1]

    # safe scalar access for last close
    try:
        last_close = df['Close'].iat[-1]
    except Exception:
        last_close = df['Close'].iloc[-1].item()
    last_close = float(last_close)

    top_buffer = box_high * (1 - buffer_pct / 100.0)
    bottom_buffer = box_low * (1 + buffer_pct / 100.0)

    # priority: confirmed signals first
    if last_close >= box_high:
        return "Confirmed breakout", "up", last_close, box_high, box_low
    if last_close <= box_low:
        return "Confirmed breakdown", "down", last_close, box_high, box_low
    if last_close >= top_buffer:
        return "Pre-breakout", "up", last_close, box_high, box_low
    if last_close <= bottom_buffer:
        return "Pre-breakdown", "down", last_close, box_high, box_low

    return "No", None, last_close, box_high, box_low

# --- Run Screener ---
def run_screener(symbols):
    results = []
    for symbol in symbols:
        try:
            df = get_data(symbol, lookback_days)
        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {e}")
            continue

        if df.empty or len(df) < box_length:
            print(f"⚠️ Skipping {symbol} (insufficient data)")
            continue

        try:
            boxes = find_darvas_boxes(df, box_length)
        except KeyError as e:
            print(f"⚠️ {symbol}: {e}")
            continue

        signal_type, direction, price, box_high, box_low = check_box_signal(df, boxes, buffer_pct)

        if signal_type != "No":
            friendly_map = {
                "Confirmed breakout": "✅ Confirmed breakout",
                "Pre-breakout": "🔼 Pre-breakout",
                "Confirmed breakdown": "🔻 Confirmed breakdown",
                "Pre-breakdown": "🔽 Pre-breakdown"
            }
            results.append({
                'Symbol': symbol,
                'Signal': friendly_map.get(signal_type, signal_type),
                'Direction': direction if direction else '',
                'Close': round(float(price), 2) if price is not None else None,
                'Box High': round(float(box_high), 2) if box_high is not None else None,
                'Box Low': round(float(box_low), 2) if box_low is not None else None,
            })

    return pd.DataFrame(results)

# --- Run script ---
if __name__ == "__main__":
    df_results = run_screener(symbols)

    if not df_results.empty:
        print("\n📊 Darvas Box Screener Signals:")
        print(df_results.to_string(index=False))

        output_path = os.path.join(output_dir, "darvas_breakouts.json")
        records = json.loads(df_results.to_json(orient="records"))

        with open(output_path, "w") as f:
            json.dump(records, f, indent=2)

        print(f"\n✅ Saved to {output_path}")
    else:
        print("❌ No breakout/breakdown signals found today.")
