#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""데이터 저장 모듈 - SQLite + CSV 하이브리드"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

from .config import CSV_PATH, DB_PATH, CSV_COLUMNS, DATA_DIR


logger = logging.getLogger(__name__)


class DataStorage:
    """SQLite + CSV 기반 저장소"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.csv_path = CSV_PATH
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """데이터베이스 및 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 고유 키(hash)를 포함한 테이블 생성
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS wedding_expos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        operating_hours TEXT,
                        location TEXT,
                        organizer TEXT,
                        contact TEXT,
                        source_url TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(name, start_date, location, source_url)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"❌ DB 초기화 실패: {e}")

    def load(self) -> pd.DataFrame:
        """DB에서 데이터 로드"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM wedding_expos ORDER BY start_date ASC", conn)
                # 불필요한 컬럼 제거
                if 'id' in df.columns:
                    df = df.drop(columns=['id', 'created_at'], errors='ignore')
                return df
        except Exception as e:
            logger.warning(f"로드 실패 (DB -> DataFrame): {e}")
            return pd.DataFrame(columns=CSV_COLUMNS)
    
    def save(self, data: List[Dict]) -> bool:
        """데이터 저장 (DB 및 CSV 동시 갱신)"""
        if not data:
            return False
        
        try:
            # 1. DB에 Insert (OR IGNORE로 중복 방지)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for item in data:
                    cursor.execute('''
                        INSERT OR IGNORE INTO wedding_expos 
                        (name, start_date, end_date, operating_hours, location, organizer, contact, source_url, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('name'), item.get('start_date'), item.get('end_date'),
                        item.get('operating_hours'), item.get('location'), item.get('organizer'),
                        item.get('contact'), item.get('source_url'), item.get('description')
                    ))
                conn.commit()
            
            # 2. 최신 데이터를 CSV로 내보내기 (대시보드 호환용)
            full_df = self.load()
            full_df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ 저장 완료: DB 동기화 및 CSV 갱신 ({len(full_df)}건)")
            return True
            
        except Exception as e:
            logger.error(f"❌ 저장 실패: {e}")
            return False
    
    def get_all(self) -> List[Dict]:
        df = self.load()
        return df.to_dict('records') if not df.empty else []
