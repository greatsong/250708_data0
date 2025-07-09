import streamlit as st
import pandas as pd

# CSV 파일 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")

if uploaded_file:
    # EUC-KR로 파일 읽기
    df = pd.read_csv(uploaded_file, encoding="euc-kr")

    # 괄호 제거
    df['행정구역'] = df['행정구역'].str.replace(r'\(.*?\)', '', regex=True).str.strip()

    # 총인구수 및 연령별 컬럼 선택
    total_col = '2025년06월_계_총인구수'
    age_cols = [col for col in df.columns if '2025년06월_계_' in col and ('세' in col or '100세 이상' in col)]

    df_slim = df[['행정구역', total_col] + age_cols].copy()

    # 컬럼명 간소화
    def rename_age(col):
        if '100세 이상' in col:
            return '100'
        return col.split('_')[-1].replace('세', '')

    df_slim.rename(columns={col: rename_age(col) for col in age_cols}, inplace=True)

    # 총인구수 숫자형으로 변환
    df_slim[total_col] = pd.to_numeric(df_slim[total_col], errors='coerce')

    # 상위 5개 지역 추출
    top5 = df_slim.sort_values(by=total_col, ascending=False).head(5)

    # 연령 컬럼만 추출
    age_columns = [col for col in top5.columns if col.isdigit()]
    age_columns_sorted = sorted(age_columns, key=int)

    # 연령 데이터를 전치하여 시각화
    chart_df = top5.set_index('행정구역')[age_columns_sorted].T
    chart_df.index.name = '연령'
    chart_df = chart_df.astype(int)

    # 선 그래프 출력
    st.line_chart(chart_df)
