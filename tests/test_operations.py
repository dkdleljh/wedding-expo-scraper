# -*- coding: utf-8 -*-

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import main as main_module

from main import main as run_main
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
    monkeypatch.setattr(main_module, "SourceHealthManager", lambda: SourceHealthManager(health_path=tmp_path / "health.json"))

    exit_code = run_main(["--dry-run"])
    assert exit_code == 0
    assert save_called["value"] is False
