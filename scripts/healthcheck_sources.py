#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""프로덕션 소스 헬스체크"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from wedding_expo_scraper.config import (
    PRODUCTION_SOURCE_MODE,
    get_dynamic_sources,
    get_priority_sources,
    get_production_dynamic_sources,
)
from wedding_expo_scraper.dynamic_scraper import DynamicScraper, PLAYWRIGHT_AVAILABLE
from wedding_expo_scraper.parser import ExpoParser
from wedding_expo_scraper.scraper import WeddingExpoScraper


def main() -> int:
    static_sources = get_priority_sources()
    dynamic_sources = get_production_dynamic_sources() if PRODUCTION_SOURCE_MODE else get_dynamic_sources()

    scraper = WeddingExpoScraper(sources=static_sources)
    raw_static = scraper.scrape_all()

    raw_dynamic = []
    if PLAYWRIGHT_AVAILABLE and dynamic_sources:
        dynamic_scraper = DynamicScraper(sources=dynamic_sources)
        raw_dynamic = dynamic_scraper.scrape_all()

    parser = ExpoParser()
    parsed = parser.parse_all(raw_static + raw_dynamic)
    filtered = parser.filter_valid_records(parsed)

    source_counts = Counter(item.get("source", "") for item in filtered)
    summary = {
        "production_source_mode": PRODUCTION_SOURCE_MODE,
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "static_source_count": len(static_sources),
        "dynamic_source_count": len(dynamic_sources),
        "raw_static_count": len(raw_static),
        "raw_dynamic_count": len(raw_dynamic),
        "parsed_count": len(parsed),
        "filtered_count": len(filtered),
        "top_sources": dict(source_counts.most_common(10)),
        "sample": filtered[:10],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
