# -*- coding: utf-8 -*-

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wedding_expo_scraper.parser import ExpoParser
from wedding_expo_scraper.config import get_all_sources, get_gwangju_sources, get_priority_sources


class TestExpoParser:
    @pytest.fixture
    def parser(self):
        return ExpoParser()

    def test_parse_full_date(self, parser):
        result = parser._parse_single_date("2026-03-28")
        assert result == "2026-03-28"

    def test_parse_date_with_dots(self, parser):
        result = parser._parse_single_date("2026.03.28")
        assert result == "2026-03-28"

    def test_parse_date_with_korean_format(self, parser):
        result = parser._parse_single_date("2026년 3월 28일")
        assert result == "2026-03-28"

    def test_parse_short_year_format(self, parser):
        result = parser._parse_single_date("26.03.28")
        assert result == "2026-03-28"

    def test_parse_short_year_95(self, parser):
        result = parser._parse_single_date("95.03.28")
        assert result == "1995-03-28"

    def test_parse_month_day_format(self, parser):
        result = parser._parse_single_date("3월 28일")
        assert result == "2026-03-28"

    def test_parse_invalid_date(self, parser):
        result = parser._parse_single_date("invalid")
        assert result is None

    def test_normalize_location_full_address(self, parser):
        result = parser._normalize_location("김대중컨벤션센터 (광주 서구 상무누리로 30)")
        assert "김대중컨벤션센터" in result
        assert "광주 서구 상무누리로 30" in result

    def test_normalize_location_short(self, parser):
        result = parser._normalize_location("염주")
        assert "염주종합체육관" in result
        assert "광주 서구 금화로 278" in result

    def test_normalize_location_unknown(self, parser):
        result = parser._normalize_location("모르는 장소")
        assert result == "모르는 장소"

    def test_normalize_name(self, parser):
        result = parser._normalize_name("  광주  웨딩박람회  ")
        assert result == "광주 웨딩박람회"

    def test_normalize_name_with_empty_parens(self, parser):
        result = parser._normalize_name("광주웨딩박람회 ()")
        assert result == "광주웨딩박람회"

    def test_parse_all(self, parser):
        raw_data = [
            {"name": "광주웨딩박람회", "raw_date": "2026.03.28", "location": "염주"},
            {"name": "전남웨딩박람회", "start_date": "2026-03-29", "end_date": "2026-03-30", "location": "김대중"},
        ]
        result = parser.parse_all(raw_data)
        assert len(result) == 2
        assert result[0]["start_date"] == "2026-03-28"
        assert result[0]["end_date"] == "2026-03-28"

    def test_parse_all_removes_duplicates(self, parser):
        raw_data = [
            {"name": "광주웨딩박람회", "raw_date": "2026.03.28", "location": "염주"},
            {"name": "광주웨딩박람회", "raw_date": "2026.03.28", "location": "염주"},
        ]
        result = parser.parse_all(raw_data)
        assert len(result) == 1

    def test_parse_all_sorting(self, parser):
        raw_data = [
            {"name": "뒷날 행사", "start_date": "2026-03-30", "end_date": "2026-03-30", "location": "광주"},
            {"name": "첫날 행사", "start_date": "2026-03-28", "end_date": "2026-03-28", "location": "광주"},
        ]
        result = parser.parse_all(raw_data)
        assert result[0]["name"] == "첫날 행사"
        assert result[1]["name"] == "뒷날 행사"

    def test_get_organizer_info_best(self, parser):
        info = parser._get_organizer_info("더베스트웨딩")
        assert info['contact'] == '062-714-1020'
        assert info['operating_hours'] == '10:00~18:00'
        assert '최대' in info['description']

    def test_get_organizer_info_reve(self, parser):
        info = parser._get_organizer_info("레브웨딩")
        assert info['contact'] == '02-6959-2764'
        assert info['operating_hours'] == '11:00~19:00'
        assert '플래너' in info['description']

    def test_get_organizer_info_unknown(self, parser):
        info = parser._get_organizer_info("알 수 없는主办")
        assert info['contact'] == ''
        assert info['operating_hours'] == '10:00~18:00'
        assert info['description'] == ''

    def test_parse_all_with_new_fields(self, parser):
        raw_data = [
            {"name": "테스트 박람회", "start_date": "2026-03-28", "end_date": "2026-03-29", 
             "location": "광주", "organizer": "더베스트웨딩", "source_url": "https://test.com"},
        ]
        result = parser.parse_all(raw_data)
        assert len(result) == 1
        assert 'operating_hours' in result[0]
        assert 'contact' in result[0]
        assert 'description' in result[0]
        assert result[0]['operating_hours'] == '10:00~18:00'
        assert result[0]['contact'] == '062-714-1020'


class TestConfig:
    def test_get_all_sources_count(self):
        sources = get_all_sources()
        assert len(sources) >= 30

    def test_get_gwangju_sources(self):
        sources = get_gwangju_sources()
        assert len(sources) > 0
        for s in sources:
            assert s.get("region") in ["광주", "전국"]

    def test_get_priority_sources(self):
        sources = get_priority_sources()
        assert len(sources) > 0
        priorities = [s.get("priority", 99) for s in sources]
        assert priorities == sorted(priorities)

    def test_no_duplicate_urls(self):
        sources = get_all_sources()
        url_name_pairs = [(s["url"], s["name"]) for s in sources]
        unique_pairs = set(url_name_pairs)
        assert len(url_name_pairs) == len(unique_pairs), f"중복: {len(url_name_pairs) - len(unique_pairs)}개"

    def test_https_urls_only(self):
        sources = get_all_sources()
        http_sources = [s for s in sources if s["url"].startswith("http://")]
        assert len(http_sources) == 0, f"http:// sources found: {[s['url'] for s in http_sources]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
