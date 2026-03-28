# Release Notes v4.0.1

릴리즈 날짜: 2026-03-28
기준 커밋: `6a708fe`

## 요약

이번 릴리즈는 운영 CSV가 테스트 데이터로 오염될 수 있던 문제를 해결하고, 실제 광주 웨딩 박람회 데이터와 운영 문서를 현재 코드 기준으로 다시 정렬한 패치 릴리즈입니다.

## 핵심 수정

- 테스트가 운영 CSV를 덮어쓰지 않도록 저장소 경로를 분리했습니다.
- `DataStorage`가 사용자 지정 `csv_path`를 받을 수 있도록 수정했습니다.
- 저장 테스트가 임시 CSV만 사용하도록 바꿨습니다.
- 실제 수집을 다시 실행해 `data/gwangju_wedding_expos.csv`와 `data/wedding_expos.db`를 최신 상태로 갱신했습니다.
- `염주종합체육관` 행사 누락이 없는지 다시 검증했습니다.

## 현재 데이터 상태

최신 저장 결과:

- 최종 유효 데이터: 8건
- 참조 소스 수: 5건
- 참조 소스 매칭: 5건
- 커버리지 누락: 0건

CSV에 포함된 대표 행사:

- 광주 연합 웨딩박람회
- 광주 초대형 웨딩박람회
- 광주 컨벤션 웨딩박람회
- 광주웨딩페스타
- 광주 메리포엠 웨딩페어
- 광주 스타일링 웨딩페어

## 문서 업데이트

아래 문서를 현재 운영 기준으로 전면 정리했습니다.

- `README.md`
- `docs/README.md`
- `docs/OPERATIONS.md`
- `docs/SETUP_NOTIFICATION.md`
- `docs/TISTORY_WEEKLY.md`

문서에는 다음 내용이 반영됐습니다.

- 현재 수집 범위와 한계
- 커버리지 감사와 서킷 브레이커 정책
- `dry-run`과 가드 실행 절차
- 크론 운영 기준
- 티스토리 발행 절차
- Discord, Telegram 알림 설정

## 검증

실행한 검증:

- `python3 -m pytest -q` → `47 passed`
- `python3 -m py_compile main.py wedding_expo_scraper/*.py scripts/*.py tests/*.py` → 통과
- `python3 main.py --skip-github --skip-tistory --skip-notify` → 성공

## 운영 판단

이 릴리즈 이후에는 다음이 보장돼야 정상입니다.

- 테스트 실행 후에도 운영 CSV가 유지됨
- CSV에 실제 광주 행사 데이터가 저장됨
- 최신 헬스 리포트에서 `coverage_missing_count == 0`
- `염주종합체육관` 행사 누락이 발생하지 않음
