#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""티스토리 자동 포스팅 모듈"""

import logging
import requests
import json
from datetime import datetime
from typing import List, Dict

from .config import (
    TISTORY_ACCESS_TOKEN, TISTORY_BLOG_NAME, TISTORY_CATEGORY_ID,
    TISTORY_TAGS, TISTORY_VISIBILITY, TISTORY_ACCEPT_COMMENT
)

logger = logging.getLogger(__name__)

class TistoryPoster:
    """티스토리 API를 이용한 포스팅 클래스"""
    
    def __init__(self):
        self.access_token = TISTORY_ACCESS_TOKEN
        self.blog_name = TISTORY_BLOG_NAME
        self.base_url = "https://www.tistory.com/apis/post/write"
        
    def is_configured(self) -> bool:
        return bool(self.access_token and self.blog_name)
    
    def _format_content(self, data: List[Dict]) -> str:
        """수집된 데이터를 HTML 형식으로 변환"""
        today = datetime.now().strftime('%Y년 %m월 %d일')
        html = f"<h2>🌸 광주광역시 웨딩박람회 주간 업데이트 ({today})</h2>"
        html += "<p>광주 지역의 최신 웨딩박람회 일정을 안내해 드립니다. 예비 부부님들의 행복한 결혼 준비를 응원합니다!</p>"
        
        html += '<table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">'
        html += '<tr style="background-color: #f2f2f2;">'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">행사명</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">날짜</th>'
        html += '<th style="border: 1px solid #ddd; padding: 8px;">장소</th>'
        html += '</tr>'
        
        for item in data:
            html += '<tr>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;"><b>{item["name"]}</b></td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{item["start_date"]} ~ {item["end_date"]}</td>'
            html += f'<td style="border: 1px solid #ddd; padding: 8px;">{item["location"]}</td>'
            html += '</tr>'
        
        html += '</table>'
        html += f'<p style="color: #666; font-size: 0.9em; margin-top: 20px;">* 본 정보는 자동 수집된 데이터로, 방문 전 해당 주관사 사이트에서 최종 일정을 확인하시기 바랍니다.</p>'
        
        return html

    def post_update(self, data: List[Dict]) -> bool:
        """블로그 포스팅 실행"""
        if not self.is_configured() or not data:
            logger.warning("티스토리 설정이 누락되었거나 게시할 데이터가 없습니다.")
            return False
        
        title = f"🌸 [광주 웨딩박람회] {datetime.now().strftime('%m월 %d일')} 최신 일정 업데이트"
        content = self._format_content(data)
        
        params = {
            "access_token": self.access_token,
            "output": "json",
            "blogName": self.blog_name,
            "title": title,
            "content": content,
            "visibility": TISTORY_VISIBILITY,
            "category": TISTORY_CATEGORY_ID,
            "tag": TISTORY_TAGS,
            "acceptComment": TISTORY_ACCEPT_COMMENT
        }
        
        try:
            response = requests.post(self.base_url, data=params, timeout=15)
            result = response.json()
            
            if response.status_code == 200 and "tistory" in result:
                url = result["tistory"].get("url")
                logger.info(f"✅ 티스토리 포스팅 성공: {url}")
                return True
            else:
                logger.error(f"❌ 티스토리 포스팅 실패: {result}")
                return False
        except Exception as e:
            logger.error(f"❌ 티스토리 API 오류: {e}")
            return False
