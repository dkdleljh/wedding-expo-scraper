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

from wedding_expo_scraper.config import ensure_directories, LOG_DIR, LOG_FORMAT, LOG_DATE_FORMAT, get_gwangju_sources, get_priority_sources
from wedding_expo_scraper.scraper import WeddingExpoScraper
from wedding_expo_scraper.dynamic_scraper import DynamicScraper
from wedding_expo_scraper.parser import ExpoParser
from wedding_expo_scraper.storage import DataStorage
from wedding_expo_scraper.github_sync import GitHubSync
from wedding_expo_scraper.notification import NotificationService


def setup_logging():
    log_file = LOG_DIR / f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    ensure_directories()
    logger = setup_logging()
    
    priority_sources = get_priority_sources()
    gwangju_sources = get_gwangju_sources()
    
    error_count = 0
    success_count = 0
    
    logger.info("=" * 70)
    logger.info("🌸 고도화 웨딩박람회 스크래핑 시작")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"📊 우선순위 소스: {len(priority_sources)}개")
    logger.info(f"📊 광주 관련 소스: {len(gwangju_sources)}개")
    logger.info("=" * 70)
    
    try:
        logger.info("[1/6] 📡 병렬 스크래핑 중...")
        scraper = WeddingExpoScraper(sources=priority_sources)
        raw_data = scraper.scrape_all()
        success_count += len(raw_data)
        logger.info(f"       ✅ {len(raw_data)}건 수집 (정적)")
        
        logger.info("       📡 동적 페이지 스크래핑 중...")
        try:
            dynamic_scraper = DynamicScraper()
            dynamic_data = dynamic_scraper.scrape_all()
            if dynamic_data:
                raw_data.extend(dynamic_data)
                success_count += len(dynamic_data)
                logger.info(f"       ✅ {len(dynamic_data)}건 추가 수집 (동적)")
        except Exception as e:
            error_count += 1
            logger.warning(f"       ⚠️ 동적 스크래핑 실패: {e}")
        
        if not raw_data:
            logger.warning("⚠️ 데이터 없음")
            notifier = NotificationService()
            notifier.send_error_notification("데이터 수집 실패: 소스 응답 없음")
            return 0
        
        # 2. 정규화
        logger.info("[2/6] 🔍 데이터 정규화...")
        parser = ExpoParser()
        parsed_data = parser.parse_all(raw_data)
        logger.info(f"       ✅ {len(parsed_data)}건 처리")
        
        # 3. 저장
        logger.info("[3/6] 💾 저장 중...")
        storage = DataStorage()
        storage.save(parsed_data)
        
        # 4. GitHub 동기화
        logger.info("[4/6] 📤 GitHub 동기화...")
        github = GitHubSync()
        if github.is_git_repo():
            if github.has_changes():
                github.sync()
                logger.info("       ✅ 동기화 완료")
            else:
                logger.info("       ⏭️ 변경 없음")
        
        # 5. 알림 전송
        logger.info("[5/6] 🔔 알림 전송...")
        notifier = NotificationService()
        notifier.send_success_notification(len(parsed_data))
        
        # 6. 일일 리포트
        logger.info("[6/6] 📊 일일 리포트...")
        notifier.send_daily_summary({
            "total": len(parsed_data),
            "new": len(parsed_data),
            "errors": error_count
        })
        
        logger.info("=" * 70)
        logger.info(f"🎉 완료! (수집: {success_count}건, 오류: {error_count}건)")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 오류: {e}", exc_info=True)
        try:
            notifier = NotificationService()
            notifier.send_error_notification(str(e))
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
