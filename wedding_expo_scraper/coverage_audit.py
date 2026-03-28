#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""광주 웨딩박람회 커버리지 감사"""

from __future__ import annotations

import logging
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from .parser import ExpoParser

logger = logging.getLogger(__name__)


class CoverageAuditor:
    REFERENCE_SOURCES = [
        {
            "name": "웨딩고-광주-레퍼런스",
            "url": "https://weddingo.kr/%EA%B4%91%EC%A3%BC",
            "region": "광주",
        }
    ]

    def __init__(self):
        self.parser = ExpoParser()
        self.session = requests.Session()

    def _fetch(self, url: str) -> str:
        response = self.session.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            },
            timeout=20,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def _extract_weddingo_reference(self, html: str, source_name: str) -> List[Dict]:
        results = []
        seen = set()
        soup = BeautifulSoup(html, "lxml")
        for article in soup.select("article.item"):
            name_el = article.select_one(".item-name")
            if not name_el:
                continue
            title = name_el.get_text(strip=True)
            if "광주" not in title:
                continue
            if not any(keyword in title for keyword in ["웨딩", "박람회", "페스타", "페어", "엑스포"]):
                continue

            date_value = ""
            location = "광주광역시"
            for row in article.select(".item-meta-row"):
                row_text = row.get_text(" ", strip=True)
                spans = row.find_all("span")
                if not spans:
                    continue
                if "날짜" in row_text:
                    date_value = spans[-1].get_text(strip=True)
                elif "장소" in row_text:
                    location_name = row.select_one('[itemprop="name"]')
                    location = location_name.get_text(strip=True) if location_name else spans[-1].get_text(strip=True)

            if not date_value or "날짜 미정" in date_value:
                continue

            parts = [part.strip() for part in date_value.split("~")]
            if len(parts) != 2:
                continue
            if parts[1].count(".") == 1:
                parts[1] = f"{parts[0].split('.')[0]}.{parts[1]}"

            item_key = (title.strip().lower(), parts[0], parts[1], location.strip().lower())
            if item_key in seen:
                continue
            seen.add(item_key)
            results.append(
                {
                    "name": title,
                    "start_date": parts[0],
                    "end_date": parts[1],
                    "location": location,
                    "organizer": source_name,
                    "source_url": self.REFERENCE_SOURCES[0]["url"],
                    "region": "광주",
                    "source": source_name,
                }
            )
        return results

    def collect_reference_records(self) -> List[Dict]:
        raw_records: List[Dict] = []
        for source in self.REFERENCE_SOURCES:
            try:
                html = self._fetch(source["url"])
                raw_records.extend(self._extract_weddingo_reference(html, source["name"]))
            except Exception as exc:
                logger.warning("커버리지 레퍼런스 수집 실패: %s", exc)
        parsed = self.parser.parse_all(raw_records)
        return self.parser.filter_valid_records(parsed)

    def audit(self, actual_records: List[Dict]) -> Dict[str, object]:
        reference_records = self.collect_reference_records()
        actual_keys = {self.parser._canonical_record_key(item) for item in actual_records}
        missing_records = [
            item for item in reference_records if self.parser._canonical_record_key(item) not in actual_keys
        ]
        return {
            "coverage_reference_count": len(reference_records),
            "coverage_matched_count": len(reference_records) - len(missing_records),
            "coverage_missing_count": len(missing_records),
            "coverage_missing_expos": [
                {
                    "name": item.get("name", ""),
                    "start_date": item.get("start_date", ""),
                    "location": item.get("location", ""),
                }
                for item in missing_records
            ],
            "coverage_reference_sources": [source["name"] for source in self.REFERENCE_SOURCES],
        }
