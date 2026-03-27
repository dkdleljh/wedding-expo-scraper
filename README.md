# 광주 웨딩박람회 스크래퍼

광주권 웨딩박람회 일정을 수집해 정규화하고, SQLite/CSV로 저장하며, 필요 시 GitHub 동기화와 티스토리 발행까지 연결하는 운영형 스크래퍼입니다.

현재 코드는 다음 운영 원칙을 기준으로 구성되어 있습니다.

- 수집 범위는 `오늘 ~ 달력 기준 3개월`
- 동일 행사는 출처가 달라도 canonical 레코드로 병합
- 실패 소스뿐 아니라 `연속 0건` 소스도 자동 격리
- `dry-run`으로 저장/배포 없이 프리체크 가능
- 프로덕션 실행은 가드 스크립트가 프리체크 후 본실행

## 빠른 시작

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
pip install -r requirements.txt
playwright install chromium
```

점검만 실행:

```bash
python3 main.py --dry-run --skip-github --skip-tistory --skip-notify
```

운영 실행:

```bash
python3 main.py
```

가드 포함 운영 실행:

```bash
bash scripts/run_production_guarded.sh
```

대시보드:

```bash
streamlit run dashboard.py
```

## 실행 모드

`main.py`는 아래 옵션을 지원합니다.

- `--dry-run`: 저장/배포 없이 수집, 정규화, 헬스 리포트만 실행
- `--skip-github`: GitHub 동기화 생략
- `--skip-tistory`: 티스토리 포스팅 생략
- `--skip-notify`: Discord/Telegram 알림 생략
- `--ignore-health`: 서킷 브레이커 무시

운영 권장 경로는 `scripts/run_production_guarded.sh`입니다. 이 스크립트는:

1. `dry-run` 프리체크 실행
2. 최신 헬스 리포트 검사
3. 체크된 소스가 전부 실패한 경우 본실행 중단
4. 조건이 괜찮으면 본실행 수행

## 현재 데이터 계약

저장 컬럼:

- `name`
- `start_date`
- `end_date`
- `operating_hours`
- `location`
- `organizer`
- `contact`
- `source_url`
- `description`
- `region`
- `source`

정규화 특징:

- 날짜는 `YYYY-MM-DD`, `YYYY.MM.DD`, `YYYY년 M월 D일`, `YY.MM.DD`, `M월 D일`, 날짜 범위를 처리
- 장소 별칭은 광주 상세 주소로 승격
- `광주 웨딩 페스타`와 `광주웨딩페스타` 같은 표기 차이는 canonicalization으로 병합

## 소스 운영 정책

기본값은 `PRODUCTION_SOURCE_MODE=ON`입니다. 이 모드에서는 전체 소스가 아니라 검증된 활성 소스셋만 사용합니다.

헬스 정책:

- 연속 실패 `SOURCE_FAILURE_THRESHOLD` 이상이면 격리
- 연속 0건 `SOURCE_ZERO_RESULT_THRESHOLD` 이상이면 격리
- 격리 유지 시간은 `SOURCE_COOLDOWN_HOURS`

헬스 파일:

- 상태 저장: `data/source_health.json`
- 최신 리포트: `data/logs/latest_source_health_report.json`

## 대시보드

`dashboard.py`는 다음 탭을 제공합니다.

- 전체 일정
- 통계
- 다가오는 일정
- 내보내기
- 소스 상태

소스 상태 탭에서는 최근 실행 기준으로 다음을 확인할 수 있습니다.

- 소스별 상태
- 연속 실패 수
- 연속 0건 수
- 최근 결과 수
- 이번 실행에서 제외된 소스와 사유

## 자동 실행

크론 설치:

```bash
bash scripts/setup_cron.sh
```

설치되는 작업은 `scripts/run_production_guarded.sh`를 호출합니다. 직접 `main.py`를 크론에 붙이는 방식은 권장하지 않습니다.

## 릴리즈 자동화

이 저장소는 운영 실행 후 자동 릴리즈까지 연결할 수 있습니다.

- 스크립트: [scripts/auto_release.py](/home/zenith/Desktop/wedding_expo_scraper/scripts/auto_release.py)
- 가드 실행 스크립트는 기본적으로 성공 후 릴리즈를 시도합니다
- 환경 변수 `AUTO_RELEASE_ON_SUCCESS=false`로 자동 릴리즈를 끌 수 있습니다

릴리즈 조건:

1. 현재 `HEAD`가 아직 태그되지 않았어야 함
2. 마지막 semver 태그 이후 새 커밋이 있어야 함
3. 조건을 만족하면 다음 patch 버전 태그 생성
4. 태그 푸시 후 GitHub Release 생성

수동 릴리즈 예시:

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 scripts/auto_release.py --version v4.0.0
```

자동 생성되는 릴리즈 노트에는 다음이 들어갑니다.

- 기준 커밋
- CSV 행 수
- 일정 범위
- 최근 소스 헬스 요약
- 이번 실행에서 제외된 소스와 사유

## 알림과 티스토리

알림 환경 변수:

- `DISCORD_WEBHOOK_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

티스토리 환경 변수:

- `TISTORY_ACCESS_TOKEN`
- `TISTORY_BLOG_NAME`
- `TISTORY_CATEGORY_ID`
- `TISTORY_TAGS`

티스토리 주간 발행 상세는 [docs/TISTORY_WEEKLY.md](./docs/TISTORY_WEEKLY.md)를 참고하세요.

## 테스트

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 -m pytest -q
```

현재 회귀 테스트는 파서, 동적 대기 전략, canonical dedupe, 소스 헬스, dry-run 동작까지 포함합니다.

## 주요 경로

- 메인 실행: [main.py](/home/zenith/Desktop/wedding_expo_scraper/main.py)
- 설정: [config.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/config.py)
- 파서: [parser.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/parser.py)
- 정적 스크래퍼: [scraper.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/scraper.py)
- 동적 스크래퍼: [dynamic_scraper.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/dynamic_scraper.py)
- 헬스 관리: [source_health.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/source_health.py)
- 운영 실행 스크립트: [run_production_guarded.sh](/home/zenith/Desktop/wedding_expo_scraper/scripts/run_production_guarded.sh)
- 릴리즈 스크립트: [auto_release.py](/home/zenith/Desktop/wedding_expo_scraper/scripts/auto_release.py)
- 운영 문서: [docs/OPERATIONS.md](/home/zenith/Desktop/wedding_expo_scraper/docs/OPERATIONS.md)
