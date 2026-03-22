#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
광주광역시 웨딩박람회 자동 스크래핑 프로그램
"""

__version__ = "1.0.0"
__author__ = "Wedding Expo Scraper"

from .config import SCRAPING_SOURCES, DATA_DIR, CSV_FILENAME
from .scraper import WeddingExpoScraper
from .parser import ExpoParser
from .storage import DataStorage
from .github_sync import GitHubSync

def main():
    """메인 실행 함수"""
    import sys
    import logging
    from datetime import datetime
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🌸 광주광역시 웨딩박람회 스크래핑 시작")
    logger.info(f"⏰ 시작 시간: {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # 1. 스크래핑
        logger.info("📡 웨딩 박람회 정보 수집 중...")
        scraper = WeddingExpoScraper()
        raw_data = scraper.scrape_all()
        logger.info(f"✅ {len(raw_data)}건의 데이터 수집 완료")
        
        if not raw_data:
            logger.warning("⚠️ 수집된 데이터가 없습니다.")
            return
        
        # 2. 파싱
        logger.info("🔍 데이터 파싱 중...")
        parser = ExpoParser()
        parsed_data = parser.parse_all(raw_data)
        logger.info(f"✅ {len(parsed_data)}건의 데이터 파싱 완료")
        
        # 3. 저장
        logger.info("💾 데이터 저장 중...")
        storage = DataStorage()
        storage.save(parsed_data)
        logger.info(f"✅ 데이터 저장 완료: {CSV_FILENAME}")
        
        # 4. GitHub 동기화
        logger.info("📤 GitHub 동기화 중...")
        github = GitHubSync()
        github.sync()
        logger.info("✅ GitHub 동기화 완료")
        
        logger.info("=" * 60)
        logger.info("🎉 모든 작업 완료!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
