#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="광주 웨딩박람회 대시보드",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "data" / "gwangju_wedding_expos.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        if 'region' not in df.columns:
            df['region'] = '광주'
        if 'source' not in df.columns:
            df['source'] = ''
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
        df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
        return df
    return pd.DataFrame()


@st.cache_data
def load_source_health():
    report_path = Path(__file__).parent / "data" / "logs" / "latest_source_health_report.json"
    state_path = Path(__file__).parent / "data" / "source_health.json"

    report = {}
    state = {}

    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            report = {}

    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    return report, state

st.title("🌸 광주광역시 웨딩박람회 대시보드")

df = load_data()
health_report, health_state = load_source_health()

if df.empty:
    st.warning("데이터가 없습니다. 스크래핑을 실행해주세요.")
    st.stop()

col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)

with col_stats1:
    st.metric("총 박람회", len(df))

with col_stats2:
    unique_locs = df['location'].nunique()
    st.metric("개최 장소", unique_locs)

with col_stats3:
    today = datetime.now()
    upcoming = df[df['start_date'] >= today]
    st.metric("다가오는 일정", len(upcoming))

with col_stats4:
    this_month = df[(df['start_date'].dt.month == today.month) & (df['start_date'].dt.year == today.year)]
    st.metric(f"{today.month}월 일정", len(this_month))

st.divider()

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    today_date = today.date()
    date_range = st.date_input(
        "📅 날짜 범위",
        value=(today_date, (today + timedelta(days=30)).date()),
        min_value=(today - timedelta(days=365)).date(),
        max_value=(today + timedelta(days=365)).date()
    )

with col_filter2:
    search = st.text_input("🔍 검색", placeholder="박람회명 검색...")

with col_filter3:
    regions = ["전체"] + sorted(df['region'].dropna().unique().tolist())
    selected_region = st.selectbox("🌏 지역", regions)

filtered_df = df.copy()

if len(date_range) == 2:
    start_filter, end_filter = date_range
    filtered_df = filtered_df[
        (filtered_df['start_date'].dt.date >= start_filter) &
        (filtered_df['start_date'].dt.date <= end_filter)
    ]

if search:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False, na=False)]

if selected_region != "전체":
    filtered_df = filtered_df[filtered_df['region'] == selected_region]

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 전체 일정", "📊 통계", "📅 캘린더", "📥 내보내기", "🩺 소스 상태"])

with tab1:
    st.subheader(f"전체 일정 ({len(filtered_df)}건)")
    
    display_cols = ['name', 'start_date', 'end_date', 'location', 'organizer']
    available = [c for c in display_cols if c in filtered_df.columns]
    
    for idx, row in filtered_df.sort_values('start_date').iterrows():
        start_str = row['start_date'].strftime('%Y-%m-%d') if pd.notna(row['start_date']) else 'N/A'
        end_str = row['end_date'].strftime('%Y-%m-%d') if pd.notna(row['end_date']) else start_str
        
        with st.expander(f"📍 {row['name']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**일정**: {start_str} ~ {end_str}")
                st.write(f"**장소**: {row.get('location', 'N/A')}")
            with col2:
                st.write(f"**주최**: {row.get('organizer', 'N/A')}")
                st.write(f"**지역**: {row.get('region', 'N/A')}")
            if row.get('source_url'):
                st.write(f"**출처**: {row['source_url']}")

with tab2:
    st.subheader("📊 통계 분석")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("**월별 분포**")
        chart_df = df.copy()
        chart_df['month'] = chart_df['start_date'].dt.month
        monthly = chart_df.groupby('month').size().reset_index(name='count')
        fig = px.bar(monthly, x='month', y='count', color='count', color_continuous_scale='Blues')
        fig.update_layout(xaxis_title="월", yaxis_title="개수", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.write("**장소별 분포 (상위 10)**")
        loc_counts = df['location'].value_counts().head(10)
        fig = px.pie(values=loc_counts.values, names=loc_counts.index, hole=0.3)
        fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    st.write("**지역별 분포**")
    region_counts = df['region'].value_counts()
    fig = px.bar(region_counts, x=region_counts.index, y=region_counts.values, color=region_counts.values, color_continuous_scale='Greens')
    fig.update_layout(xaxis_title="지역", yaxis_title="개수", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("📅 다가오는 일정")
    
    upcoming_df = df[df['start_date'] >= today].sort_values('start_date')
    
    if len(upcoming_df) > 0:
        for idx, row in upcoming_df.head(10).iterrows():
            days_left = (row['start_date'] - today).days
            start_str = row['start_date'].strftime('%Y-%m-%d')
            
            st.info(f"**{row['name']}**\n\n📅 {start_str} ({days_left}일 후) | 📍 {row.get('location', 'N/A')}")
    else:
        st.success("다가오는 일정이 없습니다.")

with tab4:
    st.subheader("📥 데이터 내보내기")
    
    csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 다운로드",
        data=csv_data,
        file_name=f"wedding_expos_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    st.write("**Markdown 테이블**")
    md_lines = ["| 행사명 | 시작일 | 종료일 | 장소 |"]
    md_lines.append("|--------|--------|--------|------|")
    for _, row in filtered_df.iterrows():
        name = row['name'][:30]
        start = row['start_date'].strftime('%Y-%m-%d') if pd.notna(row['start_date']) else ''
        end = row['end_date'].strftime('%Y-%m-%d') if pd.notna(row['end_date']) else ''
        loc = row.get('location', 'N/A')[:20]
        md_lines.append(f"| {name} | {start} | {end} | {loc} |")
    
    st.code("\n".join(md_lines), language="markdown")

with tab5:
    st.subheader("🩺 소스 헬스 상태")

    if not health_state:
        st.info("헬스 상태 데이터가 없습니다. 스크래퍼를 한 번 실행해 주세요.")
    else:
        rows = []
        for source_name, state in sorted(health_state.items()):
            rows.append({
                "소스": source_name,
                "상태": state.get("status", ""),
                "연속 실패": state.get("consecutive_failures", 0),
                "연속 0건": state.get("consecutive_zero_results", 0),
                "마지막 결과": state.get("last_result_count", 0),
                "마지막 성공": state.get("last_success_at", ""),
                "마지막 실패": state.get("last_failed_at", ""),
                "마지막 점검": state.get("last_checked_at", ""),
            })

        health_df = pd.DataFrame(rows)

        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            st.metric("추적 소스", len(health_df))
        with col_h2:
            st.metric("실패 상태", int((health_df["상태"] == "failing").sum()))
        with col_h3:
            quarantined = int(
                ((health_df["연속 실패"] >= 3) | (health_df["연속 0건"] >= 5)).sum()
            )
            st.metric("격리 후보", quarantined)

        st.dataframe(health_df, use_container_width=True, hide_index=True)

        skipped = health_report.get("skipped_sources", [])
        if skipped:
            st.write("**이번 실행에서 제외된 소스**")
            skipped_df = pd.DataFrame(skipped)
            st.dataframe(skipped_df, use_container_width=True, hide_index=True)

        if health_report.get("sources"):
            report_rows = []
            for source_name, stats in sorted(health_report["sources"].items()):
                report_rows.append({
                    "소스": source_name,
                    "종류": stats.get("kind", ""),
                    "성공": stats.get("success", False),
                    "결과 수": stats.get("result_count", 0),
                    "오류": stats.get("error", ""),
                })
            st.write("**최근 실행 요약**")
            st.dataframe(pd.DataFrame(report_rows), use_container_width=True, hide_index=True)

st.sidebar.header("ℹ️ 시스템 정보")
st.sidebar.success(f"**총 데이터**: {len(df)}건")
st.sidebar.info(f"**마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

sources_info = df.groupby('organizer').size().reset_index(name='count').sort_values('count', ascending=False)
st.sidebar.write("**소스별 수집**")
for _, row in sources_info.head(5).iterrows():
    st.sidebar.write(f"- {row['organizer']}: {row['count']}건")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**광주광역시 웨딩박람회 자동 수집**

- 자동 업데이트: 매일 06:00, 18:00
- GitHub: [dkdleljh/wedding-expo-scraper](https://github.com/dkdleljh/wedding-expo-scraper)
""")
