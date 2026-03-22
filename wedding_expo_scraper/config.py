#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 모듈 - 프로그램 전역 설정 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# ================================================================================
# 프로젝트 경로 설정
# ================================================================================

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 데이터 디렉토리
DATA_DIR = PROJECT_ROOT / "data"

# 로그 디렉토리
LOG_DIR = DATA_DIR / "logs"

# ================================================================================
# 데이터 파일 설정
# ================================================================================

CSV_FILENAME = "gwangju_wedding_expos.csv"
CSV_PATH = DATA_DIR / CSV_FILENAME

# ================================================================================
# GitHub 설정
# ================================================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "")

# ================================================================================
# 웹 스크래핑 소스 설정
# ================================================================================

SCRAPING_SOURCES = [
    {
        "name": "Wedding Fair Schedule",
        "url": "https://weddingfairschedule.kr/",
        "category": "전체 웨딩 박람회 일정"
    },
    {
        "name": "웨딩고",
        "url": "https://weddingo.kr/",
        "category": "웨딩 정보 포털"
    },
    {
        "name": "더베스트웨딩",
        "url": "https://www.gjweddingshow.kr/",
        "category": "광주 웨딩박람회 공식"
    }
]

# ================================================================================
# 스크래핑 설정
# ================================================================================

# HTTP 요청 설정
REQUEST_TIMEOUT = 30  # 초
REQUEST_RETRY_COUNT = 3  # 재시도 횟수
REQUEST_DELAY_MIN = 2  # 최소 요청 간 딜레이 (초)
REQUEST_DELAY_MAX = 5  # 최대 요청 간 딜레이 (초)

# User-Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ================================================================================
# 데이터 필드 설정
# ================================================================================

CSV_COLUMNS = [
    "name",           # 박람회명
    "start_date",     # 시작일
    "end_date",       # 종료일
    "location",       # 장소
    "organizer",      # 주관사
    "source_url",     # 출처 URL
    "scraped_at"      # 스크래핑 일시
]

# ================================================================================
# 로그 설정
# ================================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ================================================================================
# 유틸리티 함수
# ================================================================================

def ensure_directories():
    """필요한 디렉토리 생성"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_env(key: str, default: str = "") -> str:
    """환경 변수 가져오기"""
    return os.getenv(key, default)
