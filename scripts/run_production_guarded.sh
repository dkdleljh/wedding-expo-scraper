#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/zenith/Desktop/wedding_expo_scraper"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
AUTO_RELEASE_ON_SUCCESS="${AUTO_RELEASE_ON_SUCCESS:-true}"
LOG_DIR="$PROJECT_DIR/data/logs"
PRECHECK_LOG="$LOG_DIR/precheck_latest.log"
RUN_LOG="$LOG_DIR/production_latest.log"
RELEASE_LOG="$LOG_DIR/release_latest.log"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

echo "[precheck] $(date '+%Y-%m-%d %H:%M:%S')"
$PYTHON_BIN main.py --dry-run --skip-github --skip-tistory --skip-notify | tee "$PRECHECK_LOG"

$PYTHON_BIN - <<'PY'
import json
from pathlib import Path
import sys

report_path = Path("/home/zenith/Desktop/wedding_expo_scraper/data/logs/latest_source_health_report.json")
if not report_path.exists():
    print("precheck_failed: health report missing")
    sys.exit(2)

report = json.loads(report_path.read_text(encoding="utf-8"))
checked = int(report.get("checked_sources", 0))
healthy = int(report.get("healthy_sources", 0))
failed = int(report.get("failed_sources", 0))

if checked == 0:
    print("precheck_failed: no checked sources")
    sys.exit(2)

if healthy == 0:
    print("precheck_failed: no healthy sources")
    sys.exit(2)

if failed >= checked:
    print("precheck_failed: all checked sources failed")
    sys.exit(2)

print(f"precheck_ok: checked={checked} healthy={healthy} failed={failed}")
PY

echo "[run] $(date '+%Y-%m-%d %H:%M:%S')"
$PYTHON_BIN main.py | tee "$RUN_LOG"

if [[ "$AUTO_RELEASE_ON_SUCCESS" == "true" ]]; then
  echo "[release] $(date '+%Y-%m-%d %H:%M:%S')"
  $PYTHON_BIN scripts/auto_release.py | tee "$RELEASE_LOG"
fi
