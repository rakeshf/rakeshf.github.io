from nsepython import *
import pandas as pd
import json
import os
from datetime import datetime, time
import sys
from zoneinfo import ZoneInfo
from market_check import parse_args, check_market_conditions
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time as _time
import functools

# -------------------- SAFE HELPERS --------------------

def safe_pct_change(curr, prev):
    if prev in (0, None):
        return 0.0
    return round(((curr - prev) / prev) * 100, 2)

# -------------------- ARGUMENTS & MARKET CHECK --------------------

args = parse_args()
if not check_market_conditions(debug_mode=args.debug):
    sys.exit(0)

# -------------------- SYMBOL LIST --------------------

file_path = "../symbols.txt"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ File not found: {file_path}")

with open(file_path, "r") as file:
    symbols = [line.strip() for line in file if line.strip()]

print("✅ Symbols loaded:", symbols)

# -------------------- SIGNAL CHANGE ALERT --------------------

def alert_signal_changes(latest_file, prev_file, alert_file="../data/signal_alerts.json"):
    if not os.path.exists(latest_file) or not os.path.exists(prev_file):
        return

    with open(latest_file, "r") as f1, open(prev_file, "r") as f2:
        latest_data = json.load(f1)
        prev_data = json.load(f2)

    latest_map = {s["symbol"]: s for s in latest_data}
    prev_map = {s["symbol"]: s for s in prev_data}

    changes = []
    for symbol, latest in latest_map.items():
        prev = prev_map.get(symbol)
        if prev and latest.get("signal") != prev.get("signal"):
            changes.append({
                "symbol": symbol,
                "old_signal": prev.get("signal"),
                "new_signal": latest.get("signal")
            })

    if changes:
        with open(alert_file, "w") as f:
            json.dump(changes, f, indent=2)
        print(f"🚨 {len(changes)} signal(s) changed")

# -------------------- INDEX HANDLER --------------------

def add_file_to_index(new_filename, index_path="../data/index.json"):
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            try:
                files = json.load(f)
            except json.JSONDecodeError:
                files = []
    else:
        files = []

    files = [new_filename] + [f for f in files if f != new_filename]

    with open(index_path, "w") as f:
        json.dump(files, f, indent=2)

# -------------------- HELPERS: RETRY / FETCH --------------------

def retry_on_exception(retries=3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    _time.sleep(delay * (2 ** i))
            raise last_exc
        return wrapper
    return decorator


@retry_on_exception(retries=3, delay=1)
def fetch_eq_with_retry(symbol):
    return nse_eq(symbol)


@retry_on_exception(retries=3, delay=1)
def fetch_optionchain_with_retry(symbol):
    return nse_optionchain_scrapper(symbol)

# -------------------- SIGNAL LOGIC --------------------

def calculate_sentiment_and_signal(price_direction, oi_direction,
                                   ce_oi_change_pct, pe_oi_change_pct, pcr):

    if ce_oi_change_pct > pe_oi_change_pct + 1:
        build_side = "Call Side"
    elif pe_oi_change_pct > ce_oi_change_pct + 1:
        build_side = "Put Side"
    else:
        build_side = "Balanced"

    if pcr is None:
        sentiment = "Neutral"
    elif pcr > 1.2:
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

# -------------------- DIRECTORIES --------------------

output_dir = "../data"
log_dir = "../logs/stocks"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

# -------------------- MAIN LOOP --------------------

all_results = []

for symbol in symbols:
    # converted to concurrent processing below
    pass

# -------------------- CONCURRENT PROCESSING --------------------

def process_symbol(symbol: str, log_dir: str):
    try:
        print(f"\n{'='*60}\n🔍 Analyzing: {symbol}")
        oi_log_file = os.path.join(log_dir, f"{symbol}_oi_log.json")

        # ----- PRICE -----
        eq_data = fetch_eq_with_retry(symbol)
        ltp = float(eq_data["priceInfo"]["lastPrice"])
        prev_close = float(eq_data["priceInfo"]["previousClose"])

        price_change_pct = safe_pct_change(ltp, prev_close)
        price_direction = "↑" if price_change_pct > 0 else "↓"

        # ----- OPTION CHAIN -----
        chain = fetch_optionchain_with_retry(symbol)
        option_data = chain.get("records", {}).get("data", [])

        total_ce_oi = 0
        total_pe_oi = 0
        for item in option_data:
            if item.get("CE"):
                total_ce_oi += item["CE"].get("openInterest", 0)
            if item.get("PE"):
                total_pe_oi += item["PE"].get("openInterest", 0)

        curr_total_oi = total_ce_oi + total_pe_oi

        # ----- PREVIOUS OI -----
        if os.path.exists(oi_log_file):
            with open(oi_log_file, "r") as f:
                prev = json.load(f)
                prev_total_oi = prev.get("total_oi", curr_total_oi)
                prev_total_ce_oi = prev.get("total_ce_oi", total_ce_oi)
                prev_total_pe_oi = prev.get("total_pe_oi", total_pe_oi)
        else:
            prev_total_oi = curr_total_oi
            prev_total_ce_oi = total_ce_oi
            prev_total_pe_oi = total_pe_oi

        with open(oi_log_file, "w") as f:
            json.dump({
                "total_oi": curr_total_oi,
                "total_ce_oi": total_ce_oi,
                "total_pe_oi": total_pe_oi
            }, f)

        # ----- CHANGES -----
        oi_change_pct = safe_pct_change(curr_total_oi, prev_total_oi)
        ce_oi_change_pct = safe_pct_change(total_ce_oi, prev_total_ce_oi)
        pe_oi_change_pct = safe_pct_change(total_pe_oi, prev_total_pe_oi)

        oi_direction = "↑" if oi_change_pct > 0 else "↓"
        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else None

        # ----- SIGNAL -----
        sentiment, signal, build_side, conflict = calculate_sentiment_and_signal(
            price_direction, oi_direction,
            ce_oi_change_pct, pe_oi_change_pct, pcr
        )

        return {
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
            "conflict": conflict,
            "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"⚠️ Error processing {symbol}: {e}")
        return None


max_workers = min(12, max(2, (os.cpu_count() or 2) * 2))
with ThreadPoolExecutor(max_workers=max_workers) as ex:
    futures = {ex.submit(process_symbol, s, log_dir): s for s in symbols}
    for fut in as_completed(futures):
        res = fut.result()
        if res:
            all_results.append(res)

# -------------------- SAVE OUTPUT --------------------

timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%dT%H-%M-%S")
output_file = os.path.join(output_dir, f"{timestamp}.json")

add_file_to_index(output_file)

with open(output_file, "w") as f:
    json.dump(all_results, f, indent=2)

# -------------------- ALERT CHECK --------------------

index_file = "../data/index.json"
with open(index_file, "r") as f:
    index = json.load(f)

if len(index) >= 2:
    alert_signal_changes(output_file, index[1])

print(f"\n✅ Combined F&O summary saved to: {output_file}")
