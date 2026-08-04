#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs/scripts"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update_data.log"
REQS_FILE="$REPO_ROOT/requirements.txt"
VENV_DIR="$REPO_ROOT/.venv"

echo "=== Update run: $(date -u +"%Y-%m-%dT%H:%M:%SZ") ===" >> "$LOG_FILE"

PYTHON_CMD="$(command -v python3 || command -v python)"

ensure_python_env() {
  if [[ -x "$VENV_DIR/bin/python" ]] && "$VENV_DIR/bin/python" -c "import nsepython, pandas, yfinance, pytz, feedparser, vaderSentiment" >/dev/null 2>&1; then
    PYTHON_CMD="$VENV_DIR/bin/python"
    return
  fi

  echo "--- Bootstrapping Python environment ---" >> "$LOG_FILE"
  "$PYTHON_CMD" -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
  "$VENV_DIR/bin/python" -m pip install --upgrade pip >> "$LOG_FILE" 2>&1
  "$VENV_DIR/bin/python" -m pip install -r "$REQS_FILE" >> "$LOG_FILE" 2>&1
  PYTHON_CMD="$VENV_DIR/bin/python"
}

# Keep the frequent market cron fast and reliable. Other generated datasets have
# their own scheduled workflows.
if ! "$PYTHON_CMD" -c "import nsepython, pandas, yfinance, pytz, feedparser, vaderSentiment" >/dev/null 2>&1; then
  ensure_python_env
fi

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
