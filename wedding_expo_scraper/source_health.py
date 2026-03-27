#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소스 헬스 상태 관리"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .config import (
    SOURCE_COOLDOWN_HOURS,
    SOURCE_FAILURE_THRESHOLD,
    SOURCE_HEALTH_PATH,
    SOURCE_HEALTH_REPORT_PATH,
    SOURCE_ZERO_RESULT_THRESHOLD,
)

logger = logging.getLogger(__name__)


@dataclass
class SourceRunDecision:
    enabled_sources: List[Dict]
    skipped_sources: List[Dict]


class SourceHealthManager:
    def __init__(
        self,
        health_path: Path = SOURCE_HEALTH_PATH,
        failure_threshold: int = SOURCE_FAILURE_THRESHOLD,
        cooldown_hours: int = SOURCE_COOLDOWN_HOURS,
        zero_result_threshold: int = SOURCE_ZERO_RESULT_THRESHOLD,
    ):
        self.health_path = health_path
        self.failure_threshold = failure_threshold
        self.cooldown_hours = cooldown_hours
        self.zero_result_threshold = zero_result_threshold
        self.state = self._load()

    def _load(self) -> Dict[str, Dict]:
        if not self.health_path.exists():
            return {}
        try:
            return json.loads(self.health_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("소스 헬스 상태 로드 실패: %s", exc)
            return {}

    def save(self) -> None:
        self.health_path.parent.mkdir(parents=True, exist_ok=True)
        self.health_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _health_key(self, source: Dict) -> str:
        return source.get("name", source.get("url", "unknown"))

    def should_skip(self, source: Dict, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        health = self.state.get(self._health_key(source), {})
        consecutive_failures = int(health.get("consecutive_failures", 0))
        consecutive_zero_results = int(health.get("consecutive_zero_results", 0))
        last_failed_at = health.get("last_failed_at", "")
        if consecutive_failures >= self.failure_threshold and last_failed_at:
            try:
                failed_at = datetime.fromisoformat(last_failed_at)
            except ValueError:
                failed_at = None
            if failed_at and now - failed_at < timedelta(hours=self.cooldown_hours):
                return True

        last_zero_result_at = health.get("last_zero_result_at", "")
        if consecutive_zero_results >= self.zero_result_threshold and last_zero_result_at:
            try:
                zero_at = datetime.fromisoformat(last_zero_result_at)
            except ValueError:
                zero_at = None
            if zero_at and now - zero_at < timedelta(hours=self.cooldown_hours):
                return True

        return False

    def skip_reason(self, source: Dict, now: datetime | None = None) -> str:
        now = now or datetime.now()
        health = self.state.get(self._health_key(source), {})
        consecutive_failures = int(health.get("consecutive_failures", 0))
        consecutive_zero_results = int(health.get("consecutive_zero_results", 0))
        if consecutive_failures >= self.failure_threshold and self.should_skip(source, now=now):
            return "repeated_failures"
        if consecutive_zero_results >= self.zero_result_threshold and self.should_skip(source, now=now):
            return "repeated_zero_results"
        return ""

    def filter_sources(self, sources: List[Dict], now: datetime | None = None) -> SourceRunDecision:
        enabled = []
        skipped = []
        for source in sources:
            if self.should_skip(source, now=now):
                source_copy = dict(source)
                source_copy["skip_reason"] = self.skip_reason(source, now=now)
                skipped.append(source_copy)
            else:
                enabled.append(source)
        return SourceRunDecision(enabled_sources=enabled, skipped_sources=skipped)

    def update_from_run_stats(self, run_stats: Dict[str, Dict], now: datetime | None = None) -> None:
        now = now or datetime.now()
        timestamp = now.isoformat()
        for source_name, stats in run_stats.items():
            health = self.state.setdefault(source_name, {})
            success = bool(stats.get("success"))
            result_count = int(stats.get("result_count", 0))
            health["last_checked_at"] = timestamp
            health["last_result_count"] = result_count
            health["last_error"] = stats.get("error", "")
            if success:
                health["status"] = "healthy"
                health["consecutive_failures"] = 0
                health["last_success_at"] = timestamp
                if result_count > 0:
                    health["consecutive_zero_results"] = 0
                else:
                    health["consecutive_zero_results"] = int(health.get("consecutive_zero_results", 0)) + 1
                    health["last_zero_result_at"] = timestamp
            else:
                health["status"] = "failing"
                health["consecutive_failures"] = int(health.get("consecutive_failures", 0)) + 1
                health["last_failed_at"] = timestamp

    def build_report(self, run_stats: Dict[str, Dict], skipped_sources: List[Dict]) -> Dict[str, object]:
        return {
            "checked_sources": len(run_stats),
            "healthy_sources": sum(1 for stats in run_stats.values() if stats.get("success")),
            "failed_sources": sum(1 for stats in run_stats.values() if not stats.get("success")),
            "skipped_sources": [
                {"name": source.get("name", ""), "reason": source.get("skip_reason", "")}
                for source in skipped_sources
            ],
            "sources": run_stats,
            "state": self.state,
        }

    def save_report(self, report: Dict[str, object], report_path: Path = SOURCE_HEALTH_REPORT_PATH) -> None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
