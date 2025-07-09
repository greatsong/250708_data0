import streamlit as st
import pandas as pd
import altair as alt
import io
import re

st.title("📊 상위 5개 행정구역 연령별 인구 시각화 (정렬 보정)")

uploaded_file = st.file_uploader("CSV 파일을 업로드하세요 (EUC-KR 또는 UTF-8)", type="csv")

if uploaded_file:
    raw_bytes = uploaded_file.read()

    # 1. 인코딩 자동 판별
    for enc in ['euc-kr', 'utf-8']:
        try:
            text = raw_bytes.decode(enc)
            df = pd.read_csv(io.StringIO(text))
            st.success(f"✅ 파일 인코딩: {enc.upper()} 로 성공적으로 읽었습니다.")
            break
        except Exception:
            df = None

    if df is None:
        st.error("❌ CSV 파일을 읽을 수 없습니다. EUC-KR 또는 UTF-8 인코딩인지 확인해주세요.")
    else:
        # 2. 행정구역 괄호 제거
        df['행정구역'] = df['행정구역'].str.replace(r'\(.*?\)', '', regex=True).str.strip()

        # 3. 필요한 열 추출
        total_col = '2025년06월_계_총인구수'
        age_cols = [col for col in df.columns if '2025년06월_계_' in col and ('세' in col or '100세 이상' in col)]
        df_slim = df[['행정구역', total_col] + age_cols].copy()

        # 4. 열 이름 정리
        def rename_age(col):
            if '100세 이상' in col:
                return '100'
            return col.split('_')[-1].replace('세', '')

        df_slim.rename(columns={col: rename_age(col) for col in age_cols}, inplace=True)

        # 5. 총인구수 숫자형 변환 및 상위 5개 지역 추출
        df_slim[total_col] = pd.to_numeric(df_slim[total_col], errors='coerce')
        top5 = df_slim.sort_values(by=total_col, ascending=False).head(5)

        # 6. 연령 컬럼만 추출 및 정렬
        age_columns = [col for col in top5.columns if col.isdigit()]
        age_columns_sorted = sorted(age_columns, key=int)

        # 7. 시각화용 데이터 구성 (melt for Altair)
        df_melted = top5.melt(id_vars='행정구역', value_vars=age_columns_sorted,
                              var_name='연령', value_name='인구')
        df_melted['연령'] = df_melted['연령'].astype(int)  # 정렬용
        df_melted['인구'] = df_melted['인구'].astype(int)

        # 8. Altair 선 그래프 생성
        chart = alt.Chart(df_melted).mark_line().encode(
            x=alt.X('연령:Q', title='연령', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('인구:Q', title='인구 수'),
            color='행정구역:N',
            tooltip=['행정구역', '연령', '인구']
        ).properties(
            width=800,
            height=500,
            title='연령별 인구 분포 (상위 5개 지역)'
        )

        # 9. 출력
        st.altair_chart(chart, use_container_width=True)
