#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 스크래핑 모듈 - 웨딩 박람회 정보 수집
"""

import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .config import SCRAPING_SOURCES, REQUEST_TIMEOUT, REQUEST_RETRY_COUNT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, DEFAULT_USER_AGENT


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
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _respectful_delay(self):
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
    
    def _fetch_page(self, url: str) -> Optional[str]:
        for attempt in range(REQUEST_RETRY_COUNT):
            try:
                self._respectful_delay()
                
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                response.encoding = response.apparent_encoding or 'utf-8'
                
                logger.info(f"✅ {url} - 성공 (시도 {attempt + 1})")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ {url} - 실패 (시도 {attempt + 1}/{REQUEST_RETRY_COUNT}): {e}")
                if attempt < REQUEST_RETRY_COUNT - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"⏳ {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
        
        logger.error(f"❌ {url} - 모든 시도 실패")
        return None
    
    def _parse_wedding_fairs_schedule(self, html: str, url: str) -> List[Dict]:
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        selectors = [
            '.expo-item',
            '.wedding-item',
            '.schedule-item',
            '.event-item',
            '.card',
            'article',
            '.list-item',
            'div[class*="expo"]',
            'div[class*="event"]',
            'li[class*="item"]',
            '.content',
            'main'
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items and len(items) > 1:
                logger.info(f"🔍 선택자 '{selector}'로 {len(items)}개 항목 발견")
                break
        
        for item in items:
            try:
                text = item.get_text()
                
                if '광주' not in text:
                    continue
                
                title_elem = (item.select_one('h1, h2, h3, h4, h5, a, .title, .name, strong') or
                             item.select_one('[class*="title"], [class*="name"]'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 2:
                    continue
                
                date_elem = (item.select_one('.date, .schedule, .period, .time, time') or
                            item.select_one('[class*="date"], [class*="schedule"], [class*="period"]'))
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                location_elem = (item.select_one('.location, .venue, .place') or
                                item.select_one('[class*="location"], [class*="venue"], [class*="place"]'))
                location = location_elem.get_text(strip=True) if location_elem else ""
                
                link_elem = item.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                if link and not link.startswith('http'):
                    link = f"https://weddingfairschedule.kr{link}"
                
                results.append({
                    "name": title,
                    "raw_date": date_text,
                    "location": location,
                    "source_url": link,
                    "source": "weddingfairschedule.kr"
                })
                    
            except Exception as e:
                logger.debug(f"항목 파싱 오류: {e}")
                continue
        
        return results
    
    def _parse_weddingo(self, html: str, url: str) -> List[Dict]:
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        sections = soup.select('section, div[class*="expo"], div[class*="wedding"], div[class*="event"], article, .card')
        
        for section in sections:
            try:
                text = section.get_text()
                
                if '광주' not in text:
                    continue
                
                title_elem = section.select_one('h1, h2, h3, h4, a, .title, .name')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 2:
                    continue
                
                date_elem = section.select_one('[class*="date"], [class*="schedule"], time, .period')
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                location_elem = section.select_one('[class*="location"], [class*="venue"], [class*="place"]')
                location = location_elem.get_text(strip=True) if location_elem else ""
                
                link_elem = section.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                
                results.append({
                    "name": title,
                    "raw_date": date_text,
                    "location": location,
                    "source_url": link,
                    "source": "weddingo.kr"
                })
                
            except Exception as e:
                logger.debug(f"섹션 파싱 오류: {e}")
                continue
        
        return results
    
    def _parse_gjweddingshow(self, html: str, url: str) -> List[Dict]:
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        main_content = soup.select_one('main, .content, #content, .main, .container, body')
        
        if not main_content:
            main_content = soup
        
        schedule_selectors = [
            '.schedule', '.event-list', '.expo-list', '.calendar', '.program',
            '[class*="schedule"]', '[class*="event"]', '[class*="expo"]', '[class*="program"]',
            'article', '.post', '.item', '.card'
        ]
        
        sections = []
        for selector in schedule_selectors:
            found = main_content.select(selector)
            if found:
                sections = found
                break
        
        for section in sections:
            try:
                title_elem = section.select_one('h1, h2, h3, h4, h5, .title, .name, a')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 2:
                    continue
                
                date_selectors = ['.date', '.schedule', '.period', 'time', 
                                 '[class*="date"]', '[class*="schedule"]']
                date_text = ""
                for date_sel in date_selectors:
                    date_elem = section.select_one(date_sel)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        break
                
                location_selectors = ['.location', '.venue', '.place',
                                      '[class*="location"]', '[class*="venue"]']
                location = ""
                for loc_sel in location_selectors:
                    loc_elem = section.select_one(loc_sel)
                    if loc_elem:
                        location = loc_elem.get_text(strip=True)
                        break
                
                link_elem = section.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                if link and not link.startswith('http'):
                    link = f"https://www.gjweddingshow.kr{link}"
                
                results.append({
                    "name": title,
                    "raw_date": date_text,
                    "location": location,
                    "source_url": link,
                    "source": "gjweddingshow.kr"
                })
                    
            except Exception as e:
                logger.debug(f"파싱 오류: {e}")
                continue
        
        return results
    
    def _parse_naver_search(self, html: str, url: str) -> List[Dict]:
        """네이버 검색 결과 파싱 (웨딩박람회 키워드)"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        items = soup.select('.item, .news, .blog', limit=20)
        
        for item in items:
            try:
                title_elem = item.select_one('.title, .news_tit, h3, a')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or '광주' not in title or '웨딩' not in title:
                    continue
                
                date_elem = item.select_one('.date, .info, time, span:last-child')
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                link_elem = item.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                
                results.append({
                    "name": title,
                    "raw_date": date_text,
                    "location": "광주광역시",
                    "source_url": link,
                    "source": "naver_search"
                })
                
            except Exception as e:
                continue
        
        return results
    
    def _parse_fallback(self, html: str, url: str, source_name: str) -> List[Dict]:
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        all_elements = soup.select('div, section, article, li, td')
        
        for elem in all_elements:
            try:
                text = elem.get_text()
                
                keywords = ['웨딩', '박람회', '웨딩박람', '결혼', 'wedding', 'expo', '페어']
                has_keyword = any(kw in text for kw in keywords)
                has_gwangju = '광주' in text
                
                if has_keyword and has_gwangju:
                    title_elem = elem.select_one('h1, h2, h3, h4, .title, strong, a')
                    title = title_elem.get_text(strip=True) if title_elem else elem.get_text()[:100]
                    
                    is_duplicate = any(r['name'] == title[:50] for r in results)
                    if title and not is_duplicate and len(title) > 3:
                        results.append({
                            "name": title[:200],
                            "raw_date": "",
                            "location": "광주광역시",
                            "source_url": url,
                            "source": source_name
                        })
                        
            except Exception:
                continue
        
        return results
    
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
                results = self._parse_fallback(html, url, name)
            
            logger.info(f"📊 {name}: {len(results)}건 수집")
            all_results.extend(results)
        
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
