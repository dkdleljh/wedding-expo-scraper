#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
알림 모듈 - Discord/Telegram 웹훅
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests

from .config import DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


logger = logging.getLogger(__name__)


class NotificationService:
    """알림 서비스 - Discord/Telegram"""
    
    def __init__(self):
        self.discord_webhook = DISCORD_WEBHOOK_URL
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
    
    def _send_discord(self, embed: Dict) -> bool:
        """Discord 웹훅 전송"""
        if not self.discord_webhook:
            logger.debug("Discord 웹훅 미설정")
            return False
        
        try:
            response = requests.post(
                self.discord_webhook,
                json={"embeds": [embed]},
                timeout=10
            )
            if response.status_code == 204:
                logger.info("✅ Discord 알림 전송 완료")
                return True
            else:
                logger.warning(f"⚠️ Discord 전송 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Discord 오류: {e}")
            return False
    
    def _send_telegram(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Telegram 봇 전송"""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.debug("Telegram 설정 미완료")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.json().get("ok"):
                logger.info("✅ Telegram 알림 전송 완료")
                return True
            else:
                logger.warning(f"⚠️ Telegram 전송 실패")
                return False
        except Exception as e:
            logger.error(f"❌ Telegram 오류: {e}")
            return False
    
    def send_wedding_expo_notification(self, new_events: List[Dict], updated_count: int = 0) -> bool:
        """웨딩박람회 알림 전송"""
        if not new_events and updated_count == 0:
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Discord 임베드
        embed = {
            "title": "🆕 광주광역시 웨딩박람회 업데이트",
            "description": f"📅 {timestamp}",
            "color": 5763719,  # 초록
            "fields": [],
            "footer": {"text": "웨딩박람회 자동 스크래핑 시스템"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if new_events:
            for event in new_events[:5]:
                embed["fields"].append({
                    "name": f"📍 {event.get('name', 'N/A')}",
                    "value": f"일정: {event.get('start_date', 'N/A')}\n장소: {event.get('location', 'N/A')}",
                    "inline": False
                })
        
        if updated_count > 0:
            embed["fields"].append({
                "name": "📊 총 수집 데이터",
                "value": f"{updated_count}건 업데이트됨",
                "inline": True
            })
        
        # 전송
        discord_result = self._send_discord(embed)
        
        # Telegram 메시지
        if new_events:
            telegram_msg = "🆕 *광주 웨딩박람회 업데이트!*\n\n"
            for event in new_events[:3]:
                telegram_msg += f"📍 *{event.get('name', 'N/A')}*\n"
                telegram_msg += f"📅 {event.get('start_date', 'N/A')}\n"
                telegram_msg += f"📍 {event.get('location', 'N/A')}\n\n"
            telegram_result = self._send_telegram(telegram_msg)
            return discord_result or telegram_result
        
        return discord_result
    
    def send_error_notification(self, error_message: str) -> bool:
        """오류 알림 전송"""
        embed = {
            "title": "⚠️ 스크래핑 오류 발생",
            "description": error_message[:500],
            "color": 15548997,  # 빨강
            "footer": {"text": "웨딩박람회 스크래핑 시스템"},
            "timestamp": datetime.utcnow().isoformat()
        }
        return self._send_discord(embed)
    
    def send_success_notification(self, total_count: int, new_count: int = 0) -> bool:
        """성공 알림 전송"""
        embed = {
            "title": "✅ 스크래핑 완료",
            "description": f"📊 총 {total_count}건 수집" + (f" (신규 {new_count}건)" if new_count > 0 else ""),
            "color": 5763719,
            "footer": {"text": f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
            "timestamp": datetime.utcnow().isoformat()
        }
        return self._send_discord(embed)


if __name__ == "__main__":
    # 테스트
    notifier = NotificationService()
    test_events = [
        {
            "name": "2026 광주 웨딩쇼",
            "start_date": "2026-03-21",
            "location": "컨벤션타워 2층"
        }
    ]
    # notifier.send_wedding_expo_notification(test_events, 6)
    print("알림 모듈 테스트 완료 (설정 필요)")
