# 티스토리 주간 자동 발행

이 프로젝트는 `data/gwangju_wedding_expos.csv`의 현재 상태를 요약해서 티스토리 블로그에 매주 자동 발행할 수 있습니다.

## 동작 방식

1. CSV를 읽어서 총 건수, 필수 필드 충족 여부, 월별 분포, 주관사 상위, 주요 장소, 다음 일정 5건을 계산합니다.
2. HTML 본문을 생성합니다.
3. 티스토리 `post/write` API로 발행합니다.

## 필요한 환경 변수

- `TISTORY_ACCESS_TOKEN`
- `TISTORY_BLOG_NAME`
- `TISTORY_CATEGORY_ID` 선택
- `TISTORY_TAGS`
- `GITHUB_REPO_URL` 선택

## 로컬 미리보기

```bash
python scripts/publish_tistory_weekly.py --dry-run
```

## 실제 발행

```bash
python scripts/publish_tistory_weekly.py --publish
```

## GitHub Actions

워크플로우는 [`.github/workflows/tistory_weekly.yml`](../.github/workflows/tistory_weekly.yml)에 있습니다.
매주 월요일 00:00 UTC, 한국 시간 기준 월요일 오전 9시에 실행됩니다.

## 주의사항

- 티스토리 API는 계정과 권한 상태에 따라 동작이 달라질 수 있습니다.
- 실제 발행 전에 `--dry-run`으로 본문을 먼저 확인하는 것이 안전합니다.
