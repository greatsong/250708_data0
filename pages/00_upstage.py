import streamlit as st
import pandas as pd
import altair as alt
import os

st.title('📊 2025년 6월 연령별 인구 현황 분석')

# 파일 업로드 및 기본 파일 로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")
file_path = 'data.csv' if not uploaded_file else None

df = None
try:
    if uploaded_file is not None:
        # 업로드된 파일 처리
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8', nrows=100)
            if df.empty:
                raise pd.errors.EmptyDataError()
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='euc-kr', nrows=100)
            if df.empty:
                raise pd.errors.EmptyDataError()
    else:
        # 기본 파일 처리
        if not os.path.exists(file_path):
            st.error("기본 파일(data.csv)이 존재하지 않습니다. CSV 파일을 업로드해주세요.")
            st.stop()
        try:
            df = pd.read_csv(file_path, encoding='utf-8', nrows=100)
            if df.empty:
                raise pd.errors.EmptyDataError()
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='euc-kr', nrows=100)
            if df.empty:
                raise pd.errors.EmptyDataError()
except pd.errors.EmptyDataError:
    st.error("업로드된 파일이 비어 있습니다. 유효한 CSV 파일을 사용해주세요.")
    st.stop()

# 디버그: 원본 데이터 구조 확인
with st.expander("🔍 원본 데이터 구조 확인"):
    try:
        sample = pd.read_csv(uploaded_file if uploaded_file else file_path, nrows=3)
        st.write("원본 컬럼명:", sample.columns.tolist())
        st.write("데이터 샘플:", sample)
    except Exception as e:
        st.warning(f"디버그 정보 로드 실패: {str(e)}")

# 컬럼 전처리 (공백 제거 및 특수문자 처리)
df.columns = [col.replace('2025년06월_계_', '').replace('세', '').strip() for col in df.columns]

# 디버그: 전처리 후 컬럼명 출력
with st.expander("🔍 전처리 후 컬럼명 확인"):
    st.write("전처리 후 컬럼명:", df.columns.tolist())

# 필수 컬럼 존재 여부 검증
required_cols = ['행정구역', '총인구수']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"필수 컬럼이 누락되었습니다: {', '.join(missing_cols)}. 데이터 형식을 확인해주세요.")
    st.stop()

# 숫자형 컬럼 추출
numeric_cols = []
for col in df.columns:
    if col in required_cols:
        continue
    if col.replace('.', '', 1).isdigit():
        numeric_cols.append(col)
    else:
        df = df.drop(columns=[col], errors='ignore')

# 숫자형 컬럼이 없는 경우 처리
if not numeric_cols:
    st.error("연령 관련 숫자 컬럼이 없습니다. 데이터 형식을 확인해주세요.")
    st.stop()

# 데이터 용융 (long format으로 변환)
df_long = pd.melt(
    df, 
    id_vars=required_cols, 
    value_vars=numeric_cols, 
    var_name='연령', 
    value_name='인구수'
)
df_long['연령'] = df_long['연령'].astype(int)

# 상위 5개 행정구역 추출
try:
    top_regions = df.groupby('행정구역')['총인구수'].sum().nlargest(5).index.tolist()
    df_top = df_long[df_long['행정구역'].isin(top_regions)]
except Exception as e:
    st.error(f"데이터 처리 중 오류 발생: {str(e)}. '행정구역' 또는 '총인구수' 컬럼을 확인해주세요.")
    st.stop()

# 시각화
chart = alt.Chart(df_top).mark_line().encode(
    x=alt.X('인구수:Q', title='인구 수', scale=alt.Scale(type='log', domain=(1, None))),
    y=alt.Y('연령:N', title='연령', sort='-x'),
    color=alt.Color('행정구역:N', legend=alt.Legend(title='행정구역')),
    tooltip=['행정구역', '연령', alt.Tooltip('인구수:Q', format=',.0f')]
).properties(
    width=800,
    height=500
).configure_axis(
    labelFontSize=12,
    titleFontSize=14
)

st.altair_chart(chart, use_container_width=True)

# 상위 5개 행정구역 표 표시
st.subheader('🏆 총인구수 상위 5개 행정구역')
top_regions_df = df.groupby('행정구역')['총인구수'].sum().nlargest(5).reset_index()
st.dataframe(top_regions_df.style.format({'총인구수': '{:,}명'}))
