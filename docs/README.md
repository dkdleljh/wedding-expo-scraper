# 문서 안내

현재 운영 기준으로 우선 보는 문서는 아래 세 개입니다.

- [../README.md](../README.md): 전체 실행 방식, 운영 모드, 데이터 계약
- [./OPERATIONS.md](./OPERATIONS.md): 실운영 절차, 크론, 헬스 정책, 릴리즈 자동화
- [./TISTORY_WEEKLY.md](./TISTORY_WEEKLY.md): 티스토리 주간 발행 설정과 실행 방법
- [./SETUP_NOTIFICATION.md](./SETUP_NOTIFICATION.md): Discord/Telegram 알림 설정

릴리즈 노트는 역사적 기록으로 유지합니다.

- `RELEASE_NOTES_v4.0.0.md`
- `RELEASE_NOTES_v3.1.0.md`
- `RELEASE_NOTES_v3.0.0.md`
- `RELEASE_NOTES_v2.1.0.md`
- `RELEASE_NOTES_v2.0.0.md`

## 현재 운영 포인트

- 기본 실행은 `scripts/run_production_guarded.sh`
- 직접 점검은 `python3 main.py --dry-run --skip-github --skip-tistory --skip-notify`
- 소스 상태는 `data/source_health.json`
- 최신 헬스 리포트는 `data/logs/latest_source_health_report.json`
- 자동 릴리즈는 `scripts/auto_release.py`

## 참고

예전 문서에 적힌 수집 건수, 점수, 전체 소스 수치는 현재 운영 상태와 다를 수 있습니다. 최신 동작과 정책은 항상 [../README.md](../README.md)를 기준으로 봐야 합니다.
