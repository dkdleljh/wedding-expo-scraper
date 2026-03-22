#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 파싱 모듈 - 수집된 데이터 정리 및 정규화
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

from .config import CSV_COLUMNS


logger = logging.getLogger(__name__)


class ExpoParser:
    """웨딩박람회 데이터 파싱 및 정규화 클래스"""
    
    # 날짜 정규화 패턴
    DATE_PATTERNS = [
        # 2026.3.21 형식
        (r'(\d{4})[.\-년\s]+(\d{1,2})[.\-월\s]+(\d{1,2})일?', r'\1-\2-\3'),
        # 2026-03-21 형식 (이미 정규화됨)
        (r'(\d{4})-(\d{2})-(\d{2})', r'\1-\2-\3'),
        # 2026/03/21 형식
        (r'(\d{4})/(\d{2})/(\d{2})', r'\1-\2-\3'),
        # 03.21 ~ 03.22 형식 (시작일만)
        (r'^(\d{1,2})\.(\d{1,2})', r'{year}-\1-\2'),
    ]
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def _normalize_date(self, date_text: str) -> tuple:
        """날짜 텍스트를 시작일과 종료일로 분리"""
        if not date_text:
            return None, None
        
        date_text = date_text.strip()
        
        # 범위 분리 (~, -, –)
        range_separators = ['~', '~', '-', '–', '~', 'to', 'TO']
        parts = None
        
        for sep in range_separators:
            if sep in date_text:
                parts = date_text.split(sep)
                break
        
        if not parts:
            parts = [date_text]
        
        start_str = parts[0].strip()
        end_str = parts[1].strip() if len(parts) > 1 else start_str
        
        # 시작일 정규화
        start_date = self._parse_single_date(start_str)
        
        # 종료일 정규화
        end_date = self._parse_single_date(end_str)
        
        # 종료일이 시작일보다 이전이면 같은 날짜로 처리
        if end_date and start_date and end_date < start_date:
            end_date = start_date
        
        return start_date, end_date
    
    def _parse_single_date(self, date_str: str) -> Optional[str]:
        """단일 날짜 문자열 정규화"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # 다양한 형식 정규화
        # 2026.3.21 또는 2026.03.21
        match = re.search(r'(\d{4})[.\-년\s]+(\d{1,2})[.\-월\s]+(\d{1,2})일?', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 2026-03-21 (이미 정규화)
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        
        # 2026/03/21
        match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 3.21 (올해로 가정)
        match = re.search(r'^(\d{1,2})\.(\d{1,2})', date_str)
        if match:
            month, day = match.groups()
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        # 03월 21일
        match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', date_str)
        if match:
            month, day = match.groups()
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        """장소 정규화"""
        if not location:
            return ""
        
        location = location.strip()
        
        # 괄호 안의 내용 제거
        location = re.sub(r'\([^)]*\)', '', location)
        location = re.sub(r'\[[^\]]*\]', '', location)
        
        # 불필요한 공백 제거
        location = re.sub(r'\s+', ' ', location)
        
        return location.strip()
    
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
    
    def _extract_organizer(self, text: str) -> str:
        """주최사 정보 추출"""
        if not text:
            return ""
        
        # 일반적인 패턴
        patterns = [
            r'주최[:\s]*(.+?)(?:\n|$)',
            r'주관[:\s]*(.+?)(?:\n|$)',
            r'운영[:\s]*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def parse_all(self, raw_data: List[Dict]) -> List[Dict]:
        """모든 데이터 파싱 및 정규화"""
        parsed_results = []
        
        for item in raw_data:
            try:
                # 기본 데이터 추출
                name = self._normalize_name(item.get('name', ''))
                raw_date = item.get('raw_date', '')
                location = self._normalize_location(item.get('location', ''))
                source_url = item.get('source_url', '')
                source = item.get('source', '')
                
                if not name:
                    logger.debug(f"이름 없음 - 건너뜀")
                    continue
                
                # 날짜 파싱
                start_date, end_date = self._normalize_date(raw_date)
                
                # 날짜가 없으면 기본값 설정
                if not start_date:
                    start_date = datetime.now().strftime('%Y-%m-%d')
                if not end_date:
                    end_date = start_date
                
                # 장소가 없으면 기본값
                if not location:
                    location = "광주광역시"
                
                parsed_results.append({
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'location': location,
                    'organizer': '',
                    'source_url': source_url,
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
    # 테스트
    parser = ExpoParser()
    test_data = [
        {
            'name': '광주 웨딩 박람회 2026',
            'raw_date': '2026.3.21 ~ 2026.3.22',
            'location': '김대중컨벤션센터',
            'source_url': 'https://example.com',
            'source': 'test'
        },
        {
            'name': '전남 연합 웨딩페어',
            'raw_date': '2026-04-15',
            'location': '광주 금남로',
            'source_url': 'https://example.com',
            'source': 'test'
        }
    ]
    
    results = parser.parse_all(test_data)
    print(f"\n파싱 결과: {len(results)}건")
    for r in results:
        print(f"  - {r['name']}: {r['start_date']} ~ {r['end_date']} @ {r['location']}")
