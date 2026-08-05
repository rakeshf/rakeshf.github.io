from nsepython import *
import pandas as pd
try:
    import yfinance as yf
except ImportError:
    yf = None
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
import glob

# -------------------- SAFE HELPERS --------------------
def safe_pct_change(curr, prev): 
    if prev in (0, None): 
        return 0.0 
    return round(((curr - prev) / prev) * 100, 2)

# -------------------- ARGUMENTS & MARKET CHECK --------------------
args = parse_args()
if not check_market_conditions(debug_mode=args.debug, strict_interval=args.strict_interval): 
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
    os.makedirs(os.path.dirname(alert_file), exist_ok=True)

    if not os.path.exists(latest_file) or not os.path.exists(prev_file): 
        with open(alert_file, "w") as f:
            json.dump([], f, indent=2)
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

    with open(alert_file, "w") as f: 
        json.dump(changes, f, indent=2)

    if changes:
        print(f"🚨 {len(changes)} signal(s) changed")
    else:
        print("ℹ️ No signal changes detected; wrote an empty signal alert list.")

# -------------------- INDEX HANDLER --------------------

def normalize_index_path(path: str) -> str:
    path = path.replace("\\", "/")
    path = path.replace("../data/", "")
    path = path.replace("./data/", "")
    path = path.lstrip("./")
    if path.startswith("data/"):
        path = path[len("data/"):]
    return path


def add_file_to_index(new_filename, index_path="../data/index.json"):
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    normalized = normalize_index_path(new_filename)

    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            try:
                files = json.load(f)
            except json.JSONDecodeError:
                files = []
    else:
        files = []

    normalized_files = [normalize_index_path(f) for f in files if isinstance(f, str)]
    normalized_files = [normalized] + [f for f in normalized_files if f != normalized]

    with open(index_path, "w") as f:
        json.dump(normalized_files, f, indent=2)

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

def fetch_yahoo_price(symbol):
    if yf is None:
        raise RuntimeError("yfinance is not installed")

    ticker = yf.Ticker(symbol + ".NS")
    for attr in ("fast_info", "info"):
        info = getattr(ticker, attr, None)
        if not info:
            continue
        last_price = info.get("lastPrice") or info.get("regularMarketPrice") or info.get("previousClose") or info.get("close")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        if last_price is not None:
            return {"priceInfo": {"lastPrice": last_price, "previousClose": previous_close}}

    hist = ticker.history(period="2d")
    if not hist.empty:
        last_price = float(hist.iloc[-1]["Close"])
        previous_close = float(hist.iloc[-2]["Close"]) if len(hist) >= 2 else None
        return {"priceInfo": {"lastPrice": last_price, "previousClose": previous_close}}

    raise ValueError(f"Yahoo Finance returned no valid price data for {symbol}")


@retry_on_exception(retries=3, delay=1)
def fetch_eq_with_retry(symbol):
    # Prefer nse_fno for lower latency and smaller payloads; fall back to nse_eq and Yahoo Finance.
    try:
        fno = nse_fno(symbol)
        if isinstance(fno, dict):
            ltp = fno.get("underlyingValue") or fno.get("lastPrice") or fno.get("ltp")
            prev = fno.get("previousClose") or fno.get("prevClose") or None
            try:
                ltp_val = float(str(ltp).replace(',', ''))
            except Exception:
                ltp_val = None
            if ltp_val is not None:
                try:
                    prev_val = float(str(prev).replace(',', '')) if prev is not None else None
                except Exception:
                    prev_val = None
                return {"priceInfo": {"lastPrice": ltp_val, "previousClose": prev_val}}
    except Exception:
        # swallow and fallback
        pass

    try:
        eq = nse_eq(symbol)
        if isinstance(eq, dict) and eq:
            return eq
    except Exception:
        pass

    if yf is not None:
        return fetch_yahoo_price(symbol)

    raise ValueError("Unable to fetch equity data for symbol")

@retry_on_exception(retries=3, delay=1)
def fetch_optionchain_with_retry(symbol):
    return nse_optionchain_scrapper(symbol)

@retry_on_exception(retries=3, delay=1)
def calculate_technicals(symbol):
    """
    Fetches 120 days of historical data and calculates:
    - Bollinger Band Squeeze (rolling 100-day 20th percentile)
    - 5 EMA vs 13 EMA (Trend)
    - RSI (Momentum)
    """
    try:
        # yfinance requires .NS for National Stock Exchange of India
        yf_symbol = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        
        df = yf.download(yf_symbol, period="120d", progress=False)
        
        if df.empty or len(df) < 100:
             return {"squeeze_on": False, "ema_bullish": False, "rsi": 0}

        # Handle multi-index columns from yfinance's new update if necessary
        if isinstance(df.columns, pd.MultiIndex):
            close_series = df['Close'].iloc[:, 0].squeeze()
        else:
            close_series = df['Close'].squeeze()

        # 1. Bollinger Bands & Squeeze
        sma_20 = close_series.rolling(window=20).mean()
        std_20 = close_series.rolling(window=20).std()
        upper_band = sma_20 + (2.0 * std_20)
        lower_band = sma_20 - (2.0 * std_20)
        bandwidth = ((upper_band - lower_band) / sma_20) * 100

        # Calculate 100-day rolling percentile.
        width_percentile = bandwidth.rolling(window=100).rank(pct=True)
        is_squeeze = bool(width_percentile.iloc[-1] <= 0.20)

        # 2. EMAs
        ema_5 = close_series.ewm(span=5, adjust=False).mean()
        ema_13 = close_series.ewm(span=13, adjust=False).mean()
        ema_bullish = bool(ema_5.iloc[-1] > ema_13.iloc[-1])

        # 3. RSI
        delta = close_series.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])

        return {
            "squeeze_on": is_squeeze,
            "ema_bullish": ema_bullish,
            "rsi": round(current_rsi, 2)
        }
    except Exception as e:
        print(f"⚠️ Technical calc failed for {symbol}: {e}")
        return {"squeeze_on": False, "ema_bullish": False, "rsi": 0}

# -------------------- SIGNAL LOGIC --------------------
def calculate_sentiment_and_signal(price_direction, oi_direction, ce_oi_change_pct, pe_oi_change_pct, pcr):
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
    if ("Long" in signal and sentiment == "Bearish") or ("Short" in signal and sentiment == "Bullish"): 
        conflict = True 
        signal += " ⚠️"

    return sentiment, signal, build_side, conflict

# -------------------- DIRECTORIES --------------------
output_dir = "../data"
log_dir = "../logs/stocks"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)


def find_nonzero_repo_oi_fallback(symbol: str):
    """Look through the repo's generated data snapshots for a non-zero OI entry.
    This acts as a second-stage fallback when the on-demand NSE payload is blocked
    and the per-symbol cache has been reset to zeros.
    """
    history_files = sorted(glob.glob(os.path.join(output_dir, "*.json")))
    for path in reversed(history_files):
        try:
            with open(path, "r") as f:
                payload = json.load(f)
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                if item.get("symbol") != symbol:
                    continue
                total_ce_oi = int(item.get("total_ce_oi", 0) or 0)
                total_pe_oi = int(item.get("total_pe_oi", 0) or 0)
                if total_ce_oi > 0 or total_pe_oi > 0:
                    return {
                        "total_oi": total_ce_oi + total_pe_oi,
                        "total_ce_oi": total_ce_oi,
                        "total_pe_oi": total_pe_oi,
                    }
        except Exception:
            continue
    return {
        "total_oi": 0,
        "total_ce_oi": 0,
        "total_pe_oi": 0,
    }

# -------------------- MAIN LOOP --------------------
all_results = []
failed_symbols = []

# -------------------- CONCURRENT PROCESSING --------------------
def process_symbol(symbol: str, log_dir: str): 
    try: 
        print(f"\n{'='*60}\n🔍 Analyzing: {symbol}") 
        oi_log_file = os.path.join(log_dir, f"{symbol}_oi_log.json")

        # ----- PRICE ----- 
        eq_data = fetch_eq_with_retry(symbol) 
        price_info = eq_data.get("priceInfo", {}) if isinstance(eq_data, dict) else {} 
        ltp_raw = price_info.get("lastPrice") 
        prev_close_raw = price_info.get("previousClose")

        # fallbacks and safe conversions 
        if ltp_raw is None: 
            raise ValueError("missing last price for symbol")

        try: 
            ltp = float(ltp_raw) 
        except Exception: 
            ltp = float(str(ltp_raw).replace(',', ''))

        if prev_close_raw in (None, 0): 
            prev_close = ltp 
        else: 
            try: 
                prev_close = float(prev_close_raw) 
            except Exception: 
                prev_close = float(str(prev_close_raw).replace(',', ''))

        price_change_pct = safe_pct_change(ltp, prev_close) 
        price_direction = "↑" if price_change_pct > 0 else "↓"

        # ----- PREVIOUS OI ----- 
        prev = None
        if os.path.exists(oi_log_file): 
            with open(oi_log_file, "r") as f: 
                prev = json.load(f)

        # ----- OPTION CHAIN ----- 
        total_ce_oi = 0
        total_pe_oi = 0
        chain_fallback_used = False
        try:
            chain = fetch_optionchain_with_retry(symbol)
            if not isinstance(chain, dict):
                raise ValueError("option chain payload must be a dictionary")

            records = chain.get("records")
            if not isinstance(records, dict):
                raise ValueError("option chain payload missing 'records' section")

            option_data = records.get("data")
            if not isinstance(option_data, list) or not option_data:
                raise ValueError("option chain payload missing 'records.data' rows")

            for item in option_data:
                if item.get("CE"):
                    total_ce_oi += item["CE"].get("openInterest", 0)
                if item.get("PE"):
                    total_pe_oi += item["PE"].get("openInterest", 0)
        except Exception as chain_error:
            chain_fallback_used = True
            print(f"⚠️ Option chain unavailable for {symbol}: {chain_error}. Falling back to cached OI snapshot.")

            fallback_snapshot = None
            if prev is not None:
                fallback_snapshot = prev
            if fallback_snapshot is None or (
                int(fallback_snapshot.get("total_ce_oi", 0) or 0) == 0
                and int(fallback_snapshot.get("total_pe_oi", 0) or 0) == 0
            ):
                fallback_snapshot = find_nonzero_repo_oi_fallback(symbol)

            if fallback_snapshot is not None:
                total_ce_oi = int(fallback_snapshot.get("total_ce_oi", 0) or 0)
                total_pe_oi = int(fallback_snapshot.get("total_pe_oi", 0) or 0)
            else:
                total_ce_oi = 0
                total_pe_oi = 0

        curr_total_oi = total_ce_oi + total_pe_oi

        if prev is not None:
            prev_total_oi = prev.get("total_oi", curr_total_oi)
            prev_total_ce_oi = prev.get("total_ce_oi", total_ce_oi)
            prev_total_pe_oi = prev.get("total_pe_oi", total_pe_oi)
        else:
            prev_total_oi = curr_total_oi
            prev_total_ce_oi = total_ce_oi
            prev_total_pe_oi = total_pe_oi

        # Preserve the last good cached OI snapshot when the live NSE payload is blocked.
        # This avoids silently replacing a known-good snapshot with zeros on every failed run.
        if not chain_fallback_used:
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
            price_direction, oi_direction, ce_oi_change_pct, pe_oi_change_pct, pcr
        )

        # ----- TECHNICALS -----
        technicals = calculate_technicals(symbol)
        
        master_score = 0
        if signal in ["Long Build-up", "Short Covering"]: 
            master_score += 1
        if technicals["squeeze_on"]: 
            master_score += 1
        if technicals["ema_bullish"]: 
            master_score += 1

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
            "timestamp": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
            "technicals": technicals,
            "master_score": master_score
        } 
    except Exception as e: 
        print(f"⚠️ Error processing {symbol}: {e}") 
        return None

max_workers = min(12, max(2, (os.cpu_count() or 2) * 2))
with ThreadPoolExecutor(max_workers=max_workers) as ex: 
    futures = {ex.submit(process_symbol, s, log_dir): s for s in symbols} 
    for fut in as_completed(futures): 
        symbol = futures[fut]
        try:
            res = fut.result()
        except Exception as e:
            print(f"⚠️ Worker failed for {symbol}: {e}")
            failed_symbols.append(symbol)
            continue

        if res:
            all_results.append(res)
        else:
            failed_symbols.append(symbol)

if failed_symbols:
    print(f"⚠️ Skipped {len(failed_symbols)} failed symbol(s): {', '.join(sorted(failed_symbols))}")

if not all_results:
    print("❌ No symbol data was generated; not writing an empty market JSON file.")
    sys.exit(1)

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
