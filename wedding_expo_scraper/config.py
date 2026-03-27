#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

CSV_FILENAME = "gwangju_wedding_expos.csv"
CSV_PATH = DATA_DIR / CSV_FILENAME
DB_PATH = DATA_DIR / "wedding_expos.db"
SOURCE_HEALTH_PATH = DATA_DIR / "source_health.json"
SOURCE_HEALTH_REPORT_PATH = LOG_DIR / "latest_source_health_report.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "")
TISTORY_ACCESS_TOKEN = os.getenv("TISTORY_ACCESS_TOKEN", "")
TISTORY_BLOG_NAME = os.getenv("TISTORY_BLOG_NAME", "")
TISTORY_CATEGORY_ID = os.getenv("TISTORY_CATEGORY_ID", "")
TISTORY_TAGS = os.getenv("TISTORY_TAGS", "웨딩박람회,광주,주간업데이트")
TISTORY_VISIBILITY = int(os.getenv("TISTORY_VISIBILITY", "3"))
TISTORY_ACCEPT_COMMENT = int(os.getenv("TISTORY_ACCEPT_COMMENT", "1"))
PRODUCTION_SOURCE_MODE = os.getenv("PRODUCTION_SOURCE_MODE", "true").lower() == "true"

# ================================================================================
# 정적 스크래핑 소스 (30개+)
# ================================================================================
SCRAPING_SOURCES = [
    # ============================================================================
    # 1. 광주광역시 공식/주요 소스 (5개)
    # ============================================================================
    {"name": "더베스트웨딩", "url": "https://www.gjweddingshow.kr/", "category": "광주 공식", "region": "광주", "priority": 1},
    {"name": "광주웨딩페스타", "url": "https://gjweddingfesta.com/", "category": "광주", "region": "광주", "priority": 1},
    {"name": "광주컨벤션웨딩박람회", "url": "https://www.kjcc.co.kr/", "category": "광주", "region": "광주", "priority": 1},
    {"name": "김대중컨벤션센터", "url": "https://www.convention.kr/", "category": "광주", "region": "광주", "priority": 2},
    {"name": "광주문화컨벤션센터", "url": "https://www.gcccl.or.kr/", "category": "광주", "region": "광주", "priority": 2},

    # ============================================================================
    # 2. 전국 웨딩 박람회 통합 사이트 (6개)
    # ============================================================================
    {"name": "웨딩다모아-전체", "url": "https://weddingdamoa.com/wedding", "category": "전국", "region": "전국", "priority": 1},
    {"name": "웨딩다모아-전라도", "url": "https://weddingdamoa.com/wedding/jeolla", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "Wedding Fair Schedule", "url": "https://weddingfairschedule.kr/", "category": "전국", "region": "전국", "priority": 1},
    {"name": "Wedding Fair Schedule-서울", "url": "https://weddingfairschedule.kr/?region=seoul", "category": "서울", "region": "서울", "priority": 2},
    {"name": "Wedding Fair Schedule-경기", "url": "https://weddingfairschedule.kr/?region=gyeonggi", "category": "경기", "region": "경기", "priority": 2},
    {"name": "Wedding Fair Schedule-부산", "url": "https://weddingfairschedule.kr/?region=busan", "category": "부산", "region": "부산", "priority": 2},
    {"name": "Wedding Fair Schedule-대구", "url": "https://weddingfairschedule.kr/?region=daegu", "category": "대구", "region": "대구", "priority": 2},

    # ============================================================================
    # 3. 한국웨딩연합회 및 업권협회 (3개)
    # ============================================================================
    {"name": "한국웨딩연합회-전라도", "url": "https://keu.or.kr/region/jeolla/", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "한국웨딩전문가협회", "url": "https://www.kawpa.or.kr/", "category": "전국", "region": "전국", "priority": 2},
    {"name": "한국웨딩산업협회", "url": "https://www.krwia.or.kr/", "category": "전국", "region": "전국", "priority": 2},

    # ============================================================================
    # 4. 웨딩 포털 및 매거진 (5개)
    # ============================================================================
    {"name": "웨딩고", "url": "https://weddingo.kr/", "category": "웨딩 포털", "region": "전국", "priority": 1},
    {"name": "웨딩다이어리", "url": "https://www.weddingdiary.co.kr/", "category": "웨딩 포털", "region": "전국", "priority": 2},
    {"name": "웨딩박람회투어", "url": "https://www.weddingexpo.co.kr/", "category": "웨딩 포털", "region": "전국", "priority": 2},
    {"name": "웨딩SNS", "url": "https://weddingsns.com/", "category": "웨딩 포털", "region": "전국", "priority": 2},
    {"name": "웨딩매거진", "url": "https://www.weddingmagazine.co.kr/", "category": "웨딩 포털", "region": "전국", "priority": 2},

    # ============================================================================
    # 5. 웨딩모멘트 및 지역 특화 (4개)
    # ============================================================================
    {"name": "웨딩모멘트-전라도", "url": "https://weddingmoment.co.kr/jeolla", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "전라도웨딩박람회", "url": "https://url.kr/p/weddingfair/region/?region=jeolla", "category": "전라도", "region": "광주", "priority": 2},
    {"name": "광주전남웨딩", "url": "https://blog.naver.com/wngkf", "category": "블로그", "region": "광주", "priority": 2},
    {"name": "호남웨딩박람회", "url": "https://blog.naver.com/weddingshow", "category": "블로그", "region": "광주", "priority": 3},

    # ============================================================================
    # 6. 네이버 카페 및 커뮤니티 (4개)
    # ============================================================================
    {"name": "광주웨딩준비카페", "url": "https://cafe.naver.com/gwangjuwedding", "category": "카페", "region": "광주", "priority": 2},
    {"name": "전남대웨딩카페", "url": "https://cafe.naver.com/jnueduwedding", "category": "카페", "region": "광주", "priority": 3},
    {"name": "웨딩플래너카페", "url": "https://cafe.naver.com/weddingplanner", "category": "카페", "region": "전국", "priority": 3},
    {"name": "예비부부카페", "url": "https://cafe.naver.com/marriage", "category": "카페", "region": "전국", "priority": 3},

    # ============================================================================
    # 7. 결혼정보회사/스튜디오 (3개)
    # ============================================================================
    {"name": "더웨딩", "url": "https://www.thewedding.co.kr/", "category": "결혼정보", "region": "전국", "priority": 2},
    {"name": "예비부부wed", "url": "https://www.wed.co.kr/", "category": "결혼정보", "region": "전국", "priority": 2},
    {"name": "커플플레이스", "url": "https://www.coupleplace.co.kr/", "category": "결혼정보", "region": "전국", "priority": 3},

    # ============================================================================
    # 8. 기타 웨딩 서비스 (5개)
    # ============================================================================
    {"name": "adbell-광주", "url": "https://adbell.kr/?s=weddingshow&location=gwangju", "category": "광고", "region": "광주", "priority": 2},
    {"name": "레브웨딩", "url": "https://www.lovewed.kr/", "category": "웨딩", "region": "전국", "priority": 3},
    {"name": "다이렉트결혼준비", "url": "https://www.directwedding.co.kr/", "category": "웨딩", "region": "전국", "priority": 3},
    {"name": "하우투웨딩", "url": "https://www.howtowed.co.kr/", "category": "웨딩", "region": "전국", "priority": 3},
    {"name": "굿모닝웨딩", "url": "https://www.goodmorningwedding.co.kr/", "category": "웨딩", "region": "전국", "priority": 3},
]

# ================================================================================
# 동적 스크래핑 소스 (Playwright 필요 - JavaScript SPA)
# ================================================================================
DYNAMIC_SOURCES = [
    {"name": "웨딩다모아-전라도-Dynamic", "url": "https://weddingdamoa.com/wedding/jeolla", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "한국웨딩연합회-전라도-Dynamic", "url": "https://keu.or.kr/region/jeolla/", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "광주웨딩페스타-Dynamic", "url": "https://gjweddingfesta.com/", "category": "광주", "region": "광주", "priority": 1},
    {"name": "웨딩모멘트-전라도-Dynamic", "url": "https://weddingmoment.co.kr/jeolla", "category": "전라도", "region": "광주", "priority": 1},
    {"name": "전라도웨딩박람회-Dynamic", "url": "https://url.kr/p/weddingfair/region/?region=jeolla", "category": "전라도", "region": "광주", "priority": 2},
]

PRODUCTION_STATIC_SOURCE_NAMES = {
    "더베스트웨딩",
    "광주웨딩페스타",
    "웨딩다모아-전라도",
    "Wedding Fair Schedule",
    "한국웨딩연합회-전라도",
    "웨딩모멘트-전라도",
    "전라도웨딩박람회",
}

PRODUCTION_DYNAMIC_SOURCE_NAMES = {
    "웨딩다모아-전라도-Dynamic",
    "한국웨딩연합회-전라도-Dynamic",
    "광주웨딩페스타-Dynamic",
    "웨딩모멘트-전라도-Dynamic",
}

# ================================================================================
# API 소스 (Open API)
# ================================================================================
API_SOURCES = [
    {"name": "공공데이터포털-문화행사", "url": "https://www.data.go.kr/data/15099994/standard.do", "category": "API", "region": "전국", "priority": 1},
    {"name": "경기데이터드림-문화행사", "url": "https://data.gg.go.kr/", "category": "API", "region": "경기", "priority": 2},
    {"name": "광주광역시 Open API", "url": "https://www.gwangju.go.kr/", "category": "API", "region": "광주", "priority": 1},
    {"name": "SETEC 박람회 정보", "url": "https://www.setec.or.kr/", "category": "API", "region": "전국", "priority": 2},
    {"name": "킨텍스 박람회", "url": "https://www.kintex.com/", "category": "API", "region": "경기", "priority": 2},
]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

REQUEST_TIMEOUT = 15
REQUEST_RETRY_COUNT = 3
REQUEST_DELAY_MIN = 1
REQUEST_DELAY_MAX = 3
MAX_CONCURRENT_REQUESTS = 5
SOURCE_FAILURE_THRESHOLD = int(os.getenv("SOURCE_FAILURE_THRESHOLD", "3"))
SOURCE_COOLDOWN_HOURS = int(os.getenv("SOURCE_COOLDOWN_HOURS", "24"))
SOURCE_ZERO_RESULT_THRESHOLD = int(os.getenv("SOURCE_ZERO_RESULT_THRESHOLD", "5"))

USE_PLAYWRIGHT_FALLBACK = os.getenv("USE_PLAYWRIGHT_FALLBACK", "true").lower() == "true"
PLAYWRIGHT_WAIT_TIME = 5000

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CSV_COLUMNS = [
    "name", "start_date", "end_date", "operating_hours",
    "location", "organizer", "contact",
    "source_url", "description", "region", "source"
]

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default)

def ensure_directories():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_all_sources():
    return SCRAPING_SOURCES + DYNAMIC_SOURCES + API_SOURCES

def get_static_sources(region_filter: tuple[str, ...] = ("광주", "전국")):
    return [s for s in SCRAPING_SOURCES if s.get("region") in region_filter]

def get_dynamic_sources(region_filter: tuple[str, ...] = ("광주", "전국")):
    return [s for s in DYNAMIC_SOURCES if s.get("region") in region_filter]

def get_api_sources(region_filter: tuple[str, ...] = ("광주", "전국")):
    return [s for s in API_SOURCES if s.get("region") in region_filter]

def get_gwangju_sources():
    return get_static_sources() + get_dynamic_sources() + get_api_sources()

def get_production_static_sources():
    sources = get_static_sources()
    return [source for source in sources if source["name"] in PRODUCTION_STATIC_SOURCE_NAMES]

def get_production_dynamic_sources():
    sources = get_dynamic_sources()
    return [source for source in sources if source["name"] in PRODUCTION_DYNAMIC_SOURCE_NAMES]

def get_priority_sources():
    sources = get_production_static_sources() if PRODUCTION_SOURCE_MODE else get_static_sources()
    return sorted(sources, key=lambda x: x.get("priority", 99))
