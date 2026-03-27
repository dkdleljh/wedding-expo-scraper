#!/bin/bash
# ================================================================================
# 웨딩박람회 스크래핑 - Cron 설정 스크립트
# 매일 06:00, 18:00에 자동으로 실행
# ================================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RUNNER_SCRIPT="$PROJECT_DIR/scripts/run_production_guarded.sh"
CRON_JOB="0 6,18 * * * bash $RUNNER_SCRIPT >> /tmp/wedding_expo_cron.log 2>&1"
CRON_MARKER="# WEDDING_EXPO_SCRAPER_CRON"

echo "🌸 광주광역시 웨딩박람회 스크래핑 - Cron 설정"
echo "=============================================="
echo ""

if ! command -v cron &> /dev/null; then
    echo "⚠️  cron이 설치되어 있지 않습니다."
    echo "   Ubuntu/Debian: sudo apt install cron"
    echo "   CentOS/RHEL: sudo yum install cronie"
    exit 1
fi

echo "1️⃣  현재 crontab 확인..."
crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | grep -v "^#" | head -5 || echo "   (비어있음)"
echo ""

echo "2️⃣  기존 설정 제거..."
crontab -l 2>/dev/null | grep -v "$CRON_MARKER" > /tmp/current_cron 2>/dev/null || true
echo "   ✅ 기존 크론 설정 백업됨"
echo ""

echo "3️⃣  새 크론 설정 추가..."
echo "" >> /tmp/current_cron
echo "$CRON_MARKER" >> /tmp/current_cron
echo "$CRON_JOB" >> /tmp/current_cron

crontab /tmp/current_cron
echo "   ✅ 등록 완료!"
echo ""

echo "4️⃣  설정 확인..."
echo ""
echo "   📅 실행 스케줄: 매일 06:00, 18:00"
echo "   📂 프로젝트: $PROJECT_DIR"
echo "   ▶️ 실행 스크립트: $RUNNER_SCRIPT"
echo "   📝 로그 파일: /tmp/wedding_expo_cron.log"
echo ""
crontab -l | grep "$CRON_MARKER" || true
echo ""

echo "5️⃣  cron 서비스 시작..."
if command -v systemctl &> /dev/null; then
    sudo systemctl start cron 2>/dev/null || sudo systemctl start crond 2>/dev/null || true
    sudo systemctl enable cron 2>/dev/null || sudo systemctl enable crond 2>/dev/null || true
else
    sudo service cron start 2>/dev/null || sudo service crond start 2>/dev/null || true
fi
echo "   ✅ cron 서비스 시작됨"
echo ""

echo "=============================================="
echo "✅ Cron 설정 완료!"
echo ""
echo "📌 수동으로 실행하려면:"
echo "   bash $RUNNER_SCRIPT"
echo ""
echo "📌 로그 확인:"
echo "   tail -f /tmp/wedding_expo_cron.log"
echo ""
echo "📌 크론 제거:"
echo "   crontab -e 후 '$CRON_MARKER' 줄 삭제"
echo "=============================================="
