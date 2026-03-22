#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 저장 모듈 - CSV 파일 관리
"""

import os
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import pandas as pd

from .config import CSV_PATH, CSV_COLUMNS, DATA_DIR


logger = logging.getLogger(__name__)


class DataStorage:
    """데이터 저장 클래스"""
    
    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or CSV_PATH
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """데이터 디렉토리 생성"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    def _create_csv_template(self):
        """CSV 파일 템플릿 생성"""
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(self.filepath, index=False, encoding='utf-8-sig')
        logger.info(f"✅ CSV 템플릿 생성: {self.filepath}")
        
    def load(self) -> pd.DataFrame:
        """기존 데이터 로드"""
        if not self.filepath.exists():
            logger.info("기존 데이터 없음 - 새 파일 생성")
            self._create_csv_template()
            return pd.DataFrame(columns=CSV_COLUMNS)
        
        try:
            df = pd.read_csv(self.filepath, encoding='utf-8-sig')
            logger.info(f"✅ 데이터 로드: {len(df)}건")
            return df
        except Exception as e:
            logger.warning(f"데이터 로드 실패: {e} - 새 파일 생성")
            self._create_csv_template()
            return pd.DataFrame(columns=CSV_COLUMNS)
    
    def save(self, data: List[Dict]) -> bool:
        """데이터 저장"""
        if not data:
            logger.warning("저장할 데이터가 없습니다.")
            return False
        
        try:
            # 기존 데이터 로드
            existing_df = self.load()
            
            # 새 데이터 DataFrame 변환
            new_df = pd.DataFrame(data)
            
            # 열 순서 맞추기
            new_df = new_df[CSV_COLUMNS]
            
            # 기존 데이터와 병합 (중복 제거: 이름 기준)
            if not existing_df.empty:
                # 기존 데이터에서 새 데이터에 없는 항목만 유지
                existing_names = set(existing_df['name'].str.lower())
                unique_existing = existing_df[
                    ~existing_df['name'].str.lower().isin(new_df['name'].str.lower())
                ]
                combined_df = pd.concat([new_df, unique_existing], ignore_index=True)
            else:
                combined_df = new_df
            
            # 날짜순 정렬
            combined_df = combined_df.sort_values(
                by=['start_date', 'name'],
                ascending=[True, True]
            ).reset_index(drop=True)
            
            # CSV 저장
            combined_df.to_csv(self.filepath, index=False, encoding='utf-8-sig')
            
            logger.info(f"✅ 데이터 저장 완료: {len(combined_df)}건")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터 저장 실패: {e}", exc_info=True)
            return False
    
    def get_all(self) -> List[Dict]:
        """모든 데이터 반환"""
        df = self.load()
        if df.empty:
            return []
        return df.to_dict('records')
    
    def get_upcoming(self, days: int = 30) -> List[Dict]:
        """향후 일정 반환"""
        df = self.load()
        if df.empty:
            return []
        
        today = datetime.now().strftime('%Y-%m-%d')
        future_date = (datetime.now() + pd.Timedelta(days=days)).strftime('%Y-%m-%d')
        
        upcoming = df[
            (df['start_date'] >= today) & 
            (df['start_date'] <= future_date)
        ]
        
        return upcoming.to_dict('records')
    
    def backup(self) -> Optional[Path]:
        """데이터 백업"""
        if not self.filepath.exists():
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = DATA_DIR / f"backup_{timestamp}.csv"
        
        try:
            import shutil
            shutil.copy2(self.filepath, backup_path)
            logger.info(f"✅ 백업 완료: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ 백업 실패: {e}")
            return None
    
    def clear_old_backups(self, keep_days: int = 7):
        """오래된 백업 파일 삭제"""
        backup_dir = DATA_DIR
        
        if not backup_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        for file in backup_dir.glob("backup_*.csv"):
            if file.stat().st_mtime < cutoff_time:
                try:
                    file.unlink()
                    logger.info(f"🗑️ 백업 삭제: {file.name}")
                except Exception as e:
                    logger.warning(f"백업 삭제 실패: {e}")


if __name__ == "__main__":
    # 테스트
    storage = DataStorage()
    
    # 샘플 데이터
    test_data = [
        {
            'name': '광주 웨딩 박람회',
            'start_date': '2026-03-21',
            'end_date': '2026-03-22',
            'location': '김대중컨벤션센터',
            'organizer': '',
            'source_url': 'https://example.com',
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    # 저장 테스트
    storage.save(test_data)
    
    # 로드 테스트
    data = storage.get_all()
    print(f"\n저장된 데이터: {len(data)}건")
    for d in data:
        print(f"  - {d['name']} ({d['start_date']} ~ {d['end_date']})")
