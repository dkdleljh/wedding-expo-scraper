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

from wedding_expo_scraper.config import ensure_directories, LOG_DIR, LOG_FORMAT, LOG_DATE_FORMAT
from wedding_expo_scraper.scraper import WeddingExpoScraper
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
    
    logger.info("=" * 70)
    logger.info("🌸 고도화 웨딩박람회 스크래핑 시작")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        # 1. 병렬 스크래핑
        logger.info("[1/5] 📡 병렬 스크래핑 중...")
        scraper = WeddingExpoScraper()
        raw_data = scraper.scrape_all()
        logger.info(f"       ✅ {len(raw_data)}건 수집")
        
        if not raw_data:
            logger.warning("⚠️ 데이터 없음")
            return 0
        
        # 2. 정규화
        logger.info("[2/5] 🔍 데이터 정규화...")
        parser = ExpoParser()
        parsed_data = parser.parse_all(raw_data)
        logger.info(f"       ✅ {len(parsed_data)}건 처리")
        
        # 3. 저장
        logger.info("[3/5] 💾 저장 중...")
        storage = DataStorage()
        storage.save(parsed_data)
        
        # 4. GitHub 동기화
        logger.info("[4/5] 📤 GitHub 동기화...")
        github = GitHubSync()
        if github.is_git_repo():
            if github.has_changes():
                github.sync()
                logger.info("       ✅ 동기화 완료")
            else:
                logger.info("       ⏭️ 변경 없음")
        
        # 5. 알림
        logger.info("[5/5] 🔔 알림 전송...")
        notifier = NotificationService()
        notifier.send_success_notification(len(parsed_data))
        
        logger.info("=" * 70)
        logger.info("🎉 완료!")
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
