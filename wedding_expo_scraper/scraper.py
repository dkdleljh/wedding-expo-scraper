#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 스크래핑 모듈 - 웨딩 박람회 정보 수집
"""

import re
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .config import SCRAPING_SOURCES, REQUEST_TIMEOUT, REQUEST_RETRY_COUNT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


logger = logging.getLogger(__name__)


class WeddingExpoScraper:
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.results: List[Dict] = []
        
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
                logger.info(f"✅ {url} - 성공 (시도 {attempt + 1})")
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ {url} - 실패 (시도 {attempt + 1}/{REQUEST_RETRY_COUNT}): {e}")
                if attempt < REQUEST_RETRY_COUNT - 1:
                    time.sleep((attempt + 1) * 5)
        logger.error(f"❌ {url} - 모든 시도 실패")
        return None
    
    def _extract_gwangju_expos(self, soup: BeautifulSoup, url: str, source: str) -> List[Dict]:
        results = []
        
        # h3 태그에서 광주 웨딩 박람회 찾기
        for h3 in soup.find_all('h3'):
            title = h3.get_text(strip=True)
            if '광주' in title and any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어', '엑스포']):
                results.append({
                    "name": title,
                    "raw_date": "",
                    "location": self._extract_location_from_parent(h3),
                    "source_url": url,
                    "source": source
                })
        
        # strong 태그에서도 찾기
        for strong in soup.find_all('strong'):
            title = strong.get_text(strip=True)
            if '광주' in title and any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어']):
                if not any(r['name'] == title for r in results):
                    results.append({
                        "name": title,
                        "raw_date": "",
                        "location": self._extract_location_from_parent(strong),
                        "source_url": url,
                        "source": source
                    })
        
        # meta keywords에서 광주 데이터 추출
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
                                "raw_date": "",
                                "location": "광주광역시",
                                "source_url": url,
                                "source": source
                            })
        
        return results
    
    def _extract_location_from_parent(self, elem) -> str:
        location = ""
        
        # 부모 요소에서 장소 찾기
        parent = elem.find_parent(['div', 'section', 'article', 'td'])
        if parent:
            location_text = parent.get_text()
            
            # 광주 지역 장소 패턴
            gwangju_locations = ['김대중컨벤션센터', '컨벤션센터', '신세계백화점', '금남로', 'LG전자', '동광주', 
                               '광주광역시', '광산구', '남구', '동구', '북구', '광산', '남', '동', '북']
            for loc in gwangju_locations:
                if loc in location_text:
                    location = loc
                    break
        
        if not location:
            location = "광주광역시"
            
        return location
    
    def _parse_wedding_fairs_schedule(self, html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        return self._extract_gwangju_expos(soup, url, "weddingfairschedule.kr")
    
    def _parse_weddingo(self, html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        return self._extract_gwangju_expos(soup, url, "weddingo.kr")
    
    def _parse_gjweddingshow(self, html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        return self._extract_gwangju_expos(soup, url, "gjweddingshow.kr")
    
    def scrape_all(self) -> List[Dict]:
        all_results = []
        
        for source in SCRAPING_SOURCES:
            url = source["url"]
            name = source["name"]
            
            logger.info(f"\n{'='*50}")
            logger.info(f"📡 스크래핑 중: {name}")
            logger.info(f"🔗 URL: {url}")
            logger.info(f"{'='*50}")
            
            html = self._fetch_page(url)
            
            if not html:
                logger.warning(f"⚠️ {name}에서 데이터 가져오기 실패")
                continue
            
            if 'weddingfairschedule' in url:
                results = self._parse_wedding_fairs_schedule(html, url)
            elif 'weddingo' in url:
                results = self._parse_weddingo(html, url)
            elif 'gjweddingshow' in url:
                results = self._parse_gjweddingshow(html, url)
            else:
                soup = BeautifulSoup(html, 'lxml')
                results = self._extract_gwangju_expos(soup, url, name)
            
            logger.info(f"📊 {name}: {len(results)}건 수집")
            all_results.extend(results)
        
        # 중복 제거
        seen = set()
        unique_results = []
        for item in all_results:
            name_key = item['name'].strip().lower()[:50]
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(item)
        
        logger.info(f"\n✅ 총 {len(unique_results)}건의 고유 데이터 수집 완료")
        
        return unique_results


if __name__ == "__main__":
    scraper = WeddingExpoScraper()
    results = scraper.scrape_all()
    print(f"\n수집 결과: {len(results)}건")
    for r in results:
        print(f"  - {r.get('name', 'N/A')}")
