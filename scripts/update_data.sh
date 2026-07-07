#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs/scripts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update_data.log"

echo "=== Update run: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"

PYTHON_CMD="$(command -v python3 || command -v python)"

SCRIPTS=(
  intra_day.py
  market_check.py
  screener.py
  darvas_screener.py
  golden_cross.py
  sentiment.py
)

for s in "${SCRIPTS[@]}"; do
  echo "--- Running $s ---" >> "$LOG_FILE"
  "$PYTHON_CMD" "$REPO_ROOT/scripts/$s" >> "$LOG_FILE" 2>&1 || echo "ERROR: $s failed" >> "$LOG_FILE"
done

echo "=== Done: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"
