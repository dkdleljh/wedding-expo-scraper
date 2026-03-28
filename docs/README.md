# 문서 안내

이 디렉터리는 운영 문서와 릴리즈 기록을 모아 둔 곳입니다. 실제 작업자는 아래 문서를 이 순서로 보는 편이 가장 효율적입니다.

## 1. 가장 먼저 볼 문서

- [../README.md](../README.md)
  - 프로젝트 전체 개요
  - 실행 방식
  - 수집 범위와 데이터 계약
  - 커버리지 감사와 서킷 브레이커 개념

- [./OPERATIONS.md](./OPERATIONS.md)
  - 실운영 절차
  - 크론 설치
  - 장애 대응
  - 가드 스크립트 사용법

- [./SETUP_NOTIFICATION.md](./SETUP_NOTIFICATION.md)
  - Discord, Telegram 알림 설정
  - 테스트 방법
  - 운영 시 확인 포인트

- [./TISTORY_WEEKLY.md](./TISTORY_WEEKLY.md)
  - 티스토리 주간 리포트 설정
  - API 발행과 웹 로그인 발행 차이
  - 주간 발행 절차

## 2. 문서별 역할

### README.md

루트 `README.md`는 현재 저장소를 운영하는 기준 문서입니다. 프로젝트 개요, 실행 명령, 데이터 저장 구조, 테스트 방법, 가드 실행, 자동 릴리즈까지 가장 넓은 범위를 설명합니다.

### OPERATIONS.md

실제 운영 담당자가 바로 써야 하는 실무 문서입니다. `dry-run`, 본실행, 크론, 헬스 상태, 서킷 브레이커, 커버리지 누락 대응 같은 항목은 이 문서를 기준으로 보면 됩니다.

### SETUP_NOTIFICATION.md

Discord와 Telegram 알림을 설정하는 방법을 설명합니다. 운영 중에는 성공 알림보다 실패 알림과 누락 감시가 더 중요하므로, 알림 채널 연결 상태는 반드시 사전에 점검해야 합니다.

### TISTORY_WEEKLY.md

수집 데이터로 주간 리포트를 티스토리에 발행하는 과정을 설명합니다. 일일 자동 수집과 주간 블로그 발행은 별도 경로이므로, 티스토리 운영자는 이 문서를 따로 확인해야 합니다.

## 3. 릴리즈 노트

아래 파일은 특정 시점의 릴리즈 기록입니다.

- `RELEASE_NOTES_v2.0.0.md`
- `RELEASE_NOTES_v2.1.0.md`
- `RELEASE_NOTES_v3.0.0.md`
- `RELEASE_NOTES_v3.1.0.md`
- `RELEASE_NOTES_v4.0.0.md`

릴리즈 노트는 역사 기록입니다. 현재 동작과 정확한 운영 기준은 항상 루트 [../README.md](../README.md)와 [./OPERATIONS.md](./OPERATIONS.md)를 우선으로 봐야 합니다.

## 4. 문서를 볼 때 주의할 점

이 프로젝트는 외부 웹 페이지 구조에 영향을 받습니다. 따라서 과거 문서에 적힌 아래 내용은 현재와 다를 수 있습니다.

- 총 소스 개수
- 예상 수집 건수
- 특정 사이트의 성공률
- 동적 페이지 대기 전략
- 릴리즈 버전별 상세 구현

최신 운영 상태를 확인할 때는 문서만 보지 말고 다음 파일도 같이 확인해야 합니다.

- `data/gwangju_wedding_expos.csv`
- `data/source_health.json`
- `data/logs/latest_source_health_report.json`

## 5. 추천 읽기 순서

처음 설치하거나 인수인계 받을 때:

1. [../README.md](../README.md)
2. [./OPERATIONS.md](./OPERATIONS.md)
3. [./SETUP_NOTIFICATION.md](./SETUP_NOTIFICATION.md)
4. [./TISTORY_WEEKLY.md](./TISTORY_WEEKLY.md)

장애가 났을 때:

1. [./OPERATIONS.md](./OPERATIONS.md)
2. `data/logs/latest_source_health_report.json`
3. `data/source_health.json`
4. [../README.md](../README.md)의 커버리지 감사, 서킷 브레이커 설명

티스토리 발행만 따로 점검할 때:

1. [./TISTORY_WEEKLY.md](./TISTORY_WEEKLY.md)
2. [./SETUP_NOTIFICATION.md](./SETUP_NOTIFICATION.md)

## 6. 이 문서 디렉터리의 목표

이 디렉터리의 목적은 “설정법을 장황하게 늘어놓는 것”이 아니라, 실제 운영 중 필요한 판단과 절차를 빠르게 찾게 하는 데 있습니다. 문서가 코드와 어긋나면 문서를 고치는 것이 우선입니다.
