# 알림 설정 가이드

> 알림은 `main.py` 실행 중 최종 실패, 성공 완료, 일일 요약 시점에 사용됩니다. 정적/동적 소스는 내부에서 1회 재시도 후 최종 상태가 알림에 반영됩니다.

## Discord 웹훅 설정

### 1. Discord 서버에서 웹훅 생성
1. Discord 서버 접속 → 채널 선택 → 채널 설정
2. **통합** → **웹훅** → **새 웹훅**
3. 이름 입력 (예: "웨딩박람회 알림")
4. **웹훅 URL 복사** (형식: `https://discord.com/api/webhooks/...`)

### 2. 환경 변수 설정

```bash
# .env 파일에 추가
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
```

### 3. 테스트
```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 -c "
from wedding_expo_scraper.notification import NotificationService
notifier = NotificationService()
test_events = [{'name': '테스트 행사', 'start_date': '2026-04-01', 'location': '광주'}]
notifier.send_wedding_expo_notification(test_events, 1)
"
```

---

## Telegram 봇 설정

### 1. 봇 생성
1. Telegram에서 **@BotFather** 검색
2. `/newbot` 명령어 입력
3. 봇 이름 입력 (예: "웨딩박람회 알림")
4. Username 입력 (필수: `bot`으로 끝나야 함)
5. **토큰 저장** (형식: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. 채팅 ID 확인
1. 생성한 봇 검색 → **시작** 버튼 클릭
2. 브라우저에서 접속: 
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. 응답에서 `"chat":{"id":123456789,...}` 확인

### 3. 환경 변수 설정

```bash
# .env 파일에 추가
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4. 테스트
```bash
python3 -c "
from wedding_expo_scraper.notification import NotificationService
notifier = NotificationService()
notifier._send_telegram('🔔 웨딩박람회 알림 테스트 메시지')
"
```

---

## .env 파일 설정 예시

```bash
# /home/zenith/Desktop/wedding_expo_scraper/.env

# Discord 알림
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-id/your-token

# Telegram 알림
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# GitHub 연동
GITHUB_TOKEN=ghp_your_github_token
GITHUB_REPO_URL=https://github.com/dkdleljh/wedding-expo-scraper
```

---

## 알림 유형

| 유형 | 설명 | 전송 시점 |
|------|------|----------|
| `send_wedding_expo_notification` | 새 웨딩박람회 발견 | 새 행사 수집 시 |
| `send_success_notification` | 스크래핑 완료 | 매일 06:00, 18:00 |
| `send_error_notification` | 최종 실패 또는 예외 | 재시도 후 실패 시 |
| `send_daily_summary` | 일일 리포트 | 매일 자정 |

---

## 슬랙 연동 (선택)

슬랙을 사용하는 경우:

1. **Slack App** 생성: https://api.slack.com/apps
2. **Incoming Webhooks** 활성화
3. Webhook URL 복사 후 `.env`에 추가:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
```

---

## 문제 해결

### 알림이 오지 않는 경우
1. `.env` 파일 확인 → 값이正しく 입력되었는지
2. Discord/Telegram 토큰 유효성 확인
3. 인터넷 연결 상태 확인
4. 로그 확인: `tail -f /tmp/wedding_expo_cron.log`
