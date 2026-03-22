#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 파싱 모듈 - 수집된 데이터 정리 및 정규화 (완전 개선판)
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

from .config import CSV_COLUMNS


logger = logging.getLogger(__name__)


class ExpoParser:
    """웨딩박람회 데이터 파싱 및 정규화 클래스"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def _parse_single_date(self, date_str: str) -> Optional[str]:
        """단일 날짜 문자열 정규화"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # 이미 정규화된 형식
        match = re.search(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
        if match:
            return date_str
        
        # 2026.3.21 또는 2026.03.21
        match = re.search(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 26.03.21 (현재 연도)
        match = re.search(r'^(\d{1,2})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            month, day = match.group(2), match.group(3)
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        """장소 정규화"""
        if not location:
            return "광주광역시"
        
        location = location.strip()
        
        # 괄호 안의 상세 주소만 유지
        addr_match = re.search(r'\(([^)]+)\)', location)
        if addr_match:
            addr = addr_match.group(1)
            location = f"{location.split('(')[0].strip()} ({addr})"
        else:
            # 괄호 안 내용 제거
            location = re.sub(r'\([^)]*\)', '', location)
            location = re.sub(r'\[[^\]]*\]', '', location)
        
        # 불필요한 공백 제거
        location = re.sub(r'\s+', ' ', location)
        
        return location.strip() if location.strip() else "광주광역시"
    
    def _normalize_name(self, name: str) -> str:
        """박람회명 정규화"""
        if not name:
            return ""
        
        name = name.strip()
        
        # 불필요한 공백 제거
        name = re.sub(r'\s+', ' ', name)
        
        # 괄호 정리
        name = re.sub(r'\(\s*\)', '', name)
        name = re.sub(r'\[\s*\]', '', name)
        
        return name.strip()
    
    def parse_all(self, raw_data: List[Dict]) -> List[Dict]:
        """모든 데이터 파싱 및 정규화"""
        parsed_results = []
        
        for item in raw_data:
            try:
                # 기본 데이터 추출
                name = self._normalize_name(item.get('name', ''))
                
                if not name:
                    continue
                
                # 날짜 처리 (scraper에서 이미 분리된 경우)
                start_date = item.get('start_date', '')
                end_date = item.get('end_date', '')
                
                # raw_date가 있으면 파싱
                raw_date = item.get('raw_date', '')
                if raw_date and not start_date:
                    if '~' in raw_date:
                        parts = raw_date.split('~')
                        start_date = self._parse_single_date(parts[0].strip())
                        end_date = self._parse_single_date(parts[-1].strip())
                    else:
                        start_date = self._parse_single_date(raw_date)
                        end_date = start_date
                
                # 날짜가 없으면 기본값
                if not start_date:
                    start_date = datetime.now().strftime('%Y-%m-%d')
                if not end_date:
                    end_date = start_date
                
                # 장소 정규화
                location = self._normalize_location(item.get('location', ''))
                
                parsed_results.append({
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'location': location,
                    'organizer': item.get('organizer', ''),
                    'source_url': item.get('source_url', ''),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                logger.debug(f"파싱 완료: {name} | {start_date} ~ {end_date} | {location}")
                
            except Exception as e:
                logger.warning(f"파싱 오류 ({item.get('name', 'unknown')}): {e}")
                continue
        
        # 중복 제거 (이름 기준)
        seen = set()
        unique_results = []
        for item in parsed_results:
            name_key = item['name'].strip().lower()
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(item)
        
        # 날짜순 정렬
        unique_results.sort(key=lambda x: (x['start_date'], x['name']))
        
        logger.info(f"✅ 파싱 완료: {len(unique_results)}건 (중복 {len(parsed_results) - len(unique_results)}건 제거)")
        
        return unique_results


if __name__ == "__main__":
    parser = ExpoParser()
    test_data = [
        {
            'name': '광주 웨딩 박람회 2026',
            'start_date': '2026-03-21',
            'end_date': '2026-03-22',
            'location': '컨벤션타워 2층 (서구 치평동 1282-1)',
            'source_url': 'https://example.com',
            'source': 'test'
        }
    ]
    
    results = parser.parse_all(test_data)
    print(f"\n파싱 결과: {len(results)}건")
    for r in results:
        print(f"  - {r['name']}: {r['start_date']} ~ {r['end_date']} @ {r['location']}")
