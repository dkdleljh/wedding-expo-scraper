#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""데이터 저장 모듈"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

from .config import CSV_PATH, CSV_COLUMNS, DATA_DIR


logger = logging.getLogger(__name__)


class DataStorage:
    """CSV 저장"""
    
    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or CSV_PATH
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
    def load(self) -> pd.DataFrame:
        if not self.filepath.exists():
            return pd.DataFrame(columns=CSV_COLUMNS)
        try:
            df = pd.read_csv(self.filepath, encoding='utf-8-sig')
            return df
        except Exception as e:
            logger.warning(f"로드 실패: {e}")
            return pd.DataFrame(columns=CSV_COLUMNS)
    
    def save(self, data: List[Dict]) -> bool:
        if not data:
            return False
        
        try:
            existing_df = self.load()
            new_df = pd.DataFrame(data)
            
            # 열 순서 맞추기
            available_cols = [col for col in CSV_COLUMNS if col in new_df.columns]
            new_df = new_df[available_cols]
            
            # 병합 및 중복 제거
            if not existing_df.empty:
                existing_names = set(existing_df['name'].str.lower())
                unique_existing = existing_df[~existing_df['name'].str.lower().isin(new_df['name'].str.lower())]
                combined_df = pd.concat([new_df, unique_existing], ignore_index=True)
            else:
                combined_df = new_df
            
            # 정렬
            combined_df = combined_df.sort_values(by=['start_date', 'name'], ascending=[True, True]).reset_index(drop=True)
            
            # 저장
            combined_df.to_csv(self.filepath, index=False, encoding='utf-8-sig')
            logger.info(f"✅ 저장 완료: {len(combined_df)}건")
            return True
            
        except Exception as e:
            logger.error(f"❌ 저장 실패: {e}")
            return False
    
    def get_all(self) -> List[Dict]:
        df = self.load()
        return df.to_dict('records') if not df.empty else []
