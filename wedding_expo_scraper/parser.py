#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 파싱 모듈 - 정규화"""

import re
import logging
import calendar
from urllib.parse import urlparse
from datetime import datetime, date
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ExpoParser:
    """데이터 정규화"""

    TARGET_WINDOW_MONTHS = 3
    
    # ============================================================================
    # 광주광역시 웨딩박람회 개최 장소 데이터베이스 (정확한 주소)
    # ============================================================================
    # ============================================================================
    # 주관사별 연락처 및 운영시간 데이터베이스
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
            'description': '광주 최대 규모 웨딩박람회 주관사. 연간 1,300쌍 이상 방문, 7년 연속 호남권 1위.'
        },
        '베스트웨딩': {
            'contact': '062-714-1020',
            'operating_hours': '10:00~18:00',
            'website': 'https://www.gjweddingshow.kr/',
            'description': '광주 최대 규모 웨딩박람회 주관사.'
        },
        '베스트웨딩컴퍼니': {
            'contact': '062-714-1020',
            'operating_hours': '10:00~18:00',
            'website': 'https://www.gjweddingshow.kr/',
            'description': '광주 최대 규모 웨딩박람회 주관사.'
        },
        '레브웨딩': {
            'contact': '02-6959-2764',
            'operating_hours': '11:00~19:00',
            'website': 'http://revewedding.co.kr/',
            'description': '전국联网 웨딩박람회 주관사. 50여명 플래너 보유, 1:1 맞춤 웨딩 컨설팅 제공.'
        },
        '한국웨딩연합회': {
            'contact': '02-3474-8800',
            'operating_hours': '10:00~18:00',
            'website': 'https://keu.or.kr/',
            'description': '한국웨딩연합회主办 박람회. 전라·제주 지역 웨딩박람회 주관.'
        },
        '웨딩다모아': {
            'contact': '1661-8639',
            'operating_hours': '10:00~18:00',
            'website': 'https://weddingdamoa.com/',
            'description': '전국 웨딩박람회 일정 및 무료초대권 제공 플랫폼.'
        },
        '레이크웨딩': {
            'contact': '062-380-1000',
            'operating_hours': '10:00~18:00',
            'website': '',
            'description': '광주 지역 웨딩박람회 주관사. 컨벤션타워 웨딩박람회 주관.'
        },
        '메리포엠': {
            'contact': '062-942-0100',
            'operating_hours': '10:00~18:00',
            'website': '',
            'description': '메리포엠 웨딩홀 주관 박람회. 광산구 최대 규모 웨딩홀.'
        },
        '정우웨딩': {
            'contact': '062-222-2344',
            'operating_hours': '10:00~18:00',
            'website': 'https://www.jwoowedding.com/',
            'description': '광주 웨딩플래너 컨설팅 전문. 김대중컨벤션센터 웨딩박람회 주관.'
        },
    }

    EXHIBITOR_TEMPLATE = ""

    # ============================================================================
    # 장소 데이터베이스
    # ============================================================================
    LOCATION_DATABASE = {
        '김대중컨벤션센터': {
            'name': '김대중컨벤션센터',
            'address': '광주 서구 상무누리로 30 (치평동 1159-2)',
            'description': '광주 최대 전시시설, 지하철 1호선 상무역 도보 5분'
        },
        '컨벤션타워': {
            'name': '컨벤션타워',
            'address': '광주 서구 치평동 1282-1',
            'description': '도심 접근성 우수'
        },
        '신세계백화점': {
            'name': '신세계백화점 광주신세계점',
            'address': '광주 서구 무진대로 932 (광천동 49-1)',
            'description': '8층 이벤트관'
        },
        '제이아트': {
            'name': '제이아트웨딩컨벤션',
            'address': '광주 서구 풍서좌로 269 (벽진동 267-20)',
            'description': '웨딩 전문 시설'
        },
        'LG전자베스트샵': {
            'name': 'LG전자베스트샵 동광주점',
            'address': '광주 북구 동문대로 168번길 6 (두암동)',
            'description': '혼수가전 상담 가능'
        },
        '염주종합체육관': {
            'name': '염주종합체육관',
            'address': '광주 서구 금화로 278 (풍암동 423-2)',
            'description': '최대 규모 웨딩박람회 개최 가능'
        },
        '염주': {
            'name': '염주종합체육관',
            'address': '광주 서구 금화로 278 (풍암동 423-2)',
            'description': '최대 규모 웨딩박람회 개최 가능'
        },
        '유니버시아드': {
            'name': '광주여대 유니버시아드 체육관',
            'address': '광주 광산구 광주여대길 6 (산정동 158)',
            'description': '광산구 최대 체육관'
        },
        '여대': {
            'name': '광주여대 유니버시아드 체육관',
            'address': '광주 광산구 광주여대길 6 (산정동 158)',
            'description': '광산구 최대 체육관'
        },
        '더베스트': {
            'name': '더베스트웨딩컴퍼니 사옥',
            'address': '광주 동구 서석로 13-1 3층 (불로동 97-6)',
            'description': ''
        },
        '드메르': {
            'name': '드메르웨딩홀',
            'address': '광주광역시 동구',
            'description': ''
        },
        '메리포엠': {
            'name': '메리포엠 웨딩홀',
            'address': '광주 광산구 무진대로 282 (우산동 1589-1)',
            'description': ''
        },
        '빛고을': {
            'name': '빛고을체육관',
            'address': '광주 서구 금화로 278 (풍암동 423-2)',
            'description': '염주종합체육관 부지 내'
        },
        '빛고을체육관': {
            'name': '빛고을체육관',
            'address': '광주 서구 금화로 278 (풍암동 423-2)',
            'description': '염주종합체육관 부지 내'
        },
        '서광주': {
            'name': 'LG전자베스트샵 서광주본점',
            'address': '광주 서구 상무대로 886 (쌍촌동 982-24)',
            'description': '서구 소재 전자기기 매장'
        },
        '365': {
            'name': '365婚礼Hall',
            'address': '광주광역시',
            'description': '365일 운영婚礼홀'
        },
    }
    
    def __init__(self):
        self.current_year = datetime.now().year

    def _add_months(self, base_date: date, months: int) -> date:
        month_index = base_date.month - 1 + months
        year = base_date.year + month_index // 12
        month = month_index % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(base_date.day, last_day)
        return date(year, month, day)

    def _parse_date_to_date(self, date_str: str) -> Optional[date]:
        if not date_str:
            return None

        normalized = self._parse_single_date(date_str)
        if not normalized:
            return None

        try:
            return datetime.strptime(normalized, '%Y-%m-%d').date()
        except ValueError:
            return None

    def _is_precise_gwangju_location(self, location: str) -> bool:
        if not location:
            return False

        normalized = location.strip()
        if not normalized or normalized in {"광주", "광주광역시"}:
            return False

        if "광주" not in normalized:
            return False

        for data in self.LOCATION_DATABASE.values():
            if data["name"] in normalized or data["address"] in normalized:
                return True

        for keyword in self.LOCATION_DATABASE.keys():
            if keyword in normalized:
                return True

        if re.search(r'\d{1,4}\s?(층|F)', normalized):
            return True

        if re.search(r'\d{2,4}-\d{1,4}', normalized):
            return True

        return False

    def _record_key(self, item: Dict) -> tuple:
        return (
            (item.get("name") or "").strip().lower(),
            (item.get("start_date") or "").strip(),
            (item.get("end_date") or "").strip(),
            (item.get("location") or "").strip().lower(),
            (item.get("source_url") or "").strip().lower(),
            (item.get("organizer") or "").strip().lower(),
        )

    def _build_description(self, name: str, organizer: str, location: str, source_url: str) -> str:
        organizer_info = self._get_organizer_info(organizer)
        description = (organizer_info.get('description') or '').strip()
        if description:
            return description

        source_host = urlparse(source_url).netloc.replace('www.', '')

        if organizer and location:
            return f"{organizer} 주관의 {location} 웨딩박람회입니다."
        if organizer:
            return f"{organizer} 주관의 광주광역시 웨딩박람회입니다."
        if name:
            if source_host:
                return f"{name} 관련 웨딩박람회 정보입니다. 출처: {source_host}"
            return f"{name} 관련 웨딩박람회 정보입니다."
        return "광주광역시 웨딩박람회 정보입니다."
        
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
        
        # 형식 3: YYYY.MM.DD(요일)
        match = re.search(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})\([^)]+\)$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 4: MM.DD(또는 YYYY.MM.DD 형식)
        match = re.search(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 5: YY.MM.DD (짧은 연도) - 현재 연도 기준 유연한 처리
        match = re.search(r'^(\d{2})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if match:
            year, month, day = match.groups()
            yy = int(year)
            current_yy = self.current_year % 100  # 2026 → 26
            if yy <= current_yy:
                full_year = 2000 + yy  # 현재 세기 이하
            else:
                full_year = 1900 + yy  # 과거 세기
            return f"{full_year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 6: MM월 DD일 또는 MM월 DD일(요일)
        match = re.search(r'^(\d{1,2})월\s*(\d{1,2})일', date_str)
        if match:
            month, day = match.groups()
            return f"{self.current_year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 7: YYYY년 MM월 DD일
        match = re.search(r'^(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 형식 8: MM/DD/YYYY
        match = re.search(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
        if match:
            month, day, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        if not location:
            return "광주광역시"
        
        location = location.strip()
        original = location
        
        # ============================================================================
        # 정확한 주소 데이터베이스 매칭
        # ============================================================================
        for key, data in self.LOCATION_DATABASE.items():
            if key in location:
                # 상세 주소가 없으면 추가
                if data['address'] not in location:
                    return f"{data['name']} ({data['address']})"
                return location
        
        # ============================================================================
        # 키워드 기반 주소 매칭
        # ============================================================================
        location_keywords = {
            '컨벤션타워': ('컨벤션타워 2층', '광주 서구 치평동 1282-1'),
            '김대중': ('김대중컨벤션센터', '광주 서구 상무누리로 30 (치평동 1159-2)'),
            '신세계': ('신세계백화점 광주신세계점', '광주 서구 무진대로 932 (광천동 49-1)'),
            '제이아트': ('제이아트웨딩컨벤션', '광주 서구 풍서좌로 269 (벽진동 267-20)'),
            'LG': ('LG전자베스트샵 동광주점', '광주 북구 동문대로 168번길 6 (두암동)'),
            '염주': ('염주종합체육관', '광주 서구 금화로 278'),
            '유니버시아드': ('광주여대 유니버시아드 체육관', '광주 광산구 광주여대길 6 (산정동 158)'),
            '여대': ('광주여대 유니버시아드 체육관', '광주 광산구 광주여대길 6 (산정동 158)'),
        }
        
        for keyword, (name, addr) in location_keywords.items():
            if keyword in location:
                if len(location) < 10:  # 짧으면 상세 주소 추가
                    return f"{name} ({addr})"
                return location
        
        # ============================================================================
        # 일반 정리
        # ============================================================================
        location = re.sub(r'\s+', ' ', location)
        location = re.sub(r'\(\s*\)', '', location)
        location = re.sub(r'\[\s*\]', '', location)
        
        # 너무 짧으면 기본값
        if len(location) < 5:
            return "광주광역시"
        
        return location.strip()
    
    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        name = name.strip()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'\(\s*\)', '', name)
        name = re.sub(r'\[\s*\]', '', name)
        return name.strip()

    def _get_organizer_info(self, organizer: str) -> Dict:
        if not organizer:
            return {
                'contact': '',
                'operating_hours': '10:00~18:00',
                'description': self.EXHIBITOR_TEMPLATE
            }
        
        for key, info in self.ORGANIZER_INFO.items():
            if key in organizer:
                return {
                    'contact': info['contact'],
                    'operating_hours': info['operating_hours'],
                    'description': info.get('description', '') + '\n\n' + self.EXHIBITOR_TEMPLATE
                }
        
        return {
            'contact': '',
            'operating_hours': '10:00~18:00',
            'description': self.EXHIBITOR_TEMPLATE
        }
    
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
                    continue
                if not end_date:
                    end_date = start_date
                
                location = self._normalize_location(item.get('location', ''))
                if not self._is_precise_gwangju_location(location):
                    continue
                
                organizer = item.get('organizer', '')
                organizer_info = self._get_organizer_info(organizer)

                source_url = item.get('source_url', '')
                if not source_url:
                    continue
                description = self._build_description(name, organizer, location, source_url)
                
                parsed_results.append({
                    'name': name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'operating_hours': organizer_info['operating_hours'],
                    'location': location,
                    'organizer': organizer,
                    'contact': organizer_info['contact'],
                    'source_url': source_url,
                    'description': description
                })
                
            except Exception as e:
                logger.warning(f"파싱 오류: {e}")
                continue
        
        seen = set()
        unique_results = []
        for item in parsed_results:
            record_key = self._record_key(item)
            if record_key not in seen:
                seen.add(record_key)
                unique_results.append(item)
        
        unique_results.sort(key=lambda x: (x['start_date'], x['name']))
        logger.info(f"✅ 파싱 완료: {len(unique_results)}건")
        
        return unique_results

    def filter_valid_records(self, records: List[Dict]) -> List[Dict]:
        today = datetime.now().date()
        cutoff = self._add_months(today, self.TARGET_WINDOW_MONTHS)

        filtered = []
        seen = set()

        for item in records:
            try:
                start_date = self._parse_date_to_date(item.get('start_date', ''))
                end_date = self._parse_date_to_date(item.get('end_date', '')) or start_date
                location = self._normalize_location(item.get('location', ''))
                source_url = (item.get('source_url') or '').strip()

                if not start_date or not end_date:
                    continue
                if start_date < today or start_date > cutoff:
                    continue
                if not self._is_precise_gwangju_location(location):
                    continue
                if not source_url:
                    continue

                cleaned = dict(item)
                cleaned['start_date'] = start_date.strftime('%Y-%m-%d')
                cleaned['end_date'] = end_date.strftime('%Y-%m-%d')
                cleaned['location'] = location
                cleaned['source_url'] = source_url
                cleaned['description'] = self._build_description(
                    cleaned.get('name', ''),
                    cleaned.get('organizer', ''),
                    cleaned.get('location', ''),
                    cleaned.get('source_url', ''),
                )
                organizer_info = self._get_organizer_info(cleaned.get('organizer', ''))
                cleaned['operating_hours'] = cleaned.get('operating_hours') or organizer_info['operating_hours']
                cleaned['contact'] = cleaned.get('contact') or organizer_info['contact']

                record_key = self._record_key(cleaned)
                if record_key in seen:
                    continue
                seen.add(record_key)
                filtered.append(cleaned)
            except Exception as e:
                logger.warning(f"필터링 오류: {e}")
                continue

        filtered.sort(key=lambda x: (x['start_date'], x['name']))
        return filtered
