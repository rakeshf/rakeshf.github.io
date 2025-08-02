# market_check.py
import argparse
from datetime import datetime, time
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Market-time controlled script with optional debug mode.")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode (bypass market time checks)")
    return parser.parse_args()

def is_valid_trading_day():
    return datetime.now().weekday() < 5  # Monday=0, Sunday=6

def is_market_time():
    now = datetime.now()
    return time(9, 15) <= now.time() <= time(15, 30)

def is_valid_interval():
    return datetime.now().minute % 15 == 0

def check_market_conditions(debug_mode=False):
    now = datetime.now()

    if debug_mode:
        print("🐞 Debug mode enabled — bypassing market day/time checks.")
        return

    if not is_valid_trading_day():
        print(f"⛔ Market closed today ({now.strftime('%A')}).")
        sys.exit(0)

    if not is_market_time():
        print(f"⛔ Outside market hours: {now.strftime('%H:%M')} is not between 09:15–15:30 IST.")
        sys.exit(0)

    if not is_valid_interval():
        print(f"⛔ Invalid interval: {now.strftime('%H:%M')} is not on a 15-minute boundary.")
        sys.exit(0)

    print(f"✅ Running script at {now.strftime('%A %H:%M')} — debug_mode={debug_mode}")
