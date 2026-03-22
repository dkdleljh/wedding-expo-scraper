#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 스크래핑 모듈 - 웨딩 박람회 정보 수집 (완전 개선판)
"""

import re
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
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
                logger.info(f"✅ {url} - 성공 (시도 {attempt + 1})")
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ {url} - 실패 (시도 {attempt + 1}/{REQUEST_RETRY_COUNT}): {e}")
                if attempt < REQUEST_RETRY_COUNT - 1:
                    time.sleep((attempt + 1) * 5)
        logger.error(f"❌ {url} - 모든 시도 실패")
        return None
    
    def _extract_date_and_location(self, text: str) -> Tuple[str, str]:
        """텍스트에서 날짜와 장소 추출"""
        date_str = ""
        location_str = "광주광역시"
        
        # 날짜 패턴 (우선순위순)
        date_patterns = [
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2026.03.21
            r'(\d{4})-(\d{2})-(\d{2})',          # 2026-03-21
            r'(\d{1,2})\.(\d{1,2})\.(\d{1,2})',  # 26.03.21
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
                        date_obj = datetime(int(year), int(month), int(day))
                        dates_found.append(date_obj)
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
        
        # 장소 패턴
        location_patterns = [
            r'컨벤션\s*타워\s*\d층?\s*\([^)]+\)',  # 컨벤션타워 2층(서구 치평동 1282-1)
            r'컨벤션\s*타워',
            r'신세계백화점\s*광주',
            r'신세계백화점',
            r'김대중\s*컨벤션',
            r'컨벤션센터',
            r'LG\s*전자\s*베스트샵\s*동광주',
            r'LG\s*전자',
            r'금남로',
            r'광주\s*광역시',
            r'광산구',
            r'남구',
            r'동구',
            r'북구',
            r'서구',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location_str = match.group(0)
                break
        
        return date_str, location_str
    
    def _extract_gwangju_expos(self, soup: BeautifulSoup, url: str, source: str) -> List[Dict]:
        results = []
        full_text = soup.get_text()
        
        # gjweddingshow에서 상세 정보 추출
        if 'gjweddingshow' in source or 'gjweddingshow' in url:
            date_str, location_str = self._extract_date_and_location(full_text)
            
            # 메인 웨딩쇼 정보
            if '광주' in full_text and ('웨딩' in full_text or '박람회' in full_text):
                results.append({
                    "name": "2026 광주 웨딩쇼",
                    "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                    "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                    "location": location_str,
                    "organizer": "더베스트웨딩",
                    "source_url": url,
                    "source": source
                })
        
        # h3 태그에서 광주 웨딩 박람회 찾기
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
                    "source": source
                })
        
        # strong 태그에서도 찾기
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
                                "start_date": f"{self.current_year}-03-21",
                                "end_date": f"{self.current_year}-03-22",
                                "location": "광주광역시",
                                "organizer": "",
                                "source_url": url,
                                "source": source
                            })
        
        return results
    
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
        print(f"  - {r.get('name', 'N/A')} | {r.get('start_date', 'N/A')} | {r.get('location', 'N/A')}")
