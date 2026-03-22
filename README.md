# 광주광역시 웨딩박람회 자동 스크래핑 프로그램

## 개요
이 프로젝트는 광주광역시에서 진행되는 웨딩 박람회 일정을 자동으로 수집하고, 매일 업데이트하여 GitHub에 커밋하는 프로그램을 제공합니다.

## 주요 기능
- 광주광역시 웨딩 박람회 일정 자동 수집
- 매일 정해진 시간에 자동 실행 (Cron)
- GitHub 자동 커밋 및 푸시
- CSV 형식으로 데이터 저장

## 프로젝트 구조
```
wedding_expo_scraper/
├── wedding_expo_scraper/  # 메인 패키지
│   ├── __init__.py
│   ├── config.py          # 설정
│   ├── scraper.py         # 웹 스크래핑
│   ├── parser.py          # HTML 파싱
│   ├── storage.py         # 데이터 저장
│   └── github_sync.py     # GitHub 연동
├── data/                  # 데이터 저장
│   └── gwangju_wedding_expos.csv
├── scripts/               # 실행 스크립트
│   └── run_scraper.sh
├── tests/                 # 테스트
├── requirements.txt       # Python 의존성
└── .env                   # 환경 변수 (토큰)
```

## 설치 및 설정

### 1. 의존성 설치
```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. GitHub 토큰 설정
`.env` 파일을 생성하고 GitHub Personal Access Token을 입력합니다:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 3. GitHub 저장소 연결
```bash
git init
git remote add origin https://github.com/사용자명/저장소명.git
```

### 4. Cron 설정
```bash
crontab -e
# 아래 줄 추가:
0 6 * * * /home/zenith/Desktop/wedding_expo_scraper/scripts/run_scraper.sh >> /home/zenith/Desktop/wedding_expo_scraper/data/logs/cron.log 2>&1
```

## 사용 방법

### 수동 실행
```bash
cd /home/zenith/Desktop/wedding_expo_scraper
source venv/bin/activate
python -m wedding_expo_scraper
```

### 데이터 확인
```bash
cat data/gwangju_wedding_expos.csv
```

## 수집 데이터 필드
- **name**: 박람회명
- **start_date**: 시작일 (YYYY-MM-DD)
- **end_date**: 종료일 (YYYY-MM-DD)
- **location**: 장소
- **source_url**: 출처 URL
- **scraped_at**: 스크래핑 일시

## 라이선스
MIT License
