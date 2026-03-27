# 운영 가이드

이 문서는 현재 저장소를 실운영할 때 필요한 절차를 한 곳에 모은 문서입니다.

## 1. 권장 실행 경로

직접 `python3 main.py`를 크론에 붙이지 말고 아래 스크립트를 사용합니다.

```bash
bash /home/zenith/Desktop/wedding_expo_scraper/scripts/run_production_guarded.sh
```

이 스크립트는 다음 순서로 동작합니다.

1. `dry-run` 프리체크
2. 헬스 리포트 검증
3. 조건이 괜찮으면 본실행
4. 성공 후 자동 릴리즈 시도

## 2. 점검 명령

저장/배포 없이 수집 상태만 확인:

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 main.py --dry-run --skip-github --skip-tistory --skip-notify
```

프로덕션 소스셋 헬스 요약만 보기:

```bash
python3 scripts/healthcheck_sources.py
```

## 3. 헬스 파일

- 상태 저장: `data/source_health.json`
- 최신 리포트: `data/logs/latest_source_health_report.json`

헬스 리포트에는 다음이 포함됩니다.

- 체크된 소스 수
- 성공/실패 소스 수
- 이번 실행에서 제외된 소스와 사유
- 각 소스별 결과 수와 오류 상태

## 4. 서킷 브레이커 정책

기본 정책은 설정값으로 조절합니다.

- `SOURCE_FAILURE_THRESHOLD`
- `SOURCE_ZERO_RESULT_THRESHOLD`
- `SOURCE_COOLDOWN_HOURS`

의미:

- 연속 실패가 임계치를 넘으면 격리
- 연속 0건이 임계치를 넘으면 격리
- 격리된 소스는 cooldown 시간 동안 실행 대상에서 제외

## 5. 자동 릴리즈

운영 스크립트는 기본적으로 실행 성공 후 릴리즈를 시도합니다.

- 제어 환경 변수: `AUTO_RELEASE_ON_SUCCESS`
- 기본값: `true`

끄기:

```bash
AUTO_RELEASE_ON_SUCCESS=false bash scripts/run_production_guarded.sh
```

수동 릴리즈:

```bash
python3 scripts/auto_release.py --version v4.0.0
```

## 6. 크론 설치

```bash
bash /home/zenith/Desktop/wedding_expo_scraper/scripts/setup_cron.sh
```

설치 후 확인:

```bash
crontab -l
tail -f /tmp/wedding_expo_cron.log
```

## 7. 문제 대응

소스가 반복 실패하거나 0건인 경우:

1. 대시보드 `소스 상태` 탭 확인
2. `data/source_health.json` 확인
3. 필요 시 cooldown이 끝날 때까지 기다리거나 설정값 조정
4. 특정 소스를 프로덕션 소스셋에서 제거할지 검토

GitHub 릴리즈가 안 올라가는 경우:

1. `gh auth status` 확인
2. `scripts/auto_release.py` 수동 실행
3. `data/logs/release_latest.log` 확인
