import streamlit as st
import pandas as pd
import altair as alt
import io

st.title("📊 2025년 6월 기준 연령별 인구 현황 분석")

# 1. 파일 업로드 또는 기본 파일 불러오기
uploaded_file = st.file_uploader("CSV 파일 업로드 (미업로드 시 기본 파일 사용)", type=["csv"])

@st.cache_data
def load_csv(uploaded_file):
    for enc in ['utf-8', 'euc-kr']:
        try:
            return pd.read_csv(uploaded_file, encoding=enc)
        except UnicodeDecodeError:
            continue
    st.error("❌ CSV 인코딩을 확인해주세요. UTF-8 또는 EUC-KR이어야 합니다.")
    return None

if uploaded_file is not None:
    df = load_csv(uploaded_file)
else:
    df = load_csv("202506_202506_연령별인구현황_월간.csv")

if df is not None:
    # 시도 추출
    df['시도'] = df['행정구역'].str.extract(r'^(.*?[시도])')

    # 총인구수 숫자 변환
    df['총인구수'] = df['2025년06월_계_총인구수'].astype(str).str.replace(',', '').astype(int)

    # 연령별 컬럼 정리
    age_cols = [col for col in df.columns if '2025년06월_계_' in col and '세' in col]
    age_renamed = {}
    for col in age_cols:
        if '100세 이상' in col:
            age_renamed[col] = '100'
        else:
            age_renamed[col] = col.split('_')[-1].replace('세', '')
    df = df[['시도', '총인구수'] + age_cols].rename(columns=age_renamed)

    # 쉼표 제거 및 숫자형으로 변환
    for col in age_renamed.values():
        df[col] = df[col].astype(str).str.replace(',', '').astype(int)

    # 시도 단위로 집계
    df_grouped = df.groupby('시도').sum(numeric_only=True).reset_index()
    top5 = df_grouped.nlargest(5, '총인구수')

    # Melt
    melted = top5.melt(id_vars=['시도', '총인구수'], var_name='연령', value_name='인구수')
    melted['연령'] = melted['연령'].astype(int)
    melted.sort_values(by='연령', inplace=True)

    # Altair 시각화
    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X('연령:O', title='연령'),
        y=alt.Y('인구수:Q', title='인구 수'),
        color='시도:N'
    ).properties(width=700, height=400, title='상위 5개 시도별 연령대별 인구 분포')

    st.altair_chart(chart, use_container_width=True)
