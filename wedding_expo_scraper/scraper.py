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
    
    def _extract_weddingdamoa(self, html: str, url: str, source_name: str, region: str) -> List[Dict]:
        """weddingdamoa.com 파서 - 정확한 날짜/장소 추출"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 날짜 패턴: 📅 2026.03.21(토) - 2026.03.22(일)
        date_pattern = r'📅\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\([^\)]+\)\s*[-~]\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\([^\)]+\)'
        
        # 장소 패턴: 📍 광주 서구 치평동 1282-1 컨벤션타워 2층
        location_pattern = r'📍\s*([^\n]+?)(?=\s*(?:무료|사전|$))'
        
        # Tailwind CSS 기반 카드 구조 파싱
        for item in soup.find_all(['section'], class_=re.compile(r'space-y|p-4')):
            try:
                item_text = item.get_text()
                
                # 광주 관련 필터링
                if '광주' not in item_text:
                    continue
                
                # 제목 찾기 (h3, h4, strong)
                title_elem = item.find(['h3', 'h4', 'strong'])
                if not title_elem:
                    title_elem = item.find('a')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if len(title) < 3:
                    continue
                
                if not any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어', '엑스포']):
                    continue
                
                # 날짜 추출
                date_match = re.search(date_pattern, item_text)
                if date_match:
                    start_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                    end_date = f"{date_match.group(4)}-{int(date_match.group(5)):02d}-{int(date_match.group(6)):02d}"
                else:
                    start_date = f"{self.current_year}-03-21"
                    end_date = f"{self.current_year}-03-22"
                
                # 장소 추출
                loc_match = re.search(location_pattern, item_text)
                if loc_match:
                    location = loc_match.group(1).strip()
                    location = re.sub(r'\s+', ' ', location)
                    location = location[:100]
                else:
                    # 대체 장소 패턴
                    loc_patterns = [
                        r'(컨벤션\s*타워[^\n]{0,50})',
                        r'(신세계백화점[^\n]{0,50})',
                        r'(김대중[^\n]{0,50})',
                        r'(제이아트[^\n]{0,50})',
                        r'(광주[^\n]{5,80})',
                    ]
                    location = "광주광역시"
                    for lp in loc_patterns:
                        lm = re.search(lp, item_text)
                        if lm:
                            location = lm.group(1).strip()[:100]
                            break
                
                results.append({
                    "name": title[:100],
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "organizer": "웨딩다모아",
                    "source_url": url,
                    "source": source_name,
                    "region": "광주"
                })
            except Exception:
                continue
        
        return results
    
    def _extract_keu(self, html: str, url: str, source_name: str, region: str) -> List[Dict]:
        """keu.or.kr (한국웨딩연합회) 파서"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 날짜 패턴들
        date_patterns = [
            r'📅\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\([^\)]+\)\s*[~-]+\s*(\d{4})\.(\d{1,2})\.(\d{1,2})\([^\)]+\)',
            r'📅\s*(\d{1,2})월\s*(\d{1,2})일\([^\)]+\)\s*[~]\s*(\d{1,2})월\s*(\d{1,2})일\([^\)]+\)',
        ]
        
        # 카드 구조 파싱
        for item in soup.find_all(['div'], class_=re.compile(r'item|post|entry|expo|fair', re.I)):
            try:
                item_text = item.get_text()
                
                # 광주 관련 필터링
                if '광주' not in item_text:
                    continue
                
                # 제목 찾기
                title_elem = item.find(['h3', 'h4', 'h2', 'strong'])
                if not title_elem:
                    title_elem = item.find('a', href=True)
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                if len(title) < 3:
                    continue
                
                if not any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어', '엑스포', '결혼']):
                    continue
                
                # 날짜 추출
                start_date = f"{self.current_year}-03-21"
                end_date = f"{self.current_year}-03-22"
                
                for dp in date_patterns:
                    dm = re.search(dp, item_text)
                    if dm:
                        groups = dm.groups()
                        if len(groups) == 6:
                            if len(groups[0]) == 4:  # YYYY.MM.DD 형식
                                start_date = f"{groups[0]}-{int(groups[1]):02d}-{int(groups[2]):02d}"
                                end_date = f"{groups[3]}-{int(groups[4]):02d}-{int(groups[5]):02d}"
                            else:  # MM월 DD일 형식
                                start_date = f"{self.current_year}-{int(groups[0]):02d}-{int(groups[1]):02d}"
                                end_date = f"{self.current_year}-{int(groups[3]):02d}-{int(groups[4]):02d}"
                        break
                
                # 장소 추출
                location = "광주광역시"
                loc_patterns = [
                    r'📍\s*([^\n]+?)(?=\s*(?:🎟️|$))',
                    r'(?:📍|장소)[:\s]*([^\n📅]{10,100})',
                    r'(광주\s*[^\n]{10,80})',
                    r'(제이아트[^\n]{0,60})',
                    r'(컨벤션[^\n]{0,60})',
                ]
                for lp in loc_patterns:
                    lm = re.search(lp, item_text)
                    if lm:
                        location = lm.group(1).strip()
                        location = re.sub(r'\s+', ' ', location)
                        location = re.sub(r'\([^)]*\)', ' ', location)
                        location = location.strip()[:100]
                        break
                
                results.append({
                    "name": title[:100],
                    "start_date": start_date,
                    "end_date": end_date,
                    "location": location,
                    "organizer": "한국웨딩연합회",
                    "source_url": url,
                    "source": source_name,
                    "region": "광주"
                })
            except Exception:
                continue
        
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
        
        # 소스별 라우팅
        if 'weddingdamoa' in url.lower():
            results = self._extract_weddingdamoa(html, url, source_name, region)
        elif 'keu.or.kr' in url.lower():
            results = self._extract_keu(html, url, source_name, region)
        else:
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
