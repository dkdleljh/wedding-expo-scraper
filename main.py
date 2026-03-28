#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화 웨딩박람회 스크래핑 - 메인 진입점
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from wedding_expo_scraper.config import (
    ensure_directories,
    LOG_DIR,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    get_priority_sources,
    get_dynamic_sources,
    get_production_dynamic_sources,
    PRODUCTION_SOURCE_MODE,
)
from wedding_expo_scraper.scraper import WeddingExpoScraper
from wedding_expo_scraper.dynamic_scraper import DynamicScraper
from wedding_expo_scraper.parser import ExpoParser
from wedding_expo_scraper.storage import DataStorage
from wedding_expo_scraper.github_sync import GitHubSync
from wedding_expo_scraper.notification import NotificationService
from wedding_expo_scraper.tistory_post import TistoryPoster
from wedding_expo_scraper.source_health import SourceHealthManager
from wedding_expo_scraper.coverage_audit import CoverageAuditor


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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="광주 웨딩박람회 스크래퍼")
    parser.add_argument("--dry-run", action="store_true", help="저장/배포 없이 수집과 정규화만 실행")
    parser.add_argument("--skip-github", action="store_true", help="GitHub 동기화 건너뜀")
    parser.add_argument("--skip-tistory", action="store_true", help="티스토리 포스팅 건너뜀")
    parser.add_argument("--skip-notify", action="store_true", help="알림 전송 건너뜀")
    parser.add_argument("--ignore-health", action="store_true", help="서킷 브레이커를 무시하고 모든 활성 소스를 실행")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    ensure_directories()
    logger = setup_logging()
    
    priority_sources = get_priority_sources()
    dynamic_sources = get_production_dynamic_sources() if PRODUCTION_SOURCE_MODE else get_dynamic_sources()
    health_manager = SourceHealthManager()

    if not args.ignore_health:
        static_decision = health_manager.filter_sources(priority_sources)
        dynamic_decision = health_manager.filter_sources(dynamic_sources)
        priority_sources = static_decision.enabled_sources
        dynamic_sources = dynamic_decision.enabled_sources
        skipped_sources = static_decision.skipped_sources + dynamic_decision.skipped_sources
    else:
        skipped_sources = []
    
    error_count = 0
    success_count = 0
    
    logger.info("=" * 70)
    logger.info("🌸 고도화 웨딩박람회 스크래핑 시작")
    logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"⚙️ 프로덕션 소스 모드: {'ON' if PRODUCTION_SOURCE_MODE else 'OFF'}")
    logger.info(f"📌 정적 소스 {len(priority_sources)}개 / 동적 소스 {len(dynamic_sources)}개")
    if skipped_sources:
        logger.info(f"🛑 서킷 브레이커로 제외된 소스 {len(skipped_sources)}개")
    logger.info("=" * 70)
    
    run_stats = {}

    try:
        # 1. 수집
        logger.info("[1/6] 📡 정적 소스 병렬 스크래핑 중...")
        scraper = WeddingExpoScraper(sources=priority_sources)
        raw_data = scraper.scrape_all()
        success_count += len(raw_data)
        run_stats = scraper.get_last_run_stats()
        
        logger.info("       📡 동적 소스 스크래핑 중...")
        try:
            dynamic_scraper = DynamicScraper(sources=dynamic_sources)
            dynamic_data = dynamic_scraper.scrape_all()
            run_stats.update(dynamic_scraper.get_last_run_stats())
            if dynamic_data:
                raw_data.extend(dynamic_data)
                success_count += len(dynamic_data)
        except Exception as e:
            error_count += 1
            logger.warning(f"       ⚠️ 동적 스크래핑 실패: {e}")
            run_stats = run_stats if 'run_stats' in locals() else {}

        if not raw_data:
            logger.warning("⚠️ 수집된 데이터가 없습니다.")
            health_manager.update_from_run_stats(run_stats)
            health_manager.save()
            health_report = health_manager.build_report(
                run_stats,
                skipped_sources,
                summary={
                    "raw_count": 0,
                    "parsed_count": 0,
                    "final_valid_count": 0,
                },
            )
            health_manager.save_report(health_report)
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

        coverage_audit = CoverageAuditor().audit(merged_data)
        if coverage_audit.get('coverage_missing_count', 0):
            logger.warning("       ⚠️ 레퍼런스 대비 누락 행사 %s건: %s", coverage_audit['coverage_missing_count'], json.dumps(coverage_audit['coverage_missing_expos'], ensure_ascii=False))

        health_manager.update_from_run_stats(run_stats)
        health_manager.save()
        health_report = health_manager.build_report(
            run_stats,
            skipped_sources,
            summary={
                "raw_count": len(raw_data),
                "parsed_count": len(parsed_data),
                "final_valid_count": len(merged_data),
                **coverage_audit,
            },
        )
        health_manager.save_report(health_report)
        logger.info("       🩺 헬스 요약: %s", json.dumps(health_report, ensure_ascii=False))
        
        # 3. 저장
        logger.info("[3/6] 💾 저장 중 (SQLite & CSV)...")
        if args.dry_run:
            logger.info("       ⏭️ dry-run: 저장 생략")
        else:
            storage.save(merged_data)
        
        # 4. GitHub 동기화
        logger.info("[4/6] 📤 GitHub 동기화...")
        if args.dry_run or args.skip_github:
            logger.info("       ⏭️ dry-run/옵션으로 건너뜀")
        else:
            github = GitHubSync()
            if github.is_git_repo():
                github.add_all()
                if github.has_changes():
                    github.sync()
                    logger.info("       ✅ 동기화 완료")
                else:
                    logger.info("       ⏭️ 변경 없음")
        
        # 5. 티스토리 포스팅
        logger.info("[5/6] 📝 티스토리 블로그 포스팅...")
        if args.dry_run or args.skip_tistory:
            logger.info("       ⏭️ dry-run/옵션으로 건너뜀")
        else:
            try:
                poster = TistoryPoster()
                if poster.is_configured() and merged_data:
                    if datetime.now().weekday() in [0, 3] or len(parsed_data) >= 5:
                        if poster.post_update(merged_data):
                            logger.info("       ✅ 티스토리 포스팅 성공")
                else:
                    logger.info("       ⏭️ 설정 미비 또는 데이터 부족으로 건너뜀")
            except Exception as e:
                logger.warning(f"       ⚠️ 티스토리 작업 중 오류: {e}")

        # 6. 알림 전송
        logger.info("[6/6] 🔔 알림 및 리포트 전송...")
        if args.dry_run or args.skip_notify:
            logger.info("       ⏭️ dry-run/옵션으로 건너뜀")
        else:
            notifier = NotificationService()
            notifier.send_success_notification(len(merged_data), len(parsed_data))
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
