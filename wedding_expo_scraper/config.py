#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 모듈 - 프로그램 전역 설정 관리 (고도화 버전)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILENAME = "gwangju_wedding_expos.csv"
CSV_PATH = DATA_DIR / CSV_FILENAME

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "")

# ================================================================================
# 고도화된 스크래핑 소스 (광주 + 전국 주요 도시)
# ================================================================================
SCRAPING_SOURCES = [
    # ============================================================================
    # 광주광역시 소스 (최우선)
    # ============================================================================
    {"name": "더베스트웨딩", "url": "https://www.gjweddingshow.kr/", "category": "광주 공식", "region": "광주"},
    
    # ============================================================================
    # 신규 소스 1: weddingdamoa.com (전라도/광주 지역)
    # ============================================================================
    {"name": "웨딩다모아-전라도", "url": "https://weddingdamoa.com/wedding/jeolla", "category": "전라도", "region": "광주"},
    {"name": "웨딩다모아-전체", "url": "https://weddingdamoa.com/wedding", "category": "전체", "region": "전국"},
    
    # ============================================================================
    # 신규 소스 2: keu.or.kr (한국웨딩연합회)
    # ============================================================================
    {"name": "한국웨딩연합회-전라도", "url": "https://keu.or.kr/region/jeolla/", "category": "전라도", "region": "광주"},
    
    # ============================================================================
    # 기존 소스 (광주 관련)
    # ============================================================================
    {"name": "Wedding Fair Schedule", "url": "https://weddingfairschedule.kr/", "category": "전체 일정", "region": "전국"},
    {"name": "웨딩고", "url": "https://weddingo.kr/", "category": "웨딩 포털", "region": "전국"},
    
    # ============================================================================
    # 기타 지역 소스 (참고용)
    # ============================================================================
    {"name": "서울웨딩박람회", "url": "https://weddingfairschedule.kr/", "category": "서울", "region": "서울"},
    {"name": "경기웨딩박람회", "url": "https://weddingfairschedule.kr/", "category": "경기", "region": "경기"},
    {"name": "부산웨딩박람회", "url": "https://weddingfairschedule.kr/", "category": "부산", "region": "부산"},
]

# ================================================================================
# 알림 설정
# ================================================================================
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ================================================================================
# 스크래핑 설정
# ================================================================================
REQUEST_TIMEOUT = 30
REQUEST_RETRY_COUNT = 3
REQUEST_DELAY_MIN = 1
REQUEST_DELAY_MAX = 3
MAX_CONCURRENT_REQUESTS = 5

# ================================================================================
# Playwright 동적 페이지 설정
# ================================================================================
USE_PLAYWRIGHT_FALLBACK = os.getenv("USE_PLAYWRIGHT_FALLBACK", "true").lower() == "true"
PLAYWRIGHT_WAIT_TIME = 5000  # ms

# 동적 페이지 소스 (JavaScript 렌더링 필요)
DYNAMIC_SOURCES = [
    # {"name": "동적 페이지 예시", "url": "https://example.com", "wait_selector": ".content"},
]

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CSV_COLUMNS = ["name", "start_date", "end_date", "location", "organizer", "source_url", "scraped_at", "region"]

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def ensure_directories():
    """필요한 디렉토리 생성"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
