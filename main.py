import streamlit as st
import pandas as pd
import io
import re

st.title("상위 5개 행정구역 연령별 인구 시각화")

# CSV 업로드
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요 (EUC-KR 인코딩)", type="csv")

if uploaded_file is not None:
    try:
        # 파일 내용을 바이너리로 읽고 디코딩 시도
        raw_bytes = uploaded_file.read()
        text = raw_bytes.decode('euc-kr')  # EUC-KR로 디코딩
        df = pd.read_csv(io.StringIO(text))
    except UnicodeDecodeError:
        st.error("❌ EUC-KR 인코딩 오류: 올바른 CSV 파일인지 확인해주세요.")
    else:
        # 1. 행정구역 괄호 제거
        df['행정구역'] = df['행정구역'].str.replace(r'\(.*?\)', '', regex=True).str.strip()

        # 2. 총인구수 및 연령 관련 열만 필터링
        total_col = '2025년06월_계_총인구수'
        age_cols = [col for col in df.columns if '2025년06월_계_' in col and ('세' in col or '100세 이상' in col)]
        df_slim = df[['행정구역', total_col] + age_cols].copy()

        # 3. 열 이름 정리
        def rename_age(col):
            if '100세 이상' in col:
                return '100'
            return col.split('_')[-1].replace('세', '')

        df_slim.rename(columns={col: rename_age(col) for col in age_cols}, inplace=True)

        # 4. 총인구수 숫자형 변환 및 상위 5개 지역 선택
        df_slim[total_col] = pd.to_numeric(df_slim[total_col], errors='coerce')
        top5 = df_slim.sort_values(by=total_col, ascending=False).head(5)

        # 5. 연령별 컬럼 추출
        age_columns = [col for col in top5.columns if col.isdigit()]
        age_columns_sorted = sorted(age_columns, key=int)

        # 6. 시각화용 데이터 구성 (전치)
        chart_df = top5.set_index('행정구역')[age_columns_sorted].T
        chart_df.index.name = '연령'
        chart_df = chart_df.astype(int)

        # 7. 선 그래프 출력
        st.line_chart(chart_df)
