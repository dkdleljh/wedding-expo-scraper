#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Release 자동 생성 스크립트"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from git import Repo
from git.exc import GitCommandError

from wedding_expo_scraper.config import CSV_PATH, SOURCE_HEALTH_REPORT_PATH

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SEMVER_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


class AutoRelease:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = Path(repo_path or Path(__file__).parent.parent)
        self.repo = Repo(self.repo_path)

    def _run_git(self, *args: str) -> str:
        return self.repo.git.execute(["git", *args]).strip()

    def get_latest_semver_tag(self) -> str:
        versions = []
        for tag in self.repo.tags:
            match = SEMVER_PATTERN.match(tag.name)
            if match:
                versions.append((tuple(int(part) for part in match.groups()), tag.name))
        if not versions:
            return "v0.0.0"
        versions.sort()
        return versions[-1][1]

    def head_is_tagged(self) -> bool:
        try:
            self._run_git("describe", "--tags", "--exact-match", "HEAD")
            return True
        except GitCommandError:
            return False

    def has_new_commits_since_tag(self, tag_name: str) -> bool:
        if tag_name == "v0.0.0":
            return True
        commits = self._run_git("rev-list", f"{tag_name}..HEAD", "--count")
        return int(commits or "0") > 0

    def bump_patch_version(self, version: str) -> str:
        match = SEMVER_PATTERN.match(version)
        if not match:
            raise ValueError(f"semver 태그가 아닙니다: {version}")
        major, minor, patch = (int(part) for part in match.groups())
        return f"v{major}.{minor}.{patch + 1}"

    def collect_release_context(self) -> dict:
        context = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "head_commit": self.repo.head.commit.hexsha[:8],
            "head_message": self.repo.head.commit.message.strip(),
            "csv_rows": 0,
            "health": {},
        }
        if CSV_PATH.exists():
            try:
                import pandas as pd

                df = pd.read_csv(CSV_PATH)
                context["csv_rows"] = len(df)
                if not df.empty and "start_date" in df.columns:
                    context["date_min"] = str(df["start_date"].min())
                    context["date_max"] = str(df["start_date"].max())
            except Exception:
                pass

        if SOURCE_HEALTH_REPORT_PATH.exists():
            try:
                context["health"] = json.loads(SOURCE_HEALTH_REPORT_PATH.read_text(encoding="utf-8"))
            except Exception:
                context["health"] = {}
        return context

    def create_release_notes(self, version: str) -> str:
        context = self.collect_release_context()
        health = context.get("health", {})
        checked = int(health.get("checked_sources", 0))
        healthy = int(health.get("healthy_sources", 0))
        failed = int(health.get("failed_sources", 0))
        skipped = health.get("skipped_sources", [])
        skipped_lines = "\n".join(
            f"- {item.get('name', '')}: {item.get('reason', '')}" for item in skipped
        ) or "- 없음"

        top_sources = health.get("sources", {})
        source_lines = []
        for source_name, stats in sorted(top_sources.items()):
            source_lines.append(
                f"- {source_name}: success={stats.get('success')} result_count={stats.get('result_count', 0)} kind={stats.get('kind', '')}"
            )
        source_summary = "\n".join(source_lines) or "- 없음"

        return f"""# {version}

## 배포 개요

- 배포 시각: {context.get('generated_at')}
- 기준 커밋: `{context.get('head_commit')}` {context.get('head_message')}
- CSV 행 수: {context.get('csv_rows', 0)}
- 일정 범위: {context.get('date_min', 'N/A')} ~ {context.get('date_max', 'N/A')}

## 이번 버전 핵심

- 프로덕션 소스 모드 도입
- canonical dedupe 및 행사명 canonicalization 적용
- 실패/연속 0건 기반 서킷 브레이커 추가
- dry-run, guarded run, source health report 운영 경로 추가
- 대시보드 소스 상태 탭 추가
- 문서 전면 한글 정비

## 소스 헬스 요약

- checked_sources: {checked}
- healthy_sources: {healthy}
- failed_sources: {failed}

### 이번 실행에서 제외된 소스
{skipped_lines}

### 최근 소스 실행 요약
{source_summary}
"""

    def create_tag(self, version: str, message: str) -> None:
        self.repo.create_tag(version, message=message)
        logger.info("✅ 태그 생성: %s", version)

    def push_tag(self, version: str) -> None:
        self.repo.remote("origin").push(version)
        logger.info("✅ 태그 푸시 완료: %s", version)

    def create_github_release(self, version: str, release_notes: str) -> None:
        notes_file = self.repo_path / f".release_notes_{version}.md"
        notes_file.write_text(release_notes, encoding="utf-8")
        try:
            subprocess.run(
                [
                    "gh",
                    "release",
                    "create",
                    version,
                    "--title",
                    f"Wedding Expo Scraper {version}",
                    "--notes-file",
                    str(notes_file),
                    "--latest",
                ],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("✅ GitHub Release 생성 완료: %s", version)
        finally:
            if notes_file.exists():
                notes_file.unlink()

    def run(self, version: Optional[str] = None, push: bool = True, create_release: bool = True) -> Optional[str]:
        if self.head_is_tagged():
            logger.info("HEAD가 이미 태그되어 있어 릴리즈를 건너뜁니다.")
            return None

        latest_tag = self.get_latest_semver_tag()
        if not self.has_new_commits_since_tag(latest_tag):
            logger.info("마지막 태그 이후 새 커밋이 없어 릴리즈를 건너뜁니다.")
            return None

        target_version = version or self.bump_patch_version(latest_tag)
        release_notes = self.create_release_notes(target_version)
        self.create_tag(target_version, release_notes)
        if push:
            self.push_tag(target_version)
        if create_release:
            self.create_github_release(target_version, release_notes)
        return target_version


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="GitHub Release 자동 생성")
    parser.add_argument("--version", default="", help="직접 지정할 태그 버전 (예: v4.0.0)")
    parser.add_argument("--no-push", action="store_true", help="태그 푸시 생략")
    parser.add_argument("--no-release", action="store_true", help="GitHub Release 생성 생략")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    releaser = AutoRelease()
    version = releaser.run(
        version=args.version or None,
        push=not args.no_push,
        create_release=not args.no_release,
    )
    if version:
        logger.info("🎉 릴리즈 완료: %s", version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
