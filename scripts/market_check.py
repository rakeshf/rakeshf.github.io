# market_check.py

import argparse
from datetime import datetime, time
import pytz
import os

# Optional: path to a log file for tracking (especially when used in cron jobs)
LOG_PATH = "../logs/scripts/market_check.log"

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log(message):
    """Append timestamped message to log file and print it."""
    timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"{timestamp} — {message}"
    print(full_msg)
    with open(LOG_PATH, "a") as f:
        f.write(full_msg + "\n")

def parse_args():
    parser = argparse.ArgumentParser(description="Market-time controlled script with optional debug mode.")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode (bypass market time checks)")
    parser.add_argument(
        "--strict-interval",
        action="store_true",
        help="Require the script to start exactly on a 15-minute boundary.",
    )
    return parser.parse_args()

def get_current_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist)

def is_valid_trading_day(now):
    """Return True if today is Monday–Friday"""
    return now.weekday() < 5

def is_market_time(now):
    """Return True if time is between 09:15 and 15:30 IST"""
    return time(9, 15) <= now.time() <= time(15, 30)

def is_valid_interval(now):
    """Return True if current time is on a 15-minute boundary (e.g., 09:15, 09:30...)"""
    return now.minute % 15 == 0

def check_market_conditions(debug_mode=False, strict_interval=False):
    """Main market validation function. Returns True if it's okay to proceed."""
    now = get_current_time()

    if debug_mode:
        log("🐞 Debug mode enabled — bypassing market day/time checks.")
        return True

    if not is_valid_trading_day(now):
        log(f"⛔ Market closed today ({now.strftime('%A')}).")
        return False

    if not is_market_time(now):
        log(f"⛔ Outside market hours: {now.strftime('%H:%M')} is not between 09:15–15:30 IST.")
        return False

    if strict_interval and not is_valid_interval(now):
        log(f"⛔ Invalid interval: {now.strftime('%H:%M')} is not on a 15-minute boundary.")
        return False

    log(f"✅ Market open — running script at {now.strftime('%A %H:%M')}")
    return True

# Optional: allow this script to run standalone
if __name__ == "__main__":
    args = parse_args()
    success = check_market_conditions(args.debug, args.strict_interval)
    if not success:
        exit(0)
