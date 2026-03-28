# 광주 웨딩박람회 스크래퍼

광주광역시 웨딩 박람회 일정을 수집하고, 정규화하고, SQLite와 CSV로 저장한 뒤, 필요하면 GitHub 동기화, 티스토리 발행, 알림 전송까지 이어지는 운영형 수집 프로그램입니다.

이 저장소는 단순 스크래퍼가 아니라 다음 목표를 가진 운영 도구입니다.

- 향후 3개월 내 광주 웨딩 박람회 일정 수집
- 여러 출처에서 들어온 데이터를 하나의 canonical 레코드로 정리
- 누락 가능성을 참조 소스로 자동 점검
- 실패 소스와 연속 0건 소스를 자동 격리
- `dry-run`과 가드 스크립트로 본실행 전에 이상 여부를 검사
- 실행 결과를 CSV, DB, 헬스 리포트, 릴리즈까지 연결

## 1. 먼저 알아둘 점

이 프로그램은 현재 공개 웹에서 확인 가능한 광주 웨딩 박람회 정보를 최대한 안정적으로 모으도록 설계돼 있습니다. 다만 아래 항목은 기술적으로 100% 보장할 수 없습니다.

- 비공개 랜딩 페이지로만 열리는 행사
- 새로 생겼지만 아직 참조 소스에 노출되지 않은 행사
- 외부 사이트 DOM 구조 변경
- 캘린더형 SPA 페이지의 일시적 로딩 실패

대신 이 저장소는 “누락을 모르고 지나가는 상태”를 줄이기 위해 다음 안전장치를 둡니다.

- 공개 참조 소스 대비 커버리지 감사
- 헬스 리포트와 최근 실행 결과 저장
- 본실행 전 프리체크
- 연속 실패, 연속 0건 서킷 브레이커
- 테스트로 파서와 저장 로직 회귀 방지

## 2. 현재 수집 범위

현재 기본 운영은 `PRODUCTION_SOURCE_MODE=true` 기준으로, 검증된 활성 소스셋만 사용합니다.

대표 정적 소스:

- `더베스트웨딩`
- `광주웨딩페스타`
- `웨딩고-광주`
- `웨딩다모아-전라도`
- `Wedding Fair Schedule`
- `한국웨딩연합회-전라도`
- `웨딩모멘트-전라도`
- `전라도웨딩박람회`

대표 동적 소스:

- `웨딩다모아-전라도-Dynamic`
- `한국웨딩연합회-전라도-Dynamic`
- `광주웨딩페스타-Dynamic`
- `웨딩모멘트-전라도-Dynamic`

핵심 참조 소스:

- `웨딩고-광주`

참조 소스는 “실제 운영 데이터가 빠졌는지”를 검사하는 기준으로도 사용됩니다.

## 3. 데이터 처리 방식

실행 흐름은 다음과 같습니다.

1. 정적 소스 수집
2. 동적 소스 수집
3. 날짜, 장소, 주관사, 출처 정규화
4. 오늘부터 3개월 범위 필터링
5. 동일 행사 병합
6. 커버리지 감사
7. SQLite와 CSV 저장
8. 필요 시 GitHub, 티스토리, 알림 실행

### 3.1 날짜 필터링 기준

이 프로그램은 “향후 3개월”을 다음처럼 해석합니다.

- 시작일이 오늘 이후인 행사
- 이미 시작했더라도 종료일이 오늘 이후인 진행 중 행사
- 시작일이 오늘부터 3개월 이내인 행사

즉 오늘이 `2026-03-28`이면 `2026-03-27 ~ 2026-03-29` 행사도 살아 있어야 합니다. 이 기준 때문에 `염주종합체육관`처럼 이미 시작된 박람회도 정상 수집 대상입니다.

### 3.2 canonical 병합 기준

같은 행사가 여러 사이트에서 조금 다르게 표기될 수 있으므로 다음을 고려해 병합합니다.

- 행사명 canonicalization
- 시작일과 종료일
- 장소 alias 정규화
- 출처 우선순위
- 더 구체적인 장소 문자열 선호
- 비어 있지 않은 필드 수 선호

예를 들어 `광주 웨딩 페스타`와 `광주웨딩페스타`는 같은 행사로 취급할 수 있고, `메리포엠` 계열은 더 정확한 `메리포엠웨딩홀` 레코드가 선택되도록 설계돼 있습니다.

## 4. 저장 결과

기본 산출물은 아래 세 파일입니다.

- CSV: `data/gwangju_wedding_expos.csv`
- SQLite: `data/wedding_expos.db`
- 소스 헬스 상태: `data/source_health.json`

최신 실행 리포트는 아래 파일에 저장됩니다.

- `data/logs/latest_source_health_report.json`

CSV 컬럼은 다음과 같습니다.

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

현재 저장은 append가 아니라 snapshot 방식입니다. 즉 실행이 끝나면 최신 canonical 결과로 DB와 CSV를 다시 맞춥니다. 이 방식은 오래된 행사가 남아 있거나, 테스트 데이터가 운영 CSV에 섞이는 문제를 막기 위한 것입니다.

## 5. 실행 방법

### 5.1 설치

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
pip install -r requirements.txt
playwright install chromium
```

### 5.2 점검 전용 실행

저장, GitHub, 티스토리, 알림 없이 수집과 검증만 실행합니다.

```bash
python3 main.py --dry-run --skip-github --skip-tistory --skip-notify
```

이 모드는 아래 확인에 적합합니다.

- 오늘 기준으로 실제 데이터가 잘 수집되는지
- 누락이 있는지
- 소스 상태가 정상인지
- 본실행을 해도 되는지

### 5.3 일반 실행

```bash
python3 main.py
```

### 5.4 권장 운영 실행

```bash
bash scripts/run_production_guarded.sh
```

이 스크립트는 다음을 수행합니다.

1. `dry-run` 프리체크
2. 헬스 리포트 검사
3. 커버리지 누락 여부 검사
4. 조건을 만족하면 본실행
5. 성공 시 자동 릴리즈 시도

## 6. `main.py` 옵션

`main.py`는 아래 옵션을 지원합니다.

- `--dry-run`: 저장과 외부 연동 없이 수집과 검증만 수행
- `--skip-github`: GitHub 동기화 생략
- `--skip-tistory`: 티스토리 포스팅 생략
- `--skip-notify`: Discord와 Telegram 알림 생략
- `--ignore-health`: 서킷 브레이커로 제외된 소스도 강제로 실행

운영 중 대부분은 `scripts/run_production_guarded.sh`를 쓰는 편이 안전합니다.

## 7. 커버리지 감사

이 저장소는 단순히 “몇 건 수집했는지”만 보지 않고, 참조 소스 대비 빠진 행사가 있는지 검사합니다.

감사 결과는 최신 리포트에 다음 형태로 기록됩니다.

- `coverage_reference_count`
- `coverage_matched_count`
- `coverage_missing_count`
- `coverage_missing_expos`
- `coverage_reference_sources`

운영 가드 스크립트는 아래 상황에서 본실행을 중단합니다.

- 최종 유효 데이터가 0건
- 참조 소스에서 1건도 확인하지 못함
- 참조 소스 대비 누락이 존재함
- 핵심 직결 소스가 전부 0건 상태

## 8. 서킷 브레이커

소스가 일시적으로 죽거나, 살아 있어도 계속 0건만 반환하는 경우 자동으로 격리합니다.

관련 설정값:

- `SOURCE_FAILURE_THRESHOLD`
- `SOURCE_ZERO_RESULT_THRESHOLD`
- `SOURCE_COOLDOWN_HOURS`

정책은 다음과 같습니다.

- 연속 실패가 임계치를 넘으면 격리
- 연속 0건이 임계치를 넘으면 격리
- cooldown 기간이 지나면 다시 실행 대상에 포함

이 상태는 `data/source_health.json`과 대시보드에서 확인할 수 있습니다.

## 9. 대시보드

```bash
streamlit run dashboard.py
```

대시보드에는 다음 영역이 있습니다.

- 전체 일정 목록
- 기본 통계
- 다가오는 일정
- 내보내기
- 소스 상태

특히 `소스 상태` 탭에서는 아래 정보를 볼 수 있습니다.

- 소스별 성공/실패 상태
- 연속 실패 수
- 연속 0건 수
- 최근 결과 수
- 이번 실행에서 제외된 소스와 사유
- 최신 헬스 요약

## 10. 자동 실행

크론 설치:

```bash
bash scripts/setup_cron.sh
```

크론에는 직접 `main.py`가 아니라 `run_production_guarded.sh`가 연결돼야 합니다. 그래야 프리체크와 가드가 함께 동작합니다.

설치 후 확인:

```bash
crontab -l
tail -f /tmp/wedding_expo_cron.log
```

## 11. GitHub 동기화와 자동 릴리즈

실행 후 자동으로 GitHub 반영과 릴리즈를 수행할 수 있습니다.

핵심 스크립트:

- Git 동기화: `wedding_expo_scraper/github_sync.py`
- 자동 릴리즈: `scripts/auto_release.py`

자동 릴리즈 제어 환경 변수:

- `AUTO_RELEASE_ON_SUCCESS=true`

수동 릴리즈 예시:

```bash
python3 scripts/auto_release.py --version v4.0.0
```

릴리즈 노트에는 보통 다음이 포함됩니다.

- 기준 커밋 정보
- CSV 행 수
- 일정 범위
- 최근 헬스 상태
- 제외된 소스와 사유

## 12. 티스토리와 알림

상세 문서는 아래를 참고하세요.

- 운영 절차: [docs/OPERATIONS.md](./docs/OPERATIONS.md)
- 티스토리 발행: [docs/TISTORY_WEEKLY.md](./docs/TISTORY_WEEKLY.md)
- 알림 설정: [docs/SETUP_NOTIFICATION.md](./docs/SETUP_NOTIFICATION.md)

기본 환경 변수:

- `DISCORD_WEBHOOK_URL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TISTORY_ACCESS_TOKEN`
- `TISTORY_BLOG_NAME`
- `TISTORY_CATEGORY_ID`
- `TISTORY_TAGS`

## 13. 테스트

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 -m pytest -q
python3 -m py_compile main.py wedding_expo_scraper/*.py scripts/*.py tests/*.py
```

현재 테스트는 아래 내용을 포함합니다.

- 파서 날짜 정규화
- 장소 alias 정규화
- ongoing 행사 유지 여부
- canonical dedupe 품질 선택
- 커버리지 감사
- 소스 헬스와 서킷 브레이커
- dry-run 동작
- 저장 스냅샷 교체
- 테스트가 운영 CSV를 오염시키지 않는지

## 14. 주요 파일

- 메인 실행: [main.py](/home/zenith/Desktop/wedding_expo_scraper/main.py)
- 설정: [config.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/config.py)
- 정적 스크래퍼: [scraper.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/scraper.py)
- 동적 스크래퍼: [dynamic_scraper.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/dynamic_scraper.py)
- 파서: [parser.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/parser.py)
- 저장: [storage.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/storage.py)
- 헬스 상태: [source_health.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/source_health.py)
- 커버리지 감사: [coverage_audit.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/coverage_audit.py)
- 운영 스크립트: [scripts/run_production_guarded.sh](/home/zenith/Desktop/wedding_expo_scraper/scripts/run_production_guarded.sh)
- 자동 릴리즈: [scripts/auto_release.py](/home/zenith/Desktop/wedding_expo_scraper/scripts/auto_release.py)

## 15. 현재 운영 판단 기준

운영 상태를 빠르게 판단하려면 다음 세 가지를 함께 봐야 합니다.

1. `data/gwangju_wedding_expos.csv`에 오늘 기준 유효한 박람회가 실제로 들어왔는지
2. `data/logs/latest_source_health_report.json`에서 `coverage_missing_count`가 0인지
3. 대시보드 `소스 상태` 탭에서 핵심 소스가 장기 0건 또는 장기 실패 상태가 아닌지

이 세 가지가 맞으면 현재 공개 웹 기준으로는 정상 수집이라고 판단할 수 있습니다.
