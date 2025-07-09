import streamlit as st
import pandas as pd
import io
import re

st.title("상위 5개 행정구역 연령별 인구 시각화")

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")

if uploaded_file:
    raw_bytes = uploaded_file.read()

    # EUC-KR 먼저 시도, 실패 시 UTF-8 시도
    for enc in ['euc-kr', 'utf-8']:
        try:
            text = raw_bytes.decode(enc)
            df = pd.read_csv(io.StringIO(text))
            st.success(f"✅ 인코딩 방식: {enc.upper()} 로 성공적으로 읽었습니다.")
            break
        except Exception as e:
            df = None

    if df is None:
        st.error("❌ CSV 파일을 읽을 수 없습니다. EUC-KR 또는 UTF-8 인코딩인지 확인해주세요.")
    else:
        # 전처리 1: 행정구역 괄호 제거
        df['행정구역'] = df['행정구역'].str.replace(r'\(.*?\)', '', regex=True).str.strip()

        # 전처리 2: 총인구수와 연령 관련 컬럼 추출
        total_col = '2025년06월_계_총인구수'
        age_cols = [col for col in df.columns if '2025년06월_계_' in col and ('세' in col or '100세 이상' in col)]

        df_slim = df[['행정구역', total_col] + age_cols].copy()

        # 전처리 3: 연령 컬럼 이름 정리
        def rename_age(col):
            if '100세 이상' in col:
                return '100'
            return col.split('_')[-1].replace('세', '')

        df_slim.rename(columns={col: rename_age(col) for col in age_cols}, inplace=True)

        # 전처리 4: 총인구수 숫자형 변환 및 상위 5개 지역 추출
        df_slim[total_col] = pd.to_numeric(df_slim[total_col], errors='coerce')
        top5 = df_slim.sort_values(by=total_col, ascending=False).head(5)

        # 전처리 5: 연령 컬럼만 추출 후 정렬
        age_columns = [col for col in top5.columns if col.isdigit()]
        age_columns_sorted = sorted(age_columns, key=int)

        # 시각화용 데이터 구성
        chart_df = top5.set_index('행정구역')[age_columns_sorted].T
        chart_df.index.name = '연령'
        chart_df = chart_df.astype(int)

        st.line_chart(chart_df)
