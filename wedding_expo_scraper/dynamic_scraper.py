#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright 동적 페이지 스크래핑 모듈
JavaScript로 렌더링되는 페이지 지원
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .config import REQUEST_TIMEOUT


logger = logging.getLogger(__name__)

WAIT_STRATEGIES = {
    "gjweddingfesta.com": {
        "wait_until": "domcontentloaded",
        "selector": "h1, h2, h3, section, article",
        "post_wait_ms": 4000,
    },
    "weddingmoment.co.kr": {
        "wait_until": "domcontentloaded",
        "selector": "h3, section, article",
        "post_wait_ms": 2500,
    },
    "keu.or.kr": {
        "wait_until": "domcontentloaded",
        "selector": "div, section, article",
        "post_wait_ms": 2500,
    },
}


class DynamicScraper:
    """Playwright 기반 동적 페이지 스크래퍼"""
    
    def __init__(self, sources: List[Dict] = None):
        from .config import DYNAMIC_SOURCES
        self.current_year = datetime.now().year
        self.playwright = None
        self.browser = None
        self.sources = sources if sources is not None else DYNAMIC_SOURCES
        self.last_run_stats: Dict[str, Dict] = {}
        
    def _start_browser(self):
        """브라우저 시작"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright가 설치되지 않았습니다")
            return False
        
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            return True
        except Exception as e:
            logger.error(f"❌ 브라우저 시작 실패: {e}")
            return False
    
    def _close_browser(self):
        """브라우저 종료"""
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
    
    def _extract_date_and_location(self, text: str) -> tuple:
        date_str = ""
        location_str = "광주광역시"

        range_patterns = [
            r'(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일\s*[-~]\s*(?:(\d{4})년\s*)?(?:(\d{1,2})월\s*)?(\d{1,2})일',
            r'(\d{4})\.(\d{1,2})\.(\d{1,2}).{0,10}[-~].{0,10}(\d{4})\.(\d{1,2})\.(\d{1,2})',
        ]

        dates_found = []
        for pattern in range_patterns:
            for match in re.finditer(pattern, text):
                groups = match.groups()
                try:
                    if len(groups) == 6 and "." not in pattern:
                        start_year = int(groups[0] or self.current_year)
                        start_month = int(groups[1])
                        start_day = int(groups[2])
                        end_year = int(groups[3] or start_year)
                        end_month = int(groups[4] or start_month)
                        end_day = int(groups[5])
                    else:
                        start_year, start_month, start_day, end_year, end_month, end_day = map(int, groups)
                    dates_found.extend(
                        [
                            datetime(start_year, start_month, start_day),
                            datetime(end_year, end_month, end_day),
                        ]
                    )
                except ValueError:
                    continue

        date_patterns = [
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{1,2})월\s*(\d{1,2})일',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 3 and ('년' in pattern or len(match[0]) == 4):
                        year, month, day = match
                    else:
                        month, day = match[0], match[1]
                        year = str(self.current_year)
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
            r'LG전자베스트샵\s*동광주점[^\n]{0,50}',
            r'컨벤션\s*타워[^\n]{0,50}',
            r'신세계백화점[^\n]{0,50}',
            r'킨텍스[^\n]{0,50}',
            r'세텍[^\n]{0,50}',
            r'김대중[^\n]{0,50}',
            r'제이아트[^\n]{0,50}',
            r'염주[^\n]{0,50}',
            r'광주여대[^\n]{0,80}',
            r'더베스트웨딩\s*사옥[^\n]{0,50}',
            r'광주\s*[^\n]{10,80}',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location_str = match.group(0).strip()[:80]
                break
        
        return date_str, location_str
    
    def _get_wait_strategy(self, url: str, wait_selector: str = None) -> Dict[str, object]:
        strategy = {
            "wait_until": "domcontentloaded",
            "selector": wait_selector or "body",
            "post_wait_ms": 2000,
        }
        for domain, override in WAIT_STRATEGIES.items():
            if domain in url:
                strategy.update(override)
                break
        if wait_selector:
            strategy["selector"] = wait_selector
        return strategy

    def scrape_dynamic_page(self, url: str, wait_selector: str = None) -> Optional[str]:
        """동적 페이지 스크래핑"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("⚠️ Playwright가 설치되지 않았습니다")
            return None
        
        try:
            with sync_playwright() as p:
                strategy = self._get_wait_strategy(url, wait_selector)
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                logger.info(f"📡 Playwright로 페이지 로드: {url}")
                
                page.goto(url, wait_until=strategy["wait_until"], timeout=REQUEST_TIMEOUT * 1000)
                
                try:
                    page.wait_for_selector(str(strategy["selector"]), timeout=10000)
                except PlaywrightTimeout:
                    logger.warning(f"⚠️ 선택자 '{strategy['selector']}' 대기 시간 초과")

                page.wait_for_timeout(int(strategy["post_wait_ms"]))
                
                html = page.content()
                browser.close()
                return html
                
        except Exception as e:
            logger.error(f"❌ 동적 페이지 스크래핑 실패: {e}")
            return None
    
    def scrape_and_extract(self, url: str, wait_selector: str = None, source_name: str = "dynamic_page", region: str = "광주") -> Optional[List[Dict]]:
        """동적 페이지 스크래핑 + 데이터 추출"""
        from bs4 import BeautifulSoup
        
        html = self.scrape_dynamic_page(url, wait_selector)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        results = []
        full_text = soup.get_text()
        
        if '광주' in full_text and ('웨딩' in full_text or '박람회' in full_text):
            date_str, location_str = self._extract_date_and_location(full_text)
            if date_str:
                results.append({
                    "name": "광주 웨딩박람회 (동적)",
                    "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                    "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                    "location": location_str,
                    "organizer": "",
                    "source_url": url,
                    "source": source_name,
                    "region": region
                })
        
        for h3 in soup.find_all('h3'):
            title = h3.get_text(strip=True)
            if '광주' in title and any(kw in title for kw in ['웨딩', '박람회', '페스타', '페어']):
                parent_text = h3.find_parent(['div', 'section', 'article']).get_text() if h3.find_parent(['div', 'section', 'article']) else ""
                date_str, location_str = self._extract_date_and_location(parent_text)
                
                results.append({
                    "name": title,
                    "start_date": date_str.split(' ~ ')[0] if '~' in date_str else date_str,
                    "end_date": date_str.split(' ~ ')[-1] if '~' in date_str else date_str,
                    "location": location_str,
                    "organizer": "",
                    "source_url": url,
                    "source": source_name,
                    "region": region
                })
        
        logger.info(f"📊 동적 스크래핑: {len(results)}건 수집")
        return results
    
    def scrape_all(self) -> List[Dict]:
        """전체 동적 소스 스크래핑"""
        all_results = []
        self.last_run_stats = {}
        
        for source in self.sources:
            url = source["url"]
            name = source["name"]
            
            logger.info(f"📡 동적 스크래핑: {name}")
            
            try:
                results = self.scrape_and_extract(url, source_name=name, region=source.get("region", "광주"))
            except TypeError:
                results = self.scrape_and_extract(url)

            if results is None:
                logger.info(f"🔁 {name} 재시도")
                try:
                    results = self.scrape_and_extract(url, source_name=name, region=source.get("region", "광주"))
                except TypeError:
                    results = self.scrape_and_extract(url)

            if results is None:
                logger.warning(f"⚠️ {name} 최종 실패")
                self.last_run_stats[name] = {
                    "success": False,
                    "result_count": 0,
                    "error": "fetch_failed",
                    "url": url,
                    "kind": "dynamic",
                }
                continue

            if results:
                for item in results:
                    item.setdefault("source", name)
                    item.setdefault("region", source.get("region", "광주"))
                all_results.extend(results)
                logger.info(f"📊 {name}: {len(results)}건")
                self.last_run_stats[name] = {
                    "success": True,
                    "result_count": len(results),
                    "error": "",
                    "url": url,
                    "kind": "dynamic",
                }
            else:
                logger.info(f"ℹ️ {name}: 수집 결과 없음")
                self.last_run_stats[name] = {
                    "success": True,
                    "result_count": 0,
                    "error": "",
                    "url": url,
                    "kind": "dynamic",
                }
        
        logger.info(f"\n✅ 동적 소스 총 {len(all_results)}건 수집")
        return all_results

    def get_last_run_stats(self) -> Dict[str, Dict]:
        return dict(self.last_run_stats)
    
    def scrape_with_fallback(self, url: str, regular_scraper_func) -> List[Dict]:
        """일반 스크래핑 실패 시 Playwright 폴백"""
        import requests
        
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200 and len(response.text) > 1000:
                logger.info(f"✅ 일반 스크래핑 성공: {url}")
                return []
        except:
            pass
        
        logger.info(f"🔄 폴백: Playwright로 재시도: {url}")
        return self.scrape_and_extract(url)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright가 설치되지 않았습니다")
        print("   pip install playwright && python -m playwright install chromium")
    else:
        scraper = DynamicScraper()
        
        test_url = "https://www.gjweddingshow.kr/"
        print(f"🧪 동적 페이지 테스트: {test_url}")
        
        results = scraper.scrape_and_extract(test_url)
        print(f"\n결과: {len(results)}건")
        for r in results:
            print(f"  - {r['name']}")
