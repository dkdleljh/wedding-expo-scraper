# 티스토리 주간 발행 가이드

이 문서는 수집된 웨딩 박람회 데이터를 티스토리 글로 발행하는 절차를 설명합니다. 이 저장소의 핵심은 CSV와 DB를 안정적으로 갱신하는 것이고, 티스토리 발행은 그 결과를 외부 채널로 전달하는 부가 운영 경로입니다.

## 1. 발행 경로 개요

이 저장소에는 두 가지 티스토리 발행 경로가 있습니다.

- API 기반 발행
- 웹 로그인 세션 기반 발행

관련 코드:

- [tistory_post.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_post.py)
- [tistory_publisher.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_publisher.py)
- [tistory_web_publisher.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_web_publisher.py)
- [scripts/publish_tistory_weekly.py](/home/zenith/Desktop/wedding_expo_scraper/scripts/publish_tistory_weekly.py)

일일 자동 실행에서는 간단 포스트용 경로가 사용될 수 있고, 주간 리포트는 별도 스크립트로 더 명시적으로 운영하는 편이 안전합니다.

## 2. 언제 쓰는 문서인가

이 문서는 아래 상황에서 확인합니다.

- 주간 웨딩 박람회 요약 글을 자동 또는 반자동으로 발행할 때
- 티스토리 인증 설정을 새로 할 때
- API 방식과 웹 로그인 방식을 비교할 때
- 발행 오류를 디버깅할 때

## 3. 필요한 환경 변수

### 3.1 API 방식

- `TISTORY_ACCESS_TOKEN`
- `TISTORY_BLOG_NAME`
- `TISTORY_CATEGORY_ID`
- `TISTORY_TAGS`
- `TISTORY_VISIBILITY`
- `TISTORY_ACCEPT_COMMENT`

### 3.2 웹 로그인 방식

- `TISTORY_BLOG_NAME`
- 세션 파일 또는 base64 세션 문자열

기본 세션 파일 경로:

- `data/tistory_storage_state.json`

## 4. 권장 운영 순서

티스토리 발행은 아래 순서로 운영하는 것이 안전합니다.

1. 수집과 저장이 정상인지 먼저 확인
2. `dry-run`으로 주간 본문을 미리 확인
3. 이상이 없으면 실제 발행
4. 발행 후 티스토리 편집 화면이나 블로그에서 결과 확인

즉 티스토리 발행은 수집 파이프라인의 대체물이 아니라 후속 단계입니다.

## 5. 실행 명령

### 5.1 주간 리포트 미리보기

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 scripts/publish_tistory_weekly.py --dry-run
```

이 명령은 실제 업로드 없이 생성될 제목과 본문을 확인할 때 사용합니다.

### 5.2 API 방식 실제 발행

```bash
python3 scripts/publish_tistory_weekly.py --publish
```

### 5.3 웹 로그인 세션 설정

```bash
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --setup-login
```

### 5.4 세션 base64 내보내기

```bash
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --export-state-b64
```

### 5.5 웹 로그인 방식 실제 발행

```bash
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --publish
```

## 6. 주간 리포트에 들어가는 내용

일반적으로 아래 항목이 포함됩니다.

- 현재 총 데이터 수
- 유효성 검증 통과 수
- 일정 분포
- 월별 분포
- 주요 장소
- 주관사 상위
- 가까운 일정 목록
- 대표 박람회 요약

중요한 점은, 본문 품질은 CSV와 DB의 품질에 직접 의존한다는 것입니다. 즉 발행 품질을 올리려면 티스토리 쪽보다 먼저 수집 데이터 품질을 확보해야 합니다.

## 7. API 방식과 웹 로그인 방식의 차이

### API 방식 장점

- 구조가 단순함
- 인증만 정상이면 반복 실행이 쉬움
- UI 변경의 영향을 덜 받음

### API 방식 단점

- 토큰 만료나 권한 이슈가 발생할 수 있음
- 티스토리 API 제약에 영향을 받음

### 웹 로그인 방식 장점

- 브라우저 기반 편집기 흐름을 그대로 사용할 수 있음
- API 제약을 우회할 수 있는 경우가 있음

### 웹 로그인 방식 단점

- 에디터 UI 변경에 취약함
- 세션 만료 문제를 관리해야 함
- Playwright 환경이 필요함

운영 안정성을 우선하면 가능하면 API 방식을 기본으로 두고, 웹 로그인 방식은 보조 수단으로 쓰는 편이 낫습니다.

## 8. 발행 전 체크리스트

실제 발행 전에 아래를 확인합니다.

- `data/gwangju_wedding_expos.csv`가 최신 상태인지
- `coverage_missing_count == 0`인지
- 이번 주간 글에 들어갈 데이터가 충분한지
- 티스토리 인증 정보가 유효한지
- `--dry-run` 출력이 자연스러운지

## 9. 자주 발생하는 문제

### 9.1 발행은 되는데 내용이 이상한 경우

보통 원인은 수집 데이터 품질입니다. 아래를 확인합니다.

1. CSV에 잘못된 장소나 날짜가 들어갔는지
2. 진행 중 행사 필터가 잘못 적용됐는지
3. canonical 병합이 잘못돼 다른 출처의 덜 정확한 레코드가 선택됐는지

### 9.2 웹 로그인 발행이 실패하는 경우

점검 순서:

1. 세션 파일이 아직 유효한지 확인
2. 티스토리 로그인 페이지 구조가 바뀌지 않았는지 확인
3. Playwright 브라우저 설치 상태 확인
4. `--setup-login`을 다시 수행

### 9.3 API 발행이 실패하는 경우

점검 순서:

1. `TISTORY_ACCESS_TOKEN` 유효성 확인
2. 블로그 이름과 카테고리 설정 확인
3. 공개 범위와 댓글 허용 설정값 확인
4. 네트워크 또는 티스토리 API 응답 확인

## 10. 운영 팁

- 실제 발행 전에 항상 `--dry-run`을 먼저 실행
- CSV가 비정상일 때는 티스토리 발행을 하지 말고 수집 파이프라인부터 수정
- 주간 리포트는 자동화돼 있어도 사람이 제목과 본문 톤을 한 번 확인하는 편이 안전
- 웹 로그인 방식은 장기 무인 운영보다는 예비 수단으로 보는 편이 현실적
