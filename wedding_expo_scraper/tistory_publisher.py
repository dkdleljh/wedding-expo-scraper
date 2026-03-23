#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tistory 주간 발행 도구

CSV의 현재 상태를 요약해서 티스토리 블로그에 자동 발행한다.
"""

from __future__ import annotations

import argparse
import html
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

from .config import (
    CSV_PATH,
    GITHUB_REPO_URL,
    TISTORY_ACCEPT_COMMENT,
    TISTORY_ACCESS_TOKEN,
    TISTORY_BLOG_NAME,
    TISTORY_CATEGORY_ID,
    TISTORY_TAGS,
    TISTORY_VISIBILITY,
)

logger = logging.getLogger(__name__)

TISTORY_POST_URL = "https://www.tistory.com/apis/post/write"
REQUIRED_COLUMNS = [
    "name",
    "start_date",
    "end_date",
    "operating_hours",
    "location",
    "organizer",
    "contact",
    "source_url",
    "description",
]


@dataclass(frozen=True)
class WeeklySummary:
    reference_date: date
    week_start: date
    week_end: date
    total_rows: int
    valid_rows: int
    score: int
    date_range: str
    required_field_counts: Dict[str, int]
    month_counts: List[Dict[str, str]]
    top_organizers: List[Dict[str, str]]
    top_locations: List[Dict[str, str]]
    upcoming_events: List[Dict[str, str]]


def _to_date(value: object) -> Optional[date]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _week_bounds(reference_date: date) -> tuple[date, date]:
    start = reference_date - timedelta(days=reference_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def _format_range(start_date: Optional[date], end_date: Optional[date]) -> str:
    if not start_date and not end_date:
        return "N/A"
    if start_date and end_date:
        if start_date == end_date:
            return start_date.strftime("%Y-%m-%d")
        return f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    if start_date:
        return start_date.strftime("%Y-%m-%d")
    return end_date.strftime("%Y-%m-%d")


def _normalize_location_label(location: str) -> str:
    text = str(location).strip()
    if not text:
        return "N/A"
    for separator in ("(", ","):
        if separator in text:
            text = text.split(separator, 1)[0].strip()
    return text or "N/A"


def load_dataframe(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = pd.read_csv(csv_path)
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df


def summarize_dataframe(df: pd.DataFrame, reference_date: Optional[date] = None) -> WeeklySummary:
    reference_date = reference_date or datetime.now().date()
    week_start, week_end = _week_bounds(reference_date)

    if df.empty:
        return WeeklySummary(
            reference_date=reference_date,
            week_start=week_start,
            week_end=week_end,
            total_rows=0,
            valid_rows=0,
            score=0,
            date_range="N/A",
            required_field_counts={column: 0 for column in REQUIRED_COLUMNS},
            month_counts=[],
            top_organizers=[],
            top_locations=[],
            upcoming_events=[],
        )

    data = df.copy()
    for column in REQUIRED_COLUMNS:
        if column not in data.columns:
            data[column] = ""

    data["_start_date"] = data["start_date"].apply(_to_date)
    data["_end_date"] = data["end_date"].apply(_to_date)
    data["_start_text"] = data["_start_date"].apply(lambda value: value.strftime("%Y-%m-%d") if value else "")
    data["_location_label"] = data["location"].apply(_normalize_location_label)

    valid_mask = data["start_date"].astype(str).str.strip().ne("") & data["end_date"].astype(str).str.strip().ne("")
    valid_mask &= data["location"].astype(str).str.strip().ne("") & data["source_url"].astype(str).str.strip().ne("")
    valid_rows = int(valid_mask.sum())

    start_dates = data["_start_date"].dropna()
    end_dates = data["_end_date"].dropna()
    if not start_dates.empty:
        date_range = _format_range(start_dates.min(), end_dates.max() if not end_dates.empty else start_dates.max())
    else:
        date_range = "N/A"

    required_field_counts = {
        column: int(data[column].fillna("").astype(str).str.strip().ne("").sum())
        for column in REQUIRED_COLUMNS
    }

    month_counts = []
    if not start_dates.empty:
        month_series = pd.Series([value.strftime("%Y-%m") for value in start_dates])
        for month, count in month_series.value_counts().sort_index().items():
            month_counts.append({"month": month, "count": str(int(count))})

    top_organizers = []
    organizer_series = data["organizer"].fillna("").astype(str).str.strip()
    for organizer, count in organizer_series[organizer_series.ne("")].value_counts().head(5).items():
        top_organizers.append({"name": organizer, "count": str(int(count))})

    top_locations = []
    location_series = data["_location_label"]
    for location, count in location_series[location_series.ne("N/A")].value_counts().head(5).items():
        top_locations.append({"name": location, "count": str(int(count))})

    upcoming_events: List[Dict[str, str]] = []
    upcoming = data[data["_start_date"].notna()].sort_values(["_start_date", "name"]).head(5)
    for _, row in upcoming.iterrows():
        upcoming_events.append(
            {
                "name": str(row.get("name", "")),
                "period": _format_range(row.get("_start_date"), row.get("_end_date")),
                "location": str(row.get("location", "")),
                "organizer": str(row.get("organizer", "")),
                "source_url": str(row.get("source_url", "")),
            }
        )

    field_score = sum(1 for column, count in required_field_counts.items() if count == len(data))
    score = round((field_score / len(REQUIRED_COLUMNS)) * 100)

    return WeeklySummary(
        reference_date=reference_date,
        week_start=week_start,
        week_end=week_end,
        total_rows=int(len(data)),
        valid_rows=valid_rows,
        score=score,
        date_range=date_range,
        required_field_counts=required_field_counts,
        month_counts=month_counts,
        top_organizers=top_organizers,
        top_locations=top_locations,
        upcoming_events=upcoming_events,
    )


def build_title(summary: WeeklySummary) -> str:
    return f"[주간 업데이트] 광주 웨딩박람회 점검 {summary.week_start:%Y-%m-%d} ~ {summary.week_end:%Y-%m-%d}"


def _render_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> str:
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    row_html = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row)
        row_html.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(row_html)}</tbody></table>"


def render_html(summary: WeeklySummary, repo_url: str = "", csv_url: str = "") -> str:
    quality_rows = [
        (column, f"{count}/{summary.total_rows}", "100%" if summary.total_rows and count == summary.total_rows else "검토 필요")
        for column, count in summary.required_field_counts.items()
    ]

    month_rows = [(item["month"], item["count"]) for item in summary.month_counts] or [("N/A", "0")]
    organizer_rows = [(item["name"], item["count"]) for item in summary.top_organizers] or [("N/A", "0")]
    location_rows = [(item["name"], item["count"]) for item in summary.top_locations] or [("N/A", "0")]
    event_rows = [
        (item["name"], item["period"], item["location"], item["organizer"], item["source_url"])
        for item in summary.upcoming_events
    ] or [("N/A", "N/A", "N/A", "N/A", "N/A")]

    parts = [
        "<div style=\"font-family: Arial, sans-serif; line-height: 1.7;\">",
        f"<h1>광주 웨딩박람회 주간 업데이트</h1>",
        f"<p><strong>기준일:</strong> {summary.reference_date:%Y-%m-%d}<br>",
        f"<strong>점검 구간:</strong> {summary.week_start:%Y-%m-%d} ~ {summary.week_end:%Y-%m-%d}<br>",
        f"<strong>총 데이터:</strong> {summary.total_rows}건<br>",
        f"<strong>검증 통과:</strong> {summary.valid_rows}건<br>",
        f"<strong>점검 점수:</strong> {summary.score}/100</p>",
        "<h2>필수 필드 검증</h2>",
        _render_table(["항목", "채움 수", "판정"], quality_rows),
        "<h2>월별 분포</h2>",
        _render_table(["월", "건수"], month_rows),
        "<h2>주관사 상위</h2>",
        _render_table(["주관사", "건수"], organizer_rows),
        "<h2>주요 장소</h2>",
        _render_table(["장소", "건수"], location_rows),
        "<h2>다음 일정</h2>",
        _render_table(["행사명", "기간", "장소", "주관사", "출처"], event_rows),
        "<h2>원본 링크</h2>",
    ]

    if csv_url:
        parts.append(f'<p><a href="{html.escape(csv_url)}">CSV 원본 보기</a></p>')
    if repo_url:
        parts.append(f'<p><a href="{html.escape(repo_url)}">프로젝트 저장소</a></p>')

    parts.append("</div>")
    return "\n".join(parts)


def build_weekly_post(csv_path: Path = CSV_PATH, reference_date: Optional[date] = None) -> Dict[str, object]:
    df = load_dataframe(csv_path)
    summary = summarize_dataframe(df, reference_date=reference_date)
    title = build_title(summary)
    csv_link = ""
    if GITHUB_REPO_URL:
        csv_link = f"{GITHUB_REPO_URL.rstrip('/')}/blob/main/data/{csv_path.name}"
    content = render_html(
        summary,
        repo_url=GITHUB_REPO_URL,
        csv_url=csv_link,
    )
    return {"title": title, "content": content, "summary": summary}


def publish_to_tistory(
    *,
    title: str,
    content: str,
    access_token: str,
    blog_name: str,
    category_id: str = "",
    visibility: int = TISTORY_VISIBILITY,
    accept_comment: int = TISTORY_ACCEPT_COMMENT,
    tags: str = TISTORY_TAGS,
    published: Optional[int] = None,
) -> Dict[str, object]:
    params = {
        "access_token": access_token,
        "output": "json",
        "blogName": blog_name,
        "title": title,
        "content": content,
        "visibility": visibility,
        "acceptComment": accept_comment,
    }
    if category_id:
        params["category"] = category_id
    if tags:
        params["tag"] = tags
    if published is not None:
        params["published"] = published

    response = requests.post(TISTORY_POST_URL, params=params, timeout=30)
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Tistory 응답 파싱 실패: {response.text[:200]}") from exc

    if payload.get("tistory", {}).get("status") != "200":
        raise RuntimeError(f"Tistory 발행 실패: {payload}")

    return payload


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="광주 웨딩박람회 주간 Tistory 발행")
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="입력 CSV 경로")
    parser.add_argument("--dry-run", action="store_true", help="발행하지 않고 미리보기만 출력")
    parser.add_argument("--publish", action="store_true", help="티스토리에 실제 발행")
    parser.add_argument("--reference-date", type=str, default="", help="기준일(YYYY-MM-DD)")
    parser.add_argument("--blog-name", type=str, default=TISTORY_BLOG_NAME, help="티스토리 blogName")
    parser.add_argument("--category-id", type=str, default=TISTORY_CATEGORY_ID, help="티스토리 category id")
    parser.add_argument("--tags", type=str, default=TISTORY_TAGS, help="쉼표로 구분된 태그")
    parser.add_argument("--access-token", type=str, default=TISTORY_ACCESS_TOKEN, help="티스토리 access token")
    args = parser.parse_args(argv)

    reference_date = None
    if args.reference_date:
        reference_date = datetime.strptime(args.reference_date, "%Y-%m-%d").date()

    payload = build_weekly_post(csv_path=args.csv, reference_date=reference_date)
    title = str(payload["title"])
    content = str(payload["content"])
    summary = payload["summary"]

    logger.info("주간 리포트 생성 완료: %s", title)
    logger.info("총 데이터 %s건, 검증 통과 %s건, 점수 %s/100", summary.total_rows, summary.valid_rows, summary.score)

    if args.dry_run or not args.publish:
        print(title)
        print(content)
        return 0

    if not args.access_token or not args.blog_name:
        raise SystemExit("TISTORY_ACCESS_TOKEN과 TISTORY_BLOG_NAME이 필요합니다.")

    result = publish_to_tistory(
        title=title,
        content=content,
        access_token=args.access_token,
        blog_name=args.blog_name,
        category_id=args.category_id,
        tags=args.tags,
        visibility=TISTORY_VISIBILITY,
        accept_comment=TISTORY_ACCEPT_COMMENT,
        published=int(datetime.now().timestamp()),
    )

    post_info = result.get("tistory", {})
    logger.info("티스토리 발행 완료: postId=%s url=%s", post_info.get("postId"), post_info.get("url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
