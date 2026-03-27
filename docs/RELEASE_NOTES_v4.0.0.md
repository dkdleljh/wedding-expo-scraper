# Release Notes v4.0.0

## 개요

이번 버전은 단순 스크래퍼를 운영형 파이프라인으로 끌어올리는 데 초점을 둔 메이저 업데이트입니다.

## 핵심 변경

- 프로덕션 소스 모드 도입
- 정적/동적/운영 정책 분리
- canonical dedupe 적용
- 행사명 canonicalization 적용
- 연속 실패/연속 0건 기반 서킷 브레이커 추가
- dry-run 프리체크 추가
- guarded run 스크립트 추가
- 소스 헬스 상태 파일과 최신 리포트 파일 추가
- 대시보드 `소스 상태` 탭 추가
- 자동 태그/릴리즈 스크립트 정비
- README 및 운영 문서 전면 한글 재작성

## 운영 영향

- 직접 `main.py`를 크론에 붙이는 대신 `scripts/run_production_guarded.sh` 사용 권장
- 저장/푸시/포스팅 없이도 안전한 프리체크 가능
- 품질이 낮은 소스는 시간이 지나며 자동으로 격리
- 릴리즈 노트에 헬스 리포트 정보 포함

## 검증

- 테스트 통과
- dry-run 실실행 확인
- 프로덕션 헬스체크 확인

## 권장 명령

```bash
bash scripts/run_production_guarded.sh
```
