#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
광주광역시 웨딩박람회 자동 스크래핑 - 메인 진입점
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


def setup_logging():
    """로깅 설정"""
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
    """메인 실행"""
    ensure_directories()
    logger = setup_logging()
    
    logger.info("=" * 70)
    logger.info("🌸 광주광역시 웨딩박람회 자동 스크래핑 프로그램")
    logger.info(f"⏰ 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        logger.info("[1/4] 📡 웨딩 박람회 정보 수집 중...")
        scraper = WeddingExpoScraper()
        raw_data = scraper.scrape_all()
        logger.info(f"       ✅ {len(raw_data)}건 수집 완료")
        
        logger.info("[2/4] 🔍 데이터 파싱 및 정규화 중...")
        parser = ExpoParser()
        parsed_data = parser.parse_all(raw_data)
        logger.info(f"       ✅ {len(parsed_data)}건 처리 완료")
        
        if parsed_data:
            logger.info("[3/4] 💾 CSV 파일 저장 중...")
            storage = DataStorage()
            storage.save(parsed_data)
            logger.info(f"       ✅ 저장 완료")
        else:
            logger.info("[3/4] 💾 저장 건너뜀 (데이터 없음)")
        
        logger.info("[4/4] 📤 GitHub 동기화 중...")
        github = GitHubSync()
        
        if github.is_git_repo():
            if github.has_changes():
                github.sync()
                logger.info("       ✅ 동기화 완료")
            else:
                logger.info("       ⏭️ 변경 사항 없음 - 건너뜀")
        else:
            logger.warning("       ⚠️ Git 저장소가 아닙니다 - GitHub 설정을 확인하세요")
        
        logger.info("=" * 70)
        logger.info("🎉 모든 작업이 완료되었습니다!")
        logger.info(f"📁 데이터 파일: data/gwangju_wedding_expos.csv")
        logger.info(f"📁 로그 파일: data/logs/")
        logger.info("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 사용자에 의해 중단됨")
        return 1
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
