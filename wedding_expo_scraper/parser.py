#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 파싱 모듈 - 정규화"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ExpoParser:
    """데이터 정규화"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def _parse_single_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        date_str = date_str.strip()
        
        match = re.search(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
        if match:
            return date_str
        
        match = re.search(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        match = re.search(r'^(\d{1,2})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            month, day = match.group(2), match.group(3)
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        if not location:
            return "광주광역시"
        location = location.strip()
        location = re.sub(r'\([^)]*\)', lambda m: f"({m.group(0)[1:-1]})" if len(m.group(0)) > 3 else '', location)
        location = re.sub(r'\s+', ' ', location)
        return location.strip() if location.strip() else "광주광역시"
    
    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'\(\s*\)', '', name)
        name = re.sub(r'\[\s*\]', '', name)
        return name.strip()
    
    def parse_all(self, raw_data: List[Dict]) -> List[Dict]:
        parsed_results = []
        
        for item in raw_data:
            try:
                name = self._normalize_name(item.get('name', ''))
                if not name:
                    continue
                
                start_date = item.get('start_date', '')
                end_date = item.get('end_date', '')
                raw_date = item.get('raw_date', '')
                
                if raw_date and not start_date:
                    if '~' in raw_date:
                        parts = raw_date.split('~')
                        start_date = self._parse_single_date(parts[0].strip())
                        end_date = self._parse_single_date(parts[-1].strip())
                    else:
                        start_date = self._parse_single_date(raw_date)
                        end_date = start_date
                
                if not start_date:
                    start_date = datetime.now().strftime('%Y-%m-%d')
                if not end_date:
                    end_date = start_date
                
                location = self._normalize_location(item.get('location', ''))
                
                parsed_results.append({
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'location': location,
                    'organizer': item.get('organizer', ''),
                    'source_url': item.get('source_url', ''),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'region': item.get('region', '기타')
                })
                
            except Exception as e:
                logger.warning(f"파싱 오류: {e}")
                continue
        
        seen = set()
        unique_results = []
        for item in parsed_results:
            name_key = item['name'].strip().lower()
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(item)
        
        unique_results.sort(key=lambda x: (x['start_date'], x['name']))
        logger.info(f"✅ 파싱 완료: {len(unique_results)}건")
        
        return unique_results
