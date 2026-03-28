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
                cursor.execute(
                    '''
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
                        region TEXT DEFAULT '광주',
                        source TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(name, start_date, location, source_url)
                    )
                    '''
                )
                self._ensure_columns(cursor)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ DB 초기화 실패: {e}")

    def _ensure_columns(self, cursor: sqlite3.Cursor):
        cursor.execute("PRAGMA table_info(wedding_expos)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            "region": "ALTER TABLE wedding_expos ADD COLUMN region TEXT DEFAULT '광주'",
            "source": "ALTER TABLE wedding_expos ADD COLUMN source TEXT DEFAULT ''",
            "updated_at": "ALTER TABLE wedding_expos ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }
        for column, ddl in required_columns.items():
            if column not in existing_columns:
                cursor.execute(ddl)

    def load(self) -> pd.DataFrame:
        """DB에서 데이터 로드"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM wedding_expos ORDER BY start_date ASC, name ASC", conn)
                # 불필요한 컬럼 제거
                if 'id' in df.columns:
                    df = df.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore')
                for column in CSV_COLUMNS:
                    if column not in df.columns:
                        df[column] = ""
                df = df[CSV_COLUMNS]
                return df
        except Exception as e:
            logger.warning(f"로드 실패 (DB -> DataFrame): {e}")
            return pd.DataFrame(columns=CSV_COLUMNS)
    
    def save(self, data: List[Dict]) -> bool:
        """데이터 저장 (DB 및 CSV 동시 갱신)"""
        if not data:
            return False
        
        try:
            # 1. canonical 최종 결과를 스냅샷 방식으로 저장
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM wedding_expos')
                for item in data:
                    cursor.execute('''
                        INSERT INTO wedding_expos 
                        (name, start_date, end_date, operating_hours, location, organizer, contact, source_url, description, region, source, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        item.get('name'), item.get('start_date'), item.get('end_date'),
                        item.get('operating_hours'), item.get('location'), item.get('organizer'),
                        item.get('contact'), item.get('source_url'), item.get('description'),
                        item.get('region', '광주'), item.get('source', '')
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
