# 🌸 고도화 웨딩박람회 자동 스크래핑 프로그램

## 개요
이 프로젝트는 **광주광역시** 및 전국 주요 도시의 웨딩 박람회 일정을 자동으로 수집하고, 매일 업데이트하여 GitHub에 커밋하는 고도화된 프로그램을 제공합니다.

## 🚀 주요 기능 (고도화 완료)

| 기능 | 설명 | 상태 |
|------|------|------|
| **병렬 스크래핑** | ThreadPoolExecutor로 동시 6개 소스 처리 | ✅ 완료 |
| **Playwright 동적 페이지** | JavaScript 렌더링 페이지対応 | ✅ 완료 |
| **날짜/장소 추출** | 정규식으로 정확한 날짜와 장소 추출 | ✅ 완료 |
| **Discord 알림** | 신규 웨딩박람회 등록 시 웹훅 알림 | ✅ 완료 |
| **Telegram 알림** | 텔레그램 봇으로 알림 전송 | ✅ 완료 |
| **Streamlit 대시보드** | 웹 브라우저에서 데이터 시각화 | ✅ 완료 |
| **GitHub 자동 동기화** | 데이터 변경 시 자동 커밋/푸시 | ✅ 완료 |
| **Cron 자동 실행** | 매일 새벽 6:00 자동 실행 | ✅ 완료 |

## 프로젝트 구조
```
wedding_expo_scraper/
├── wedding_expo_scraper/  # 메인 패키지
│   ├── __init__.py
│   ├── config.py          # 설정
│   ├── scraper.py         # 병렬 스크래핑
│   ├── parser.py          # 데이터 정규화
│   ├── storage.py         # CSV 저장
│   ├── notification.py     # 알림 시스템
│   ├── dynamic_scraper.py  # Playwright 동적 페이지
│   └── github_sync.py     # GitHub 연동
├── data/                  # 데이터 저장
│   ├── gwangju_wedding_expos.csv
│   └── logs/
├── dashboard.py           # Streamlit 대시보드
├── main.py               # 메인 실행 파일
├── scripts/
│   └── run_scraper.sh
├── requirements.txt
└── .env                 # 토큰 설정
```

## 설치 및 설정

### 1. 의존성 설치
```bash
cd /home/zenith/Desktop/wedding_expo_scraper
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치 (선택사항)
```bash
python -m playwright install chromium
```

### 3. 알림 설정 (선택사항)
`.env` 파일 생성:
```
# Discord 웹훅
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Telegram 봇
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Playwright 폴백 사용
USE_PLAYWRIGHT_FALLBACK=true
```

### 4. 대시보드 실행 (선택사항)
```bash
pip install streamlit
streamlit run dashboard.py
```

## 사용 방법

### 수동 실행
```bash
python3 main.py
```

### 대시보드 실행
```bash
streamlit run dashboard.py
```

## 수집 데이터 필드
| 필드 | 설명 |
|------|------|
| **name** | 박람회명 |
| **start_date** | 시작일 (YYYY-MM-DD) |
| **end_date** | 종료일 (YYYY-MM-DD) |
| **location** | 장소 |
| **organizer** | 주관사 |
| **source_url** | 출처 URL |
| **scraped_at** | 스크래핑 일시 |
| **region** | 지역 |

## 데이터 소스
- weddingfairschedule.kr
- weddingo.kr
- gjweddingshow.kr
- 동적 페이지 소스 (Playwright対応)

## 라이선스
MIT License
