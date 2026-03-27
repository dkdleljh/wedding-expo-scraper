#!/bin/bash
# ================================================================================
# 광주광역시 웨딩박람회 스크래핑 자동 실행 스크립트
# ================================================================================

set -euo pipefail

SCRIPT_DIR="/home/zenith/Desktop/wedding_expo_scraper"
LOG_DIR="$SCRIPT_DIR/data/logs"
RUNNER_SCRIPT="$SCRIPT_DIR/scripts/run_production_guarded.sh"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +\%Y\%m\%d_\%H\%M\%S).log"

echo "============================================" | tee -a "$LOG_FILE"
echo "🚀 웨딩박람회 스크래핑 자동 실행" | tee -a "$LOG_FILE"
echo "⏰ 시작 시간: $(date)" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR" || exit 1
bash "$RUNNER_SCRIPT" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "============================================" | tee -a "$LOG_FILE"
echo "🏁 종료 시간: $(date)" | tee -a "$LOG_FILE"
echo "종료 코드: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "============================================" | tee -a "$LOG_FILE"

exit $EXIT_CODE
