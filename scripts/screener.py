from nsepython import *
import pandas as pd
import json
import os
from datetime import datetime
from market_check import parse_args, check_market_conditions

# Parse command line arguments
args = parse_args()
check_market_conditions(debug_mode=args.debug)
# -- List of F&O stocks to analyze --
symbols = ["TCS", "INFY", "ICICIBANK", "INFY", "ITC"]  # Add more if needed


# -- Function to add file to index --

def add_file_to_index(new_filename, index_path='../data/index.json'):
    # Ensure the directory exists
    dir_path = os.path.dirname(index_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)  # create directory including parents if needed

    # Load existing index or create empty list if file does not exist or is invalid
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            try:
                files = json.load(f)
            except json.JSONDecodeError:
                files = []
    else:
        files = []

    print(f"\n✅ Combined F&O summary saved to: {os.path.basename(output_file)}")
    # Add new filename if not already present
    if new_filename not in files:
        files.append(new_filename)
        files.sort()
        with open(index_path, 'w') as f:
            json.dump(files, f, indent=2)
        print(f"Added '{new_filename}' to {index_path}")
    else:
        print(f"'{new_filename}' already exists in {index_path}")

# -- Function to calculate sentiment and signal --
def calculate_sentiment_and_signal(price_direction, oi_direction, ce_oi_change_pct, pe_oi_change_pct, pcr):
    if ce_oi_change_pct > pe_oi_change_pct + 1:
        build_side = "Call Side"
    elif pe_oi_change_pct > ce_oi_change_pct + 1:
        build_side = "Put Side"
    else:
        build_side = "Balanced"

    if pcr > 1.2:
        sentiment = "Bearish"
    elif pcr < 0.8:
        sentiment = "Bullish"
    else:
        sentiment = "Neutral"

    if price_direction == "↑" and oi_direction == "↑":
        signal = "Long Build-up"
    elif price_direction == "↓" and oi_direction == "↑":
        signal = "Short Build-up"
    elif price_direction == "↓" and oi_direction == "↓":
        signal = "Long Unwinding"
    elif price_direction == "↑" and oi_direction == "↓":
        signal = "Short Covering"
    else:
        signal = "No Clear Signal"

    conflict = False
    if ("Long" in signal and sentiment == "Bearish") or \
       ("Short" in signal and sentiment == "Bullish"):
        conflict = True
        signal += " ⚠️"

    return sentiment, signal, build_side, conflict

# -- Output directory --
output_dir = "../data"
os.makedirs(output_dir, exist_ok=True)

# -- log directory --
log_dir = "../logs"
os.makedirs(log_dir, exist_ok=True)

# -- Collect all results here --
all_results = []

# -- Loop through all symbols --
for symbol in symbols:
    try:
        print(f"\n{'='*60}\n🔍 Analyzing: {symbol}")
        oi_log_file = os.path.join(log_dir, f"{symbol}_oi_log.json")
        # --- Price data ---
        eq_data = nse_eq(symbol)
        ltp = float(eq_data['priceInfo']['lastPrice'])
        prev_close = float(eq_data['priceInfo']['previousClose'])
        price_change_pct = round(((ltp - prev_close) / prev_close) * 100, 2)
        price_direction = "↑" if price_change_pct > 0 else "↓"

        # --- Option Chain ---
        chain = nse_optionchain_scrapper(symbol)
        option_data = chain.get("records", {}).get("data", [])

        total_ce_oi = 0
        total_pe_oi = 0

        for item in option_data:
            ce = item.get("CE")
            pe = item.get("PE")
            if ce:
                total_ce_oi += ce.get("openInterest", 0)
            if pe:
                total_pe_oi += pe.get("openInterest", 0)

        curr_total_oi = total_ce_oi + total_pe_oi

        # --- Load previous data ---
        if os.path.exists(oi_log_file):
            with open(oi_log_file, "r") as f:
                prev_oi_data = json.load(f)
                prev_total_oi = prev_oi_data.get("total_oi", curr_total_oi * 0.97)
                prev_total_ce_oi = prev_oi_data.get("total_ce_oi", total_ce_oi * 0.97)
                prev_total_pe_oi = prev_oi_data.get("total_pe_oi", total_pe_oi * 0.97)
        else:
            prev_total_oi = curr_total_oi * 0.97
            prev_total_ce_oi = total_ce_oi * 0.97
            prev_total_pe_oi = total_pe_oi * 0.97

        # --- Save current OI for next run ---
        with open(oi_log_file, "w") as f:
            json.dump({
                "total_oi": curr_total_oi,
                "total_ce_oi": total_ce_oi,
                "total_pe_oi": total_pe_oi
            }, f)

        # --- Change calculations ---
        oi_change_pct = round(((curr_total_oi - prev_total_oi) / prev_total_oi) * 100, 2)
        ce_oi_change_pct = round(((total_ce_oi - prev_total_ce_oi) / prev_total_ce_oi) * 100, 2)
        pe_oi_change_pct = round(((total_pe_oi - prev_total_pe_oi) / prev_total_pe_oi) * 100, 2)
        oi_direction = "↑" if oi_change_pct > 0 else "↓"
        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 0

        # --- Signal logic ---
        sentiment, signal, build_side, conflict_flag = calculate_sentiment_and_signal(
            price_direction, oi_direction, ce_oi_change_pct, pe_oi_change_pct, pcr
        )

        # --- Show in terminal ---
        print(f"🧾 {symbol} F&O Signal Summary")
        print(f"📈 Price: ₹{ltp} ({price_direction})")
        print(f"📉 Prev Close: ₹{prev_close}")
        print(f"🪙 Price Change: {price_change_pct}%")
        print(f"📊 Total CE OI: {total_ce_oi}")
        print(f"📊 Total PE OI: {total_pe_oi}")
        print(f"🔄 OI Change: {oi_change_pct}% ({oi_direction})")
        print(f"🔼 CE OI Change: {ce_oi_change_pct}%")
        print(f"🔽 PE OI Change: {pe_oi_change_pct}%")
        print(f"📟 PCR: {pcr}")
        print(f"🧠 Sentiment: {sentiment}")
        print(f"📌 Build-up Side: {build_side}")
        print(f"🧭 F&O Signal: **{signal}**")
        if conflict_flag:
            print("⚠️ Conflicting Signal & Sentiment")

        # --- Append to combined result list ---
        all_results.append({
            "symbol": symbol,
            "price": ltp,
            "previous_close": prev_close,
            "price_change_pct": price_change_pct,
            "price_direction": price_direction,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "oi_change_pct": oi_change_pct,
            "ce_oi_change_pct": ce_oi_change_pct,
            "pe_oi_change_pct": pe_oi_change_pct,
            "oi_direction": oi_direction,
            "pcr": pcr,
            "sentiment": sentiment,
            "signal": signal,
            "build_side": build_side,
            "conflict": conflict_flag
        })

    except Exception as e:
        print(f"⚠️ Error processing {symbol}: {e}")

# --- Save all results to timestamped JSON file ---
timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
output_file = os.path.join(output_dir, f"{timestamp}.json")
add_file_to_index(output_file)

with open(output_file, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\n✅ Combined F&O summary saved to: {output_file}")



