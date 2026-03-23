#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tistory 웹 로그인 기반 주간 발행 도구

Playwright로 티스토리 관리자 페이지에 로그인한 뒤 글을 작성하고 발행한다.
API 대신 브라우저 기반으로 동작하므로, 첫 설정 시 로그인 세션 저장이 필요하다.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from .config import CSV_PATH, PROJECT_ROOT
from .tistory_publisher import build_weekly_post

logger = logging.getLogger(__name__)

TISTORY_MANAGE_NEWPOST_PATH = "/manage/newpost/?type=post"
DEFAULT_STORAGE_STATE_PATH = PROJECT_ROOT / "data" / "tistory_storage_state.json"
DEFAULT_HEADLESS = True


def build_manage_url(blog_name: str) -> str:
    blog_name = blog_name.strip()
    if not blog_name:
        raise ValueError("blog_name is required")
    if blog_name.startswith("http://") or blog_name.startswith("https://"):
        return f"{blog_name.rstrip('/')}{TISTORY_MANAGE_NEWPOST_PATH}"
    return f"https://{blog_name}.tistory.com{TISTORY_MANAGE_NEWPOST_PATH}"


def _decode_state_b64(encoded: str) -> Dict[str, object]:
    raw = base64.b64decode(encoded.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def _encode_state_file(state_path: Path) -> str:
    return base64.b64encode(state_path.read_bytes()).decode("utf-8")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _first_visible(page, selectors: List[str]):
    for selector in selectors:
        locator = page.locator(selector)
        if locator.count() > 0:
            try:
                if locator.first.is_visible():
                    return locator.first
            except Exception:
                return locator.first
    return None


def _set_input_value(page, selectors: List[str], value: str) -> bool:
    locator = _first_visible(page, selectors)
    if locator is None:
        return False

    try:
        locator.click(force=True)
    except Exception:
        pass

    try:
        locator.fill(value)
        return True
    except Exception:
        try:
            locator.evaluate(
                """
                (el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """,
                value,
            )
            return True
        except Exception:
            return False


def _inject_html_into_page(page, html_content: str) -> bool:
    js = """
    (value) => {
        const editors = [];
        if (window.tinymce && tinymce.activeEditor) editors.push(() => tinymce.activeEditor.setContent(value));
        if (window.CKEDITOR) {
            Object.values(CKEDITOR.instances || {}).forEach((editor) => editors.push(() => editor.setData(value)));
        }
        if (window.editor && typeof window.editor.setHTML === 'function') {
            editors.push(() => window.editor.setHTML(value));
        }
        if (editors.length > 0) {
            editors[0]();
            return 'script';
        }
        return 'fallback';
    }
    """

    try:
        result = page.evaluate(js, html_content)
        if result == "script":
            return True
    except Exception:
        pass

    candidates = [
        '[contenteditable="true"]',
        'iframe',
        'textarea',
    ]

    for selector in candidates:
        try:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            element = locator.first
            if selector == 'iframe':
                frame = element.content_frame()
                if frame is None:
                    continue
                for frame_selector in ['[contenteditable="true"]', 'body', 'textarea']:
                    target = frame.locator(frame_selector)
                    if target.count() == 0:
                        continue
                    try:
                        if frame_selector == 'textarea':
                            target.first.fill(html_content)
                        else:
                            target.first.click(force=True)
                            page.keyboard.press("Control+A")
                            page.keyboard.insert_text(html_content)
                        return True
                    except Exception:
                        continue
            elif selector == 'textarea':
                element.fill(html_content)
                return True
            else:
                element.click(force=True)
                try:
                    page.keyboard.press("Control+A")
                except Exception:
                    pass
                page.keyboard.insert_text(html_content)
                return True
        except Exception:
            continue

    return False


def _click_publish(page) -> bool:
    selectors = [
        'button:has-text("발행")',
        'button:has-text("등록")',
        'button:has-text("공개")',
        '[role="button"]:has-text("발행")',
        '[role="button"]:has-text("등록")',
        '[role="button"]:has-text("공개")',
        'text=발행',
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() == 0:
                continue
            locator.first.click(force=True)
            return True
        except Exception:
            continue

    return False


@dataclass
class PublishResult:
    title: str
    published_url: str
    score: int


class TistoryWebPublisher:
    def __init__(
        self,
        blog_name: str,
        storage_state_path: Path = DEFAULT_STORAGE_STATE_PATH,
        headless: bool = DEFAULT_HEADLESS,
    ):
        self.blog_name = blog_name.strip()
        self.storage_state_path = storage_state_path
        self.headless = headless

    @property
    def manage_url(self) -> str:
        return build_manage_url(self.blog_name)

    def save_storage_state_from_logged_in_browser(self, output_path: Optional[Path] = None) -> Path:
        output_path = output_path or self.storage_state_path
        _ensure_parent(output_path)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self.manage_url, wait_until="domcontentloaded")
            logger.info("브라우저가 열렸습니다. 티스토리에 로그인한 뒤, 이 터미널로 돌아와 Enter를 누르세요.")
            input()
            context.storage_state(path=str(output_path))
            browser.close()

        logger.info("로그인 세션 저장 완료: %s", output_path)
        return output_path

    def save_storage_state_from_b64(self, encoded: str, output_path: Optional[Path] = None) -> Path:
        output_path = output_path or self.storage_state_path
        _ensure_parent(output_path)
        state = _decode_state_b64(encoded)
        output_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def export_storage_state_b64(self, state_path: Optional[Path] = None) -> str:
        state_path = state_path or self.storage_state_path
        if not state_path.exists():
            raise FileNotFoundError(state_path)
        return _encode_state_file(state_path)

    def _load_context(self, browser):
        kwargs = {"viewport": {"width": 1440, "height": 1600}}
        if self.storage_state_path.exists():
            kwargs["storage_state"] = str(self.storage_state_path)
        return browser.new_context(**kwargs)

    def _fill_editor(self, page, html_content: str) -> None:
        if not _set_input_value(
            page,
            [
                'input[placeholder*="제목"]',
                'input[title*="제목"]',
                'input[name*="title"]',
                'textarea[placeholder*="제목"]',
                'input[type="text"]',
            ],
            html_content,
        ):
            raise RuntimeError("제목 입력창을 찾지 못했습니다.")

        if not _inject_html_into_page(page, html_content):
            raise RuntimeError("본문 편집기를 찾지 못했습니다.")

    def publish(self, title: str, content: str) -> PublishResult:
        if not self.blog_name:
            raise ValueError("blog_name is required")
        if not self.storage_state_path.exists():
            raise FileNotFoundError(
                f"로그인 세션 파일이 없습니다: {self.storage_state_path}. "
                "먼저 --setup-login으로 세션을 저장하세요."
            )

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            context = self._load_context(browser)
            page = context.new_page()

            logger.info("티스토리 관리자 페이지 접속: %s", self.manage_url)
            page.goto(self.manage_url, wait_until="networkidle")

            if re.search(r"/auth/login|login", page.url, re.IGNORECASE):
                raise RuntimeError("로그인 세션이 만료되었습니다. 다시 로그인 세션을 저장하세요.")

            self._fill_editor(page, title)

            # 일부 에디터는 본문을 별도 frame이나 contenteditable로 관리한다.
            if not _inject_html_into_page(page, content):
                raise RuntimeError("본문을 편집기에 주입하지 못했습니다.")

            page.wait_for_timeout(1000)

            if not _click_publish(page):
                raise RuntimeError("발행 버튼을 찾지 못했습니다.")

            try:
                page.wait_for_timeout(3000)
            except PlaywrightTimeout:
                pass

            current_url = page.url
            context.storage_state(path=str(self.storage_state_path))
            browser.close()

        logger.info("티스토리 발행 완료: %s", current_url)
        return PublishResult(title=title, published_url=current_url, score=100)


def build_b64_secret_help(state_path: Path) -> str:
    encoded = _encode_state_file(state_path)
    return encoded[:16] + "..."


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Tistory 웹 로그인 기반 주간 발행")
    parser.add_argument("--blog-name", default=os.getenv("TISTORY_BLOG_NAME", ""), help="티스토리 블로그 이름")
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="입력 CSV 경로")
    parser.add_argument("--storage-state", type=Path, default=DEFAULT_STORAGE_STATE_PATH, help="로그인 세션 저장 파일")
    parser.add_argument("--setup-login", action="store_true", help="브라우저를 열어 로그인 세션을 저장")
    parser.add_argument("--export-state-b64", action="store_true", help="저장된 세션을 base64로 출력")
    parser.add_argument("--import-state-b64", type=str, default="", help="base64 인코딩된 세션을 저장")
    parser.add_argument("--dry-run", action="store_true", help="발행하지 않고 본문만 출력")
    parser.add_argument("--publish", action="store_true", help="실제 발행")
    parser.add_argument("--reference-date", type=str, default="", help="기준일(YYYY-MM-DD)")
    args = parser.parse_args(argv)

    publisher = TistoryWebPublisher(args.blog_name, storage_state_path=args.storage_state)

    if args.import_state_b64:
        publisher.save_storage_state_from_b64(args.import_state_b64, args.storage_state)
        logger.info("base64 세션을 저장했습니다: %s", args.storage_state)
        return 0

    if args.export_state_b64:
        print(publisher.export_storage_state_b64(args.storage_state))
        return 0

    if args.setup_login:
        publisher.save_storage_state_from_logged_in_browser(args.storage_state)
        return 0

    reference_date = None
    if args.reference_date:
        reference_date = datetime.strptime(args.reference_date, "%Y-%m-%d").date()

    payload = build_weekly_post(csv_path=args.csv, reference_date=reference_date)
    title = str(payload["title"])
    content = str(payload["content"])

    logger.info("주간 발행 준비 완료: %s", title)

    if args.dry_run or not args.publish:
        print(title)
        print(content)
        return 0

    result = publisher.publish(title, content)
    logger.info("발행 결과: %s", result.published_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
