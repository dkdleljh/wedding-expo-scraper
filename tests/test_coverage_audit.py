# -*- coding: utf-8 -*-

from wedding_expo_scraper.coverage_audit import CoverageAuditor
from wedding_expo_scraper.scraper import WeddingExpoScraper


def test_extract_weddingo_gwangju_cards():
    html = """
    <article class="item">
      <div class="item-name">광주 메리포엠 웨딩페어</div>
      <div class="item-meta-row"><span class="meta-icon">날짜</span><span>2026.4.4 ~ 4.5</span></div>
      <div class="item-meta-row"><span class="meta-icon">장소</span><span itemprop="name">메리포엠웨딩홀(광주 광산구 무진대로 282)</span></div>
    </article>
    <article class="item">
      <div class="item-name">광주 스타일링 웨딩페어</div>
      <div class="item-meta-row"><span class="meta-icon">날짜</span><span>2026.4.4 ~ 4.5</span></div>
      <div class="item-meta-row"><span class="meta-icon">장소</span><span itemprop="name">더베스트웨딩컴퍼니 사옥</span></div>
    </article>
    """
    scraper = WeddingExpoScraper(sources=[])
    results = scraper._extract_weddingo(html, "https://weddingo.kr/%EA%B4%91%EC%A3%BC", "웨딩고-광주", "광주")

    assert len(results) == 2
    assert results[0]["start_date"] == "2026-04-04"
    assert results[0]["end_date"] == "2026-04-05"


def test_coverage_audit_detects_missing_reference():
    auditor = CoverageAuditor()
    auditor.collect_reference_records = lambda: [
        {
            "name": "광주 스타일링 웨딩페어",
            "start_date": "2026-04-04",
            "end_date": "2026-04-05",
            "location": "더베스트웨딩 사옥 (광주 동구 서석로 13-1 3층)",
            "source_url": "https://weddingo.kr/%EA%B4%91%EC%A3%BC",
            "source": "웨딩고-광주-레퍼런스",
            "region": "광주",
            "organizer": "웨딩고",
            "operating_hours": "10:00~18:00",
            "contact": "",
            "description": "",
        }
    ]

    report = auditor.audit([])
    assert report["coverage_reference_count"] == 1
    assert report["coverage_missing_count"] == 1
    assert report["coverage_missing_expos"][0]["name"] == "광주 스타일링 웨딩페어"
