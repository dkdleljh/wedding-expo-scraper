#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화 웨딩박람회 스크래핑 - 메인 진입점
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from wedding_expo_scraper.config import ensure_directories, LOG_DIR, LOG_FORMAT, LOG_DATE_FORMAT, get_gwangju_sources, get_priority_sources, DYNAMIC_SOURCES
from wedding_expo_scraper.scraper import WeddingExpoScraper
from wedding_expo_scraper.dynamic_scraper import DynamicScraper
from wedding_expo_scraper.parser import ExpoParser
from wedding_expo_scraper.storage import DataStorage
from wedding_expo_scraper.github_sync import GitHubSync
from wedding_expo_scraper.notification import NotificationService
from wedding_expo_scraper.tistory_post import TistoryPoster


class SensitiveDataFilter(logging.Filter):
    """로그 내 민감 정보 필터링"""
    def filter(self, record):
        from wedding_expo_scraper.config import GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, TISTORY_ACCESS_TOKEN
        if isinstance(record.msg, str):
            for token in [GITHUB_TOKEN, TELEGRAM_BOT_TOKEN, TISTORY_ACCESS_TOKEN]:
                if token and len(token) > 5 and token in record.msg:
                    record.msg = record.msg.replace(token, "***REDACTED***")
        return True

def setup_logging():
    log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    file_handler = logging.FileHandler(log_file)
    stream_handler = logging.StreamHandler(sys.stdout)
    
    sensitive_filter = SensitiveDataFilter()
    file_handler.addFilter(sensitive_filter)
    stream_handler.addFilter(sensitive_filter)
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[file_handler, stream_handler]
    )
    
    return logging.getLogger(__name__)


def main():
    ensure_directories()
    logger = setup_logging()
    
    priority_sources = get_priority_sources()
    
    error_count = 0
    success_count = 0
    
    logger.info("=" * 70)
    logger.info("🌸 고도화 웨딩박람회 스크래핑 시작")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # 1. 수집
        logger.info("[1/6] 📡 병렬 스크래핑 중...")
        scraper = WeddingExpoScraper(sources=priority_sources)
        raw_data = scraper.scrape_all()
        success_count += len(raw_data)
        
        logger.info("       📡 동적 페이지 스크래핑 중...")
        try:
            dynamic_scraper = DynamicScraper(sources=DYNAMIC_SOURCES)
            dynamic_data = dynamic_scraper.scrape_all()
            if dynamic_data:
                raw_data.extend(dynamic_data)
                success_count += len(dynamic_data)
        except Exception as e:
            error_count += 1
            logger.warning(f"       ⚠️ 동적 스크래핑 실패: {e}")
        
        if not raw_data:
            logger.warning("⚠️ 수집된 데이터가 없습니다.")
            return 0
        
        # 2. 정규화
        logger.info("[2/6] 🔍 데이터 정규화 및 보안 처리...")
        parser = ExpoParser()
        parsed_data = parser.parse_all(raw_data)
        
        storage = DataStorage()
        merged_data = parser.filter_valid_records(parsed_data)
        if not merged_data:
            logger.info("       ⚠️ 신규 유효 데이터가 없어 기존 데이터 로드")
            merged_data = storage.get_all()
        
        # 3. 저장
        logger.info("[3/6] 💾 저장 중 (SQLite & CSV)...")
        storage.save(merged_data)
        
        # 4. GitHub 동기화
        logger.info("[4/6] 📤 GitHub 동기화...")
        github = GitHubSync()
        if github.is_git_repo():
            github.add_all() # 변경사항 스테이징
            if github.has_changes():
                github.sync()
                logger.info("       ✅ 동기화 완료")
            else:
                logger.info("       ⏭️ 변경 없음")
        
        # 5. 티스토리 포스팅
        logger.info("[5/6] 📝 티스토리 블로그 포스팅...")
        try:
            poster = TistoryPoster()
            if poster.is_configured() and merged_data:
                # 월/목 주기 또는 신규 데이터 대량 발생 시 포스팅
                if datetime.now().weekday() in [0, 3] or len(parsed_data) >= 5:
                    if poster.post_update(merged_data):
                        logger.info("       ✅ 티스토리 포스팅 성공")
            else:
                logger.info("       ⏭️ 설정 미비 또는 데이터 부족으로 건너뜀")
        except Exception as e:
            logger.warning(f"       ⚠️ 티스토리 작업 중 오류: {e}")

        # 6. 알림 전송
        logger.info("[6/6] 🔔 알림 및 리포트 전송...")
        notifier = NotificationService()
        notifier.send_success_notification(len(merged_data))
        notifier.send_daily_summary({
            "total": len(merged_data),
            "new": len(parsed_data),
            "errors": error_count
        })
        
        logger.info("=" * 70)
        logger.info(f"🎉 모든 작업 완료! (수집: {success_count}건, 최종저장: {len(merged_data)}건)")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 치명적 오류: {e}", exc_info=True)
        try:
            notifier = NotificationService()
            notifier.send_error_notification(str(e))
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
