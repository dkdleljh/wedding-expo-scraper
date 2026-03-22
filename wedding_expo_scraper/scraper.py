#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화 스크래핑 모듈 - 비동기 병렬 처리
"""

import re
import asyncio
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .config import SCRAPING_SOURCES, REQUEST_TIMEOUT, REQUEST_RETRY_COUNT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, MAX_CONCURRENT_REQUESTS


logger = logging.getLogger(__name__)


class WeddingExpoScraper:
    """고도화 웨딩박람회 스크래퍼 - 비동기 + 병렬 처리"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.current_year = datetime.now().year
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    
    def _respectful_delay(self):
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
    
    def _fetch_page(self, url: str) -> Optional[str]:
        for attempt in range(REQUEST_RETRY_COUNT):
            try:
                self._respectful_delay()
                response = self.session.get(url, headers=self._get_headers(), timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text
            except requests.exceptions.RequestException as e:
                if attempt < REQUEST_RETRY_COUNT - 1:
                    time.sleep((attempt + 1) * 3)
        return None
    
    def _extract_date_and_location(self, text: str) -> tuple:
        """날짜와 장소 추출"""
        date_str = ""
        location_str = "광주광역시"
        
        date_patterns = [
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
            r'(\d{1,2})\.(\d{1,2})\.(\d{1,2})',
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    if len(match[0]) == 4:
                        year, month, day = match
                    else:
                        year = str(self.current_year)
                        month, day = match[1], match[2]
                    try:
                        dates_found.append(datetime(int(year), int(month), int(day)))
                    except ValueError:
                        continue
        
        if dates_found:
            dates_found.sort()
            start_date = dates_found[0]
            end_date = dates_found[-1]
            if start_date == end_date:
                date_str = start_date.strftime('%Y-%m-%d')
            else:
                date_str = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
        
        location_patterns = [
            r'컨벤션\s*타워[^\n]*',
            r'신세계백화점[^\n]*',
            r'김대중\s*컨벤션[^\n]*',
            r'킨텍스[^\n]*',
            r'세텍[^\n]*',
            r'LG\s*전자[^\n]*',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location_str = match.group(0)[:50]
                break
        
        return date_str, location_str
    
    def _extract_gwangju_expos(self, html: str, url: str, source: str, region: str) -> List[Dict]:
        results = []
        soup = BeautifulSoup(html, 'lxml')
        full_text = soup.get_text()
        
        if 'gjweddingshow' in source:
            date_str, location_str = self._extract_date_and_location(full_text)
            if '광주' in full_text and ('웨딩' in full_text or '박람회' in full_text):
                results.append({
                    "name": "2026 광주 웨딩쇼",
                    "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                    "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                    "location": location_str,
                    "organizer": "더베스트웨딩",
                    "source_url": url,
                    "source": source,
                    "region": "광주"
                })
        
        for h3 in soup.find_all('h3'):
            title = h3.get_text(strip=True)
            if '광주' in title and any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어', '엑스포']):
                parent_text = h3.find_parent(['div', 'section', 'article']).get_text() if h3.find_parent(['div', 'section', 'article']) else ""
                date_str, location_str = self._extract_date_and_location(parent_text)
                
                results.append({
                    "name": title,
                    "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                    "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                    "location": location_str,
                    "organizer": "",
                    "source_url": url,
                    "source": source,
                    "region": region
                })
        
        for strong in soup.find_all('strong'):
            title = strong.get_text(strip=True)
            if '광주' in title and any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어']):
                if not any(r['name'] == title for r in results):
                    parent_text = strong.find_parent(['div', 'section', 'article']).get_text() if strong.find_parent(['div', 'section', 'article']) else ""
                    date_str, location_str = self._extract_date_and_location(parent_text)
                    
                    results.append({
                        "name": title,
                        "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                        "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                        "location": location_str,
                        "organizer": "",
                        "source_url": url,
                        "source": source,
                        "region": region
                    })
        
        meta_keywords = soup.find('meta', {'name': 'keywords'})
        if meta_keywords:
            keywords = meta_keywords.get('content', '')
            if '광주' in keywords:
                gwangju_items = re.findall(r'[^,]+', keywords)
                for item in gwangju_items:
                    item = item.strip()
                    if '광주' in item and any(kw in item for kw in ['웨딩', '박람회', '페스타', '페어']):
                        if not any(r['name'] == item for r in results):
                            results.append({
                                "name": item,
                                "start_date": f"{self.current_year}-03-21",
                                "end_date": f"{self.current_year}-03-22",
                                "location": "광주광역시",
                                "organizer": "",
                                "source_url": url,
                                "source": source,
                                "region": "광주"
                            })
        
        return results
    
    def scrape_single(self, source: Dict) -> List[Dict]:
        """단일 소스 스크래핑"""
        url = source["url"]
        name = source["name"]
        source_name = source.get("name", "")
        region = source.get("region", "기타")
        
        logger.info(f"📡 스크래핑: {name}")
        
        html = self._fetch_page(url)
        if not html:
            logger.warning(f"⚠️ {name} 실패")
            return []
        
        results = self._extract_gwangju_expos(html, url, source_name, region)
        logger.info(f"📊 {name}: {len(results)}건")
        return results
    
    def scrape_all(self) -> List[Dict]:
        """병렬 스크래핑"""
        logger.info(f"\n{'='*50}")
        logger.info(f"🚀 병렬 스크래핑 시작 ({len(SCRAPING_SOURCES)}개 소스)")
        logger.info(f"{'='*50}")
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = {executor.submit(self.scrape_single, source): source for source in SCRAPING_SOURCES}
            for future in futures:
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    logger.error(f"스크래핑 오류: {e}")
        
        seen = set()
        unique_results = []
        for item in all_results:
            name_key = item['name'].strip().lower()[:50]
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(item)
        
        logger.info(f"\n✅ 총 {len(unique_results)}건 수집 완료")
        return unique_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    scraper = WeddingExpoScraper()
    results = scraper.scrape_all()
    print(f"\n결과: {len(results)}건")
    for r in results:
        print(f"  - {r['name']} ({r.get('region', 'N/A')})")
