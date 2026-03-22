#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 대시보드 - 웨딩박람회 데이터 시각화
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="광주 웨딩박람회 대시보드",
    page_icon="🌸",
    layout="wide"
)

# 데이터 로드
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent.parent / "data" / "gwangju_wedding_expos.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        return df
    return pd.DataFrame()

# 메인 타이틀
st.title("🌸 광주광역시 웨딩박람회 대시보드")
st.markdown(f"**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 데이터 로드
df = load_data()

if df.empty:
    st.warning("데이터가 없습니다. 스크래핑을 실행해주세요.")
else:
    # 메트릭 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 박람회 수", len(df))
    
    with col2:
        unique_locations = df['location'].nunique()
        st.metric("개최 장소 수", unique_locations)
    
    with col3:
        if 'start_date' in df.columns:
            upcoming = df[df['start_date'] >= datetime.now().strftime('%Y-%m-%d')]
            st.metric("다가오는 일정", len(upcoming))
    
    st.divider()
    
    # 필터
    st.subheader("🔍 필터")
    col1, col2 = st.columns(2)
    
    with col1:
        search = st.text_input("박람회명 검색")
    
    with col2:
        if 'region' in df.columns:
            regions = ["전체"] + df['region'].dropna().unique().tolist()
            selected_region = st.selectbox("지역", regions)
        else:
            selected_region = "전체"
    
    # 필터 적용
    filtered_df = df.copy()
    
    if search:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search, na=False)]
    
    if selected_region != "전체" and 'region' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    # 데이터 테이블
    st.subheader(f"📋 전체 일정 ({len(filtered_df)}건)")
    
    display_cols = ['name', 'start_date', 'end_date', 'location']
    if 'organizer' in filtered_df.columns:
        display_cols.append('organizer')
    if 'region' in filtered_df.columns:
        display_cols.append('region')
    
    available_cols = [col for col in display_cols if col in filtered_df.columns]
    st.dataframe(
        filtered_df[available_cols],
        use_container_width=True,
        hide_index=True
    )
    
    # 상세 정보
    st.divider()
    st.subheader("📍 장소별 분포")
    
    if 'location' in df.columns:
        location_counts = df['location'].value_counts().head(10)
        st.bar_chart(location_counts)
    
    # 다운로드
    st.divider()
    csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv,
        file_name=f"wedding_expos_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# 사이드바
st.sidebar.header("ℹ️ 정보")
st.sidebar.info("""
**광주광역시 웨딩박람회 자동 수집 시스템**

- 데이터 소스: weddingfairschedule.kr
- 자동 업데이트: 매일 새벽 6:00
- GitHub: dkdleljh/wedding-expo-scraper
""")
