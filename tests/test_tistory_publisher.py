# -*- coding: utf-8 -*-

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from wedding_expo_scraper.tistory_publisher import build_title, publish_to_tistory, render_html, summarize_dataframe


def test_summarize_dataframe_builds_counts():
    df = pd.DataFrame(
        [
            {
                "name": "행사 A",
                "start_date": "2026-03-23",
                "end_date": "2026-03-23",
                "operating_hours": "10:00~18:00",
                "location": "광주 서구",
                "organizer": "주관사 A",
                "contact": "010-0000-0000",
                "source_url": "https://example.com/a",
                "description": "설명 A",
            },
            {
                "name": "행사 B",
                "start_date": "2026-03-30",
                "end_date": "2026-03-31",
                "operating_hours": "10:00~18:00",
                "location": "광주 북구",
                "organizer": "주관사 B",
                "contact": "010-1111-1111",
                "source_url": "https://example.com/b",
                "description": "설명 B",
            },
        ]
    )

    summary = summarize_dataframe(df, reference_date=date(2026, 3, 23))

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.score == 100
    assert summary.week_start == date(2026, 3, 23)
    assert summary.week_end == date(2026, 3, 29)
    assert summary.required_field_counts["name"] == 2
    assert summary.month_counts[0]["month"] == "2026-03"
    assert summary.upcoming_events[0]["name"] == "행사 A"


def test_render_html_contains_summary_and_links():
    df = pd.DataFrame(
        [
            {
                "name": "행사 A",
                "start_date": "2026-03-23",
                "end_date": "2026-03-23",
                "operating_hours": "10:00~18:00",
                "location": "광주 서구",
                "organizer": "주관사 A",
                "contact": "010-0000-0000",
                "source_url": "https://example.com/a",
                "description": "설명 A",
            }
        ]
    )
    summary = summarize_dataframe(df, reference_date=date(2026, 3, 23))
    html = render_html(summary, repo_url="https://github.com/example/repo", csv_url="gwangju_wedding_expos.csv")

    assert "광주 웨딩박람회 주간 업데이트" in html
    assert "CSV 원본 보기" in html
    assert "프로젝트 저장소" in html
    assert "행사 A" in html


def test_publish_to_tistory_builds_request(monkeypatch):
    captured = {}

    def fake_post(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"tistory": {"status": "200", "postId": "123", "url": "https://example.com/post/123"}},
        )

    monkeypatch.setattr("wedding_expo_scraper.tistory_publisher.requests.post", fake_post)

    result = publish_to_tistory(
        title="제목",
        content="<p>본문</p>",
        access_token="token",
        blog_name="blog",
        category_id="42",
        tags="a,b",
    )

    assert captured["url"] == "https://www.tistory.com/apis/post/write"
    assert captured["params"]["access_token"] == "token"
    assert captured["params"]["blogName"] == "blog"
    assert captured["params"]["category"] == "42"
    assert result["tistory"]["postId"] == "123"


def test_build_title_uses_week_range():
    from wedding_expo_scraper.tistory_publisher import WeeklySummary

    summary = WeeklySummary(
        reference_date=date(2026, 3, 23),
        week_start=date(2026, 3, 23),
        week_end=date(2026, 3, 29),
        total_rows=1,
        valid_rows=1,
        score=100,
        date_range="2026-03-23",
        required_field_counts={},
        month_counts=[],
        top_organizers=[],
        top_locations=[],
        upcoming_events=[],
    )

    assert build_title(summary) == "[주간 업데이트] 광주 웨딩박람회 점검 2026-03-23 ~ 2026-03-29"
