# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import main as main_module

from main import main as run_main
from wedding_expo_scraper.config import CRITICAL_SOURCE_NAMES
from wedding_expo_scraper.source_health import SourceHealthManager


def test_source_health_circuit_breaker(tmp_path):
    manager = SourceHealthManager(health_path=tmp_path / "health.json", failure_threshold=2, cooldown_hours=24)
    source = {"name": "테스트소스", "url": "https://example.com"}

    now = datetime(2026, 3, 28, 10, 0, 0)
    manager.update_from_run_stats({"테스트소스": {"success": False, "result_count": 0, "error": "boom"}}, now=now)
    assert manager.should_skip(source, now=now) is False

    manager.update_from_run_stats({"테스트소스": {"success": False, "result_count": 0, "error": "boom"}}, now=now)
    assert manager.should_skip(source, now=now) is True
    assert manager.should_skip(source, now=now + timedelta(hours=25)) is False


def test_source_health_recovery_resets_failures(tmp_path):
    manager = SourceHealthManager(health_path=tmp_path / "health.json", failure_threshold=2, cooldown_hours=24)
    source = {"name": "테스트소스", "url": "https://example.com"}
    now = datetime(2026, 3, 28, 10, 0, 0)

    manager.update_from_run_stats({"테스트소스": {"success": False, "result_count": 0, "error": "boom"}}, now=now)
    manager.update_from_run_stats({"테스트소스": {"success": True, "result_count": 3, "error": ""}}, now=now)

    assert manager.should_skip(source, now=now) is False
    assert manager.state["테스트소스"]["consecutive_failures"] == 0


def test_source_health_zero_result_circuit_breaker(tmp_path):
    manager = SourceHealthManager(
        health_path=tmp_path / "health.json",
        failure_threshold=2,
        cooldown_hours=24,
        zero_result_threshold=2,
    )
    source = {"name": "테스트소스", "url": "https://example.com"}
    now = datetime(2026, 3, 28, 10, 0, 0)

    manager.update_from_run_stats({"테스트소스": {"success": True, "result_count": 0, "error": ""}}, now=now)
    assert manager.should_skip(source, now=now) is False

    manager.update_from_run_stats({"테스트소스": {"success": True, "result_count": 0, "error": ""}}, now=now)
    assert manager.should_skip(source, now=now) is True
    assert manager.skip_reason(source, now=now) == "repeated_zero_results"

    manager.update_from_run_stats({"테스트소스": {"success": True, "result_count": 2, "error": ""}}, now=now)
    assert manager.should_skip(source, now=now) is False


def test_main_dry_run_skips_side_effects(monkeypatch, tmp_path):
    class FakeScraper:
        def __init__(self, sources=None):
            self.sources = sources or []

        def scrape_all(self):
            return [{
                "name": "광주웨딩페스타",
                "start_date": "2026-03-28",
                "end_date": "2026-03-29",
                "location": "LG전자베스트샵 동광주점",
                "organizer": "",
                "source_url": "https://example.com",
                "region": "광주",
                "source": "테스트",
            }]

        def get_last_run_stats(self):
            return {"테스트": {"success": True, "result_count": 1, "error": "", "url": "https://example.com", "kind": "static"}}

    class FakeDynamicScraper(FakeScraper):
        def scrape_all(self):
            return []

        def get_last_run_stats(self):
            return {}

    save_called = {"value": False}

    class FakeStorage:
        def save(self, data):
            save_called["value"] = True
            return True

        def get_all(self):
            return []

    monkeypatch.setattr(main_module, "WeddingExpoScraper", FakeScraper)
    monkeypatch.setattr(main_module, "DynamicScraper", FakeDynamicScraper)
    monkeypatch.setattr(main_module, "DataStorage", FakeStorage)
    monkeypatch.setattr(main_module, "get_priority_sources", lambda: [{"name": "테스트", "url": "https://example.com"}])
    monkeypatch.setattr(main_module, "get_production_dynamic_sources", lambda: [])
    class FakeCoverageAuditor:
        def audit(self, actual_records):
            return {
                "coverage_reference_count": 1,
                "coverage_matched_count": 1,
                "coverage_missing_count": 0,
                "coverage_missing_expos": [],
                "coverage_reference_sources": ["테스트-레퍼런스"],
            }

    monkeypatch.setattr(
        main_module,
        "SourceHealthManager",
        lambda: SourceHealthManager(
            health_path=tmp_path / "health.json",
            report_path=tmp_path / "report.json",
        ),
    )
    monkeypatch.setattr(main_module, "CoverageAuditor", FakeCoverageAuditor)

    exit_code = run_main(["--dry-run"])
    assert exit_code == 0
    assert save_called["value"] is False
    report = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert '"final_valid_count": 1' in report


def test_source_health_report_tracks_critical_zero_results(tmp_path):
    manager = SourceHealthManager(
        health_path=tmp_path / "health.json",
        report_path=tmp_path / "report.json",
    )
    run_stats = {
        "더베스트웨딩": {"success": True, "result_count": 0, "error": ""},
        "광주웨딩페스타": {"success": True, "result_count": 0, "error": ""},
        "광주웨딩페스타-Dynamic": {"success": True, "result_count": 0, "error": ""},
        "웨딩모멘트-전라도": {"success": True, "result_count": 5, "error": ""},
    }

    report = manager.build_report(
        run_stats,
        skipped_sources=[],
        summary={"raw_count": 5, "parsed_count": 3, "final_valid_count": 2},
    )

    assert report["final_valid_count"] == 2
    assert set(report["critical_zero_result_sources"]) == CRITICAL_SOURCE_NAMES


def test_storage_save_replaces_snapshot(tmp_path):
    from wedding_expo_scraper.storage import DataStorage

    storage = DataStorage(db_path=tmp_path / "test.db", csv_path=tmp_path / "test.csv")
    first = [
        {
            "name": "행사 A",
            "start_date": "2026-03-28",
            "end_date": "2026-03-29",
            "operating_hours": "10:00~18:00",
            "location": "염주종합체육관 (광주 서구 금화로 278)",
            "organizer": "",
            "contact": "",
            "source_url": "https://a.example.com",
            "description": "",
            "region": "광주",
            "source": "테스트",
        },
        {
            "name": "행사 B",
            "start_date": "2026-04-04",
            "end_date": "2026-04-05",
            "operating_hours": "10:00~18:00",
            "location": "메리포엠웨딩홀(광주 광산구 무진대로 282)",
            "organizer": "",
            "contact": "",
            "source_url": "https://b.example.com",
            "description": "",
            "region": "광주",
            "source": "테스트",
        },
    ]
    second = [first[1]]

    assert storage.save(first) is True
    assert len(storage.get_all()) == 2
    assert storage.save(second) is True
    rows = storage.get_all()
    assert len(rows) == 1
    assert rows[0]["name"] == "행사 B"
