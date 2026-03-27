# 티스토리 주간 발행

이 프로젝트는 CSV 상태를 요약해 티스토리에 발행하는 두 가지 경로를 제공합니다.

- API 기반: [tistory_publisher.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_publisher.py)
- 웹 로그인 기반: [tistory_web_publisher.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_web_publisher.py)

`main.py`의 일일 실행은 간단 포스트용 [tistory_post.py](/home/zenith/Desktop/wedding_expo_scraper/wedding_expo_scraper/tistory_post.py)를 사용하고, 주간 리포트/세션 기반 발행은 별도 스크립트로 운용합니다.

## 필요한 값

API 방식:

- `TISTORY_ACCESS_TOKEN`
- `TISTORY_BLOG_NAME`
- `TISTORY_CATEGORY_ID` 선택
- `TISTORY_TAGS` 선택

웹 로그인 방식:

- `TISTORY_BLOG_NAME`
- 로컬 세션 파일: `data/tistory_storage_state.json`
- 또는 base64 세션 문자열

## 주간 리포트 미리보기

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 scripts/publish_tistory_weekly.py --dry-run
```

## API 방식 실제 발행

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 scripts/publish_tistory_weekly.py --publish
```

## 웹 로그인 방식

로그인 세션 저장:

```bash
cd /home/zenith/Desktop/wedding_expo_scraper
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --setup-login
```

세션 base64 내보내기:

```bash
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --export-state-b64
```

웹 발행:

```bash
python3 scripts/publish_tistory_weekly.py --blog-name YOUR_BLOG_NAME --publish
```

## 동작 내용

주간 리포트는 다음을 포함합니다.

- 총 데이터 수
- 검증 통과 수
- 필수 필드 충족 현황
- 월별 분포
- 주관사 상위
- 주요 장소
- 다음 일정 5건

## 주의사항

- 웹 로그인 방식은 티스토리 에디터 UI 변경의 영향을 받을 수 있습니다.
- 실제 발행 전에는 `--dry-run`으로 본문을 먼저 확인하는 편이 안전합니다.
- 일일 자동 실행과 주간 발행은 별도 경로이므로, 주간 포스트 품질을 따로 검토해야 합니다.
