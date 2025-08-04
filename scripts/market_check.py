# market_check.py

import argparse
from datetime import datetime, time
import pytz

def parse_args():
    parser = argparse.ArgumentParser(description="Market-time controlled script with optional debug mode.")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode (bypass market time checks)")
    return parser.parse_args()

def get_current_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

def is_valid_trading_day(now):
    return now.weekday() < 5  # Monday=0, Sunday=6

def is_market_time(now):
    return time(9, 15) <= now.time() <= time(15, 30)

def is_valid_interval(now):
    return now.minute % 15 == 0

def check_market_conditions(debug_mode=False):
    now = get_current_time()

    if debug_mode:
        print("🐞 Debug mode enabled — bypassing market day/time checks.")
        return True

    if not is_valid_trading_day(now):
        print(f"⛔ Market closed today ({now.strftime('%A')}).")
        return False

    if not is_market_time(now):
        print(f"⛔ Outside market hours: {now.strftime('%H:%M')} is not between 09:15–15:30 IST.")
        return False

    if not is_valid_interval(now):
        print(f"⛔ Invalid interval: {now.strftime('%H:%M')} is not on a 15-minute boundary.")
        return False

    print(f"✅ Running script at {now.strftime('%A %H:%M')} — debug_mode={debug_mode}")
    return True

# Main block (optional if you want to use this as standalone script)
if __name__ == "__main__":
    args = parse_args()
    success = check_market_conditions(args.debug)
    if not success:
        exit(0)
