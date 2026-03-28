# 알림 설정 가이드

이 문서는 Discord와 Telegram 알림을 설정하는 방법을 설명합니다. 알림은 단순 편의 기능이 아니라 운영 안전장치입니다. 수집 실패, 누락 가능성, 실행 완료 여부를 사람이 빨리 알아차리게 만드는 역할을 합니다.

## 1. 알림이 필요한 이유

이 프로젝트는 크론과 가드 스크립트로 상당 부분 자동화돼 있지만, 아래 상황은 사람에게 바로 전달돼야 합니다.

- 실행 중 치명적 예외 발생
- 본실행 성공 또는 실패
- 핵심 소스 장기 0건
- 참조 소스 대비 누락 가능성
- 일일 요약 확인 필요

따라서 알림 채널이 끊겨 있으면 “자동 실행은 되지만 아무도 이상을 모르는 상태”가 될 수 있습니다.

## 2. 지원 채널

현재 기본 지원 채널:

- Discord Webhook
- Telegram Bot

코드 경로:

- [notification.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/notification.py)

## 3. Discord 설정

### 3.1 웹훅 생성

1. Discord 서버에서 알림을 받을 채널을 선택합니다.
2. 채널 설정으로 이동합니다.
3. `통합` 또는 `Integrations` 메뉴를 엽니다.
4. `웹훅`을 생성합니다.
5. 웹훅 URL을 복사합니다.

형식 예시:

```text
https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
```

### 3.2 환경 변수 설정

`.env` 또는 쉘 환경에 아래 값을 넣습니다.

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN
```

### 3.3 테스트

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 - <<'PY'
from wedding_expo_scraper.notification import NotificationService
notifier = NotificationService()
notifier.send_success_notification(3, 5)
PY
```

## 4. Telegram 설정

### 4.1 봇 생성

1. Telegram에서 `@BotFather`를 엽니다.
2. `/newbot`을 입력합니다.
3. 봇 이름과 username을 설정합니다.
4. 발급된 토큰을 저장합니다.

### 4.2 채팅 ID 확인

1. 만든 봇과 대화를 시작합니다.
2. 아래 URL을 브라우저에서 엽니다.

```text
https://api.telegram.org/botYOUR_TOKEN/getUpdates
```

3. 응답 JSON에서 `chat.id` 값을 찾습니다.

### 4.3 환경 변수 설정

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 4.4 테스트

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 - <<'PY'
from wedding_expo_scraper.notification import NotificationService
notifier = NotificationService()
notifier._send_telegram('웨딩박람회 알림 테스트 메시지')
PY
```

## 5. `.env` 예시

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-id/your-token
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO_URL=https://github.com/dkdleljh/wedding-expo-scraper
TISTORY_ACCESS_TOKEN=xxx
TISTORY_BLOG_NAME=your_blog_name
TISTORY_CATEGORY_ID=0
```

## 6. 운영에서 기대하는 알림 종류

상황에 따라 구현 세부는 바뀔 수 있지만, 운영적으로는 다음 알림이 중요합니다.

- 실행 성공 알림
- 실행 실패 알림
- 일일 요약 알림
- 수집 결과 요약 알림
- 장기 0건 또는 커버리지 누락 감시 알림

알림은 많을수록 좋은 것이 아니라, 운영 판단에 필요한 신호만 주는 것이 중요합니다.

## 7. 점검 체크리스트

알림 설정 후 아래를 확인합니다.

- Discord 메시지가 실제 채널에 도착하는지
- Telegram 메시지가 실제 채팅에 도착하는지
- `.env` 파일이 서비스 실행 사용자 기준으로 읽히는지
- 크론 실행 환경에서도 동일하게 동작하는지

즉 쉘에서 한 번 성공했다고 끝내지 말고, 크론 기반 실행에서도 도착하는지 꼭 확인해야 합니다.

## 8. 문제 해결

### 8.1 아무 알림도 오지 않는 경우

1. `.env` 값 확인
2. Discord 웹훅 URL 또는 Telegram 토큰 확인
3. 네트워크 연결 확인
4. 실행 사용자 계정이 환경 변수를 읽는지 확인
5. `/tmp/wedding_expo_cron.log`와 애플리케이션 로그 확인

### 8.2 일부 채널만 실패하는 경우

1. Discord와 Telegram을 분리해서 테스트
2. 해당 채널 인증 정보만 재발급
3. 수동 테스트 후 본실행 재시도

### 8.3 운영 중에는 성공 알림만 오고 장애 신호가 약한 경우

운영 기준으로는 성공 알림보다 실패와 누락 경보가 더 중요합니다. 알림 정책을 바꿀 때는 “좋은 소식”보다 “대응이 필요한 소식”이 먼저 오도록 설계하는 편이 맞습니다.
