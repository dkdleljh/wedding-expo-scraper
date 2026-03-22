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
    """웨딩박람회 스크래핑 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.results: List[Dict] = []
        
    def _get_headers(self) -> Dict[str, str]:
        """요청 헤더 생성"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    def _respectful_delay(self):
        """서버에 부담을 주지 않는 딜레이"""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """웹페이지 가져오기 (재시도 포함)"""
        for attempt in range(REQUEST_RETRY_COUNT):
            try:
                self._respectful_delay()
                
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                # 인코딩 처리
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
        """weddingfairschedule.kr 파싱"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 웨딩 박람회 항목 찾기
        # 일반적인 선택자 시도
        selectors = [
            '.expo-item',
            '.wedding-item',
            '.schedule-item',
            '.event-item',
            '.card',
            'article',
            '.list-item'
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.info(f"🔍 선택자 '{selector}'로 {len(items)}개 항목 발견")
                break
        
        for item in items:
            try:
                # 제목 추출
                title_elem = (item.select_one('h2, h3, h4, .title, .name') or 
                             item.select_one('[class*="title"], [class*="name"]'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # 날짜 추출
                date_elem = (item.select_one('.date, .schedule, .period, time') or
                            item.select_one('[class*="date"], [class*="schedule"]'))
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                
                # 장소 추출
                location_elem = (item.select_one('.location, .venue, .place') or
                                item.select_one('[class*="location"], [class*="venue"]'))
                location = location_elem.get_text(strip=True) if location_elem else ""
                
                # 링크 추출
                link_elem = item.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                if link and not link.startswith('http'):
                    link = f"https://weddingfairschedule.kr{link}"
                
                # 광주 관련 데이터만 필터링
                if title and ('광주' in title or 'Gwangju' in title.upper() or
                           '광주' in location or '광주' in date_text):
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
        """weddingo.kr 파싱"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 페이지 내 모든 섹션 탐색
        sections = soup.select('section, div[class*="expo"], div[class*="wedding"], div[class*="event"]')
        
        for section in sections:
            try:
                # 텍스트에서 광주 검색
                text = section.get_text()
                if '광주' not in text:
                    continue
                
                # 제목
                title_elem = section.select_one('h2, h3, h4, a')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title:
                    continue
                
                # 날짜, 장소
                date_elem = section.select_one('[class*="date"], [class*="schedule"], time')
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
        """gjweddingshow.kr (광주 공식) 파싱"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 메인 컨텐츠 영역 찾기
        main_content = soup.select_one('main, .content, #content, .main')
        
        if not main_content:
            main_content = soup
        
        # 스케줄/일정 섹션 찾기
        schedule_selectors = [
            '.schedule', '.event-list', '.expo-list', '.calendar',
            '[class*="schedule"]', '[class*="event"]', '[class*="expo"]'
        ]
        
        sections = []
        for selector in schedule_selectors:
            found = main_content.select(selector)
            if found:
                sections = found
                break
        
        for section in sections:
            try:
                title_elem = section.select_one('h2, h3, h4, .title, .name')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                # 날짜 추출 - 다양한 형식 지원
                date_selectors = ['.date', '.schedule', '.period', 'time', 
                                 '[class*="date"]', '[class*="schedule"]']
                date_text = ""
                for date_sel in date_selectors:
                    date_elem = section.select_one(date_sel)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        break
                
                # 장소 추출
                location_selectors = ['.location', '.venue', '.place',
                                      '[class*="location"]', '[class*="venue"]']
                location = ""
                for loc_sel in location_selectors:
                    loc_elem = section.select_one(loc_sel)
                    if loc_elem:
                        location = loc_elem.get_text(strip=True)
                        break
                
                # 링크
                link_elem = section.select_one('a[href]')
                link = link_elem['href'] if link_elem else ""
                if link and not link.startswith('http'):
                    link = f"https://www.gjweddingshow.kr{link}"
                
                if title:
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
    
    def _parse_fallback(self, html: str, url: str, source_name: str) -> List[Dict]:
        """폴백 파싱 - 모든 웹페이지에서 웨딩박람회 정보 추출"""
        results = []
        soup = BeautifulSoup(html, 'lxml')
        
        # 모든 링크와 텍스트 탐색
        all_elements = soup.select('div, section, article, li')
        
        for elem in all_elements:
            try:
                text = elem.get_text()
                
                # 광주 + 웨딩/박람회 관련 키워드 포함 확인
                keywords = ['웨딩', '박람회', '웨딩박람', '결혼', 'wedding', 'expo']
                has_keyword = any(kw in text for kw in keywords)
                has_gwangju = '광주' in text
                
                if has_keyword and has_gwangju:
                    # 제목 추출 시도
                    title_elem = elem.select_one('h1, h2, h3, h4, .title, strong')
                    title = title_elem.get_text(strip=True) if title_elem else elem.get_text()[:100]
                    
                    # 중복 체크
                    is_duplicate = any(r['name'] == title for r in results)
                    if title and not is_duplicate:
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
        """모든 소스에서 스크래핑"""
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
            
            # 소스별 파싱
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
        
        # 중복 제거 (이름 기준)
        seen = set()
        unique_results = []
        for item in all_results:
            name_key = item['name'].strip().lower()
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(item)
        
        logger.info(f"\n✅ 총 {len(unique_results)}건의 고유 데이터 수집 완료")
        
        return unique_results


if __name__ == "__main__":
    # 테스트 실행
    scraper = WeddingExpoScraper()
    results = scraper.scrape_all()
    print(f"\n수집 결과: {len(results)}건")
    for r in results:
        print(f"  - {r.get('name', 'N/A')}")
