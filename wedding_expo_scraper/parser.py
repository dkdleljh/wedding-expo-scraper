#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 파싱 모듈 - 정규화 및 보안 강화"""

import re
import logging
import calendar
import html
from urllib.parse import urlparse
from datetime import datetime, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ExpoParser:
    """데이터 정규화 및 보안 처리 클래스"""

    TARGET_WINDOW_MONTHS = 3
    
    # ============================================================================
    # 광주광역시 웨딩박람회 개최 장소 데이터베이스 (정확한 주소)
    # ============================================================================
    ORGANIZER_INFO = {
        '더베스트웨딩': {
            'contact': '062-714-1020',
            'operating_hours': '10:00~18:00',
            'website': 'https://www.gjweddingshow.kr/',
            'description': '광주 최대 규모 웨딩박람회 주관사. 연간 1,300쌍 이상 방문, 7년 연속 호남권 1위.'
        },
        '더베스트웨딩컴퍼니': {
            'contact': '062-714-1020',
            'operating_hours': '10:00~18:00',
            'website': 'https://www.gjweddingshow.kr/',
            'description': '광주 최대 규모 웨딩박람회 주관사.'
        },
        '레브웨딩': {
            'contact': '02-6959-2764',
            'operating_hours': '11:00~19:00',
            'website': 'http://revewedding.co.kr/',
            'description': '전국 연동 웨딩박람회 주관사.'
        },
        '한국웨딩연합회': {
            'contact': '02-3474-8800',
            'operating_hours': '10:00~18:00',
            'website': 'https://keu.or.kr/',
            'description': '전라·제주 지역 웨딩박람회 주관.'
        },
        '웨딩다모아': {
            'contact': '1661-8639',
            'operating_hours': '10:00~18:00',
            'website': 'https://weddingdamoa.com/',
            'description': '전국 웨딩박람회 일정 제공 플랫폼.'
        },
    }

    LOCATION_DATABASE = {
        '김대중컨벤션센터': {
            'name': '김대중컨벤션센터',
            'address': '광주 서구 상무누리로 30',
            'description': '광주 최대 전시시설'
        },
        '컨벤션타워': {
            'name': '컨벤션타워',
            'address': '광주 서구 치평동 1282-1',
            'description': '도심 접근성 우수'
        },
        '신세계백화점': {
            'name': '신세계백화점 광주신세계점',
            'address': '광주 서구 무진대로 932',
            'description': '8층 이벤트관'
        },
        '제이아트': {
            'name': '제이아트웨딩컨벤션',
            'address': '광주 서구 풍서좌로 269',
            'description': '웨딩 전문 시설'
        },
    }
    
    def __init__(self):
        self.current_year = datetime.now().year

    def _sanitize_text(self, text: str) -> str:
        """HTML 태그 제거 및 이스케이프 처리 (XSS 방지)"""
        if not text:
            return ""
        # 1. HTML 태그 제거
        text = re.sub(r'<[^>]*>', '', text)
        # 2. HTML 이스케이프
        return html.escape(text.strip())

    def _add_months(self, base_date: date, months: int) -> date:
        month_index = base_date.month - 1 + months
        year = base_date.year + month_index // 12
        month = month_index % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(base_date.day, last_day)
        return date(year, month, day)

    def _parse_single_date(self, date_str: str) -> Optional[str]:
        if not date_str:
            return None
        date_str = date_str.strip()
        
        # 형식 1: YYYY-MM-DD
        match = re.search(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
        if match:
            return date_str
        
        # 형식 2: YYYY.MM.DD
        match = re.search(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 6: MM월 DD일
        match = re.search(r'^(\d{1,2})월\s*(\d{1,2})일', date_str)
        if match:
            month, day = match.groups()
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        return None

    def _is_precise_gwangju_location(self, location: str) -> bool:
        if not location:
            return False
        normalized = location.strip()
        if not normalized or normalized in {"광주", "광주광역시"}:
            return False
        if "광주" not in normalized:
            return False
        return True

    def _normalize_location(self, location: str) -> str:
        if not location:
            return "광주광역시"
        
        location = self._sanitize_text(location)
        for key, data in self.LOCATION_DATABASE.items():
            if key in location:
                if data['address'] not in location:
                    return f"{data['name']} ({data['address']})"
                return location
        
        location = re.sub(r'\s+', ' ', location)
        return location.strip()
    
    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        name = self._sanitize_text(name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()

    def _get_organizer_info(self, organizer: str) -> Dict:
        if not organizer:
            return {'contact': '', 'operating_hours': '10:00~18:00', 'description': ''}
        
        for key, info in self.ORGANIZER_INFO.items():
            if key in organizer:
                return info
        
        return {'contact': '', 'operating_hours': '10:00~18:00', 'description': ''}

    def _build_description(self, name: str, organizer: str, location: str, source_url: str) -> str:
        organizer_info = self._get_organizer_info(organizer)
        description = organizer_info.get('description', '')
        if description:
            return description

        source_host = urlparse(source_url).netloc.replace('www.', '')
        return f"{name} 관련 웨딩박람회 정보입니다. (출처: {source_host})"

    def _record_key(self, item: Dict) -> tuple:
        return (
            (item.get("name") or "").strip().lower(),
            (item.get("start_date") or "").strip(),
            (item.get("location") or "").strip().lower(),
            (item.get("source_url") or "").strip().lower(),
        )
    
    def parse_all(self, raw_data: List[Dict]) -> List[Dict]:
        parsed_results = []
        
        for item in raw_data:
            try:
                name = self._normalize_name(item.get('name', ''))
                if not name: continue
                
                start_date = self._parse_single_date(item.get('start_date', ''))
                if not start_date: continue
                
                end_date = self._parse_single_date(item.get('end_date', '')) or start_date
                location = self._normalize_location(item.get('location', ''))
                
                if not self._is_precise_gwangju_location(location): continue
                
                organizer = self._sanitize_text(item.get('organizer', ''))
                organizer_info = self._get_organizer_info(organizer)
                source_url = item.get('source_url', '')
                
                description = self._sanitize_text(self._build_description(name, organizer, location, source_url))
                
                parsed_results.append({
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'operating_hours': self._sanitize_text(organizer_info['operating_hours']),
                    'location': location,
                    'organizer': organizer,
                    'contact': self._sanitize_text(organizer_info['contact']),
                    'source_url': source_url,
                    'description': description
                })
                
            except Exception as e:
                logger.warning(f"파싱 오류: {e}")
                continue
        
        return parsed_results

    def filter_valid_records(self, records: List[Dict]) -> List[Dict]:
        today = datetime.now().date()
        cutoff = self._add_months(today, self.TARGET_WINDOW_MONTHS)
        filtered = []
        seen = set()

        for item in records:
            try:
                start_dt = datetime.strptime(item['start_date'], '%Y-%m-%d').date()
                if start_dt < today or start_dt > cutoff: continue
                
                key = self._record_key(item)
                if key in seen: continue
                seen.add(key)
                filtered.append(item)
            except: continue

        filtered.sort(key=lambda x: (x['start_date'], x['name']))
        return filtered
