# 운영 가이드

이 문서는 실제 운영자가 이 저장소를 점검하고, 실행하고, 장애를 처리할 때 필요한 절차를 정리한 문서입니다. 코드를 읽지 않고도 현재 상태를 판단할 수 있도록 운영 기준을 중심으로 설명합니다.

## 1. 운영 목표

운영의 목적은 단순히 스크립트를 한 번 실행하는 것이 아닙니다. 아래 세 조건을 동시에 만족해야 정상 운영으로 봅니다.

- 향후 3개월 범위의 광주 웨딩 박람회 데이터가 실제로 수집됨
- 참조 소스 대비 누락이 없음
- 저장 결과와 헬스 리포트가 함께 갱신됨

실행 성공 로그만 보고 정상이라고 판단하면 안 됩니다. 반드시 CSV와 최신 헬스 리포트를 같이 확인해야 합니다.

## 2. 권장 실행 경로

운영에서는 직접 `python3 main.py`를 크론에 연결하지 말고, 아래 스크립트를 사용합니다.

```bash
bash /home/zenith/Desktop/wedding_expo_scraper/scripts/run_production_guarded.sh
```

이 스크립트는 다음 순서로 동작합니다.

1. `dry-run` 프리체크
2. 최신 헬스 리포트 읽기
3. 최종 유효 건수 검사
4. 참조 소스 커버리지 검사
5. 핵심 소스 0건 상태 검사
6. 이상이 없을 때만 본실행
7. 성공 시 자동 릴리즈 시도

즉 이 스크립트는 “실행기”라기보다 “운영 가드”에 가깝습니다.

## 3. 가장 먼저 확인할 파일

운영 상태를 빠르게 파악하려면 다음 파일을 봅니다.

- `data/gwangju_wedding_expos.csv`
- `data/source_health.json`
- `data/logs/latest_source_health_report.json`
- `/tmp/wedding_expo_cron.log`

### 3.1 CSV에서 봐야 할 것

- 오늘 기준 유효한 행사가 실제로 들어왔는지
- 진행 중 행사도 남아 있는지
- 장소가 광주 상세 주소로 정규화돼 있는지
- 테스트용 더미 데이터가 섞이지 않았는지

### 3.2 헬스 리포트에서 봐야 할 것

중요 필드:

- `raw_count`
- `parsed_count`
- `final_valid_count`
- `coverage_reference_count`
- `coverage_matched_count`
- `coverage_missing_count`
- `zero_result_sources`
- `critical_zero_result_sources`
- `skipped_sources`

정상 기준:

- `final_valid_count > 0`
- `coverage_reference_count > 0`
- `coverage_missing_count == 0`

## 4. 점검 명령

### 4.1 저장 없이 점검

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 main.py --dry-run --skip-github --skip-tistory --skip-notify
```

이 명령은 다음 상황에서 사용합니다.

- 현재 데이터가 제대로 수집되는지 보고 싶을 때
- 외부 연동 없이 스크래핑만 재검증하고 싶을 때
- 크론 실행 전에 사람이 직접 확인할 때
- 장애 대응 중 저장 결과를 덮어쓰지 않고 확인하고 싶을 때

### 4.2 프로덕션 소스 헬스 점검

```bash
python3 scripts/healthcheck_sources.py
```

이 명령은 소스별 결과 수와 상태를 빠르게 보고 싶을 때 유용합니다.

### 4.3 실제 저장 포함 실행

```bash
python3 main.py --skip-github --skip-tistory --skip-notify
```

이 명령은 외부 배포 없이 실제 CSV와 DB를 갱신하고 싶을 때 사용합니다.

## 5. 크론 운영

크론 설치:

```bash
bash /home/zenith/Desktop/wedding_expo_scraper/scripts/setup_cron.sh
```

확인:

```bash
crontab -l
tail -f /tmp/wedding_expo_cron.log
```

운영 원칙:

- 크론에는 항상 `run_production_guarded.sh`를 연결
- `main.py` 직접 호출은 수동 디버깅이나 개발 확인용으로만 사용
- 크론 로그만 보지 말고 CSV와 최신 리포트를 같이 확인

## 6. 서킷 브레이커 정책

소스 상태는 `data/source_health.json`에 누적됩니다. 이 상태를 바탕으로 특정 소스를 자동으로 제외합니다.

관련 설정값:

- `SOURCE_FAILURE_THRESHOLD`
- `SOURCE_ZERO_RESULT_THRESHOLD`
- `SOURCE_COOLDOWN_HOURS`

정책:

- 연속 실패가 임계치를 넘으면 제외
- 연속 0건이 임계치를 넘으면 제외
- cooldown 기간이 지나면 재진입 허용

의도는 단순합니다. “계속 깨지는 소스 때문에 전체 실행을 오염시키지 말자”는 것입니다.

## 7. 커버리지 감사 정책

이 프로젝트는 공개 참조 소스를 기준으로 누락 여부를 추가 검사합니다.

현재 핵심 참조는 `웨딩고-광주`입니다. 운영 가드는 참조 소스 대비 누락이 존재하면 본실행을 막습니다.

아래 값은 특히 중요합니다.

- `coverage_reference_count`: 참조 소스에서 확인된 행사 수
- `coverage_matched_count`: 현재 최종 결과와 매칭된 행사 수
- `coverage_missing_count`: 참조 소스에는 있는데 최종 결과에 없는 행사 수
- `coverage_missing_expos`: 빠진 행사 상세

`coverage_missing_count > 0`이면 운영자는 바로 원인을 점검해야 합니다.

## 8. 자주 발생하는 장애 유형

### 8.1 실행은 성공했지만 CSV가 이상한 경우

점검 순서:

1. `data/gwangju_wedding_expos.csv` 직접 확인
2. `data/logs/latest_source_health_report.json` 확인
3. 최근 테스트가 실제 운영 CSV를 덮어쓰지 않았는지 확인
4. `python3 main.py --skip-github --skip-tistory --skip-notify` 재실행

현재 저장소는 테스트가 운영 CSV를 덮어쓰지 않도록 분리돼 있어야 정상입니다.

### 8.2 특정 행사만 빠진 경우

점검 순서:

1. 참조 소스에서 해당 행사가 아직 노출되는지 확인
2. 날짜 필터에 걸리지 않았는지 확인
3. 진행 중 행사인데 시작일 기준으로 잘못 잘리지 않았는지 확인
4. 장소 alias 때문에 정규화가 실패하지 않았는지 확인
5. `coverage_missing_expos`에 기록됐는지 확인

### 8.3 핵심 소스가 계속 0건인 경우

점검 순서:

1. `critical_zero_result_sources` 확인
2. 대시보드 `소스 상태` 탭 확인
3. 실제 사이트 DOM 변경 여부 확인
4. cooldown 종료 후 재시도 또는 파서 수정

### 8.4 GitHub 릴리즈가 안 되는 경우

점검 순서:

1. `gh auth status` 확인
2. `AUTO_RELEASE_ON_SUCCESS` 값 확인
3. `python3 scripts/auto_release.py --version vX.Y.Z` 수동 실행
4. `data/logs/release_latest.log` 확인

## 9. 운영 중 사람이 판단해야 하는 것

완전 무인 운영에 가깝게 구성돼 있어도, 아래 항목은 사람이 주기적으로 확인해야 합니다.

- 참조 소스가 여전히 유효한지
- 새 광주 박람회 소스가 생겼는지
- 특정 사이트가 구조를 바꿨는지
- 장소 alias 사전에 추가할 항목이 있는지
- 티스토리나 GitHub 인증이 만료되지 않았는지

즉 이 문서의 목표는 “사람이 매일 모든 걸 수동으로 하게 하는 것”이 아니라, “사람이 봐야 할 포인트를 좁히는 것”입니다.

## 10. 운영자가 자주 쓰는 명령 모음

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 main.py --dry-run --skip-github --skip-tistory --skip-notify
python3 main.py --skip-github --skip-tistory --skip-notify
python3 scripts/healthcheck_sources.py
python3 -m pytest -q
python3 -m py_compile main.py wedding_expo_scraper/*.py scripts/*.py tests/*.py
bash scripts/run_production_guarded.sh
```

## 11. 운영 종료 판단 기준

다음 조건이면 현재 운영은 정상으로 봐도 됩니다.

- CSV에 오늘 기준 유효한 광주 행사들이 들어 있음
- 참조 소스 대비 누락이 없음
- `critical_zero_result_sources`가 비어 있거나 허용 가능한 수준임
- 테스트가 통과함
- 크론 로그에 치명적 예외가 없음
