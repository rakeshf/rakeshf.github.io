#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs/scripts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update_data.log"

echo "=== Update run: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"

PYTHON_CMD="$(command -v python3 || command -v python)"

# Keep the frequent market cron fast and reliable. Other generated datasets have
# their own scheduled workflows.
SCRIPTS=(
  screener.py
)

pushd "$REPO_ROOT/scripts" > /dev/null
for s in "${SCRIPTS[@]}"; do
  echo "--- Running $s ---" >> "$LOG_FILE"
  "$PYTHON_CMD" "$s" >> "$LOG_FILE" 2>&1
done
popd > /dev/null

echo "=== Done: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"
