import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# List of NIFTY 50 or F&O symbols (Yahoo format)
# -- List of F&O stocks to analyze --
file_path = "../darvas-box.txt"

# -- Output directory --
output_dir = "../data"
os.makedirs(output_dir, exist_ok=True)

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

with open(file_path, "r") as file:
    symbols = [line.strip() for line in file if line.strip()]

print("✅ Symbols loaded:", symbols) # Add more if needed

def is_golden_cross(df):
    if df.shape[0] < 201:
        return False

    df['50_SMA'] = df['Close'].rolling(window=50).mean()
    df['200_SMA'] = df['Close'].rolling(window=200).mean()

    for i in range(-5, -1):
        prev_50 = df['50_SMA'].iloc[i-1]
        prev_200 = df['200_SMA'].iloc[i-1]
        curr_50 = df['50_SMA'].iloc[i]
        curr_200 = df['200_SMA'].iloc[i]
        if pd.notna(prev_50) and pd.notna(prev_200) and pd.notna(curr_50) and pd.notna(curr_200):
            if prev_50 < prev_200 and curr_50 > curr_200:
                return df.index[i].strftime("%Y-%m-%d")
    return False

results = []

print("🔍 Scanning for Golden Cross signals...")

for symbol in symbols:
    try:
        print(f"📈 Analyzing {symbol}...")
        df = yf.download(symbol, period="1y", progress=False, auto_adjust=False)
        if df.empty:
            print(f"⚠️ No data for {symbol}. Skipping.")
            continue
        crossover_date = is_golden_cross(df)
        if crossover_date:
            last_price = round(float(df["Close"].iloc[-1].item()), 2)
            print(f"🟢 {symbol}: Golden Cross on {crossover_date} at ₹{last_price}")
            results.append({
                "Symbol": symbol.replace(".NS", ""),
                "Golden Cross Date": crossover_date,
                "Last Price": last_price
            })
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")

# Save results to JSON
output_file = os.path.join(output_dir, "golden_cross.json")
try:
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ {len(results)} stocks found with Golden Cross.")
    print(f"📁 Results saved to '{output_file}'")
    for r in results:
        print(f"🟢 {r['Symbol']}: {r['Golden Cross Date']} (₹{r['Last Price']})")
except Exception as e:
    print(f"❌ Error saving results to JSON: {e}")
