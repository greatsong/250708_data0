import streamlit as st
import pandas as pd
import altair as alt

st.title('📊 2025년 6월 연령별 인구 현황 분석')

# 파일 업로드 및 기본 파일 로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")
if uploaded_file is not None:
    # 인코딩 자동 감지
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding='euc-kr')
else:
    # 기본 파일 로드 시도
    try:
        df = pd.read_csv('data.csv', encoding='utf-8')
    except (UnicodeDecodeError, FileNotFoundError):
        st.error("파일을 찾을 수 없거나 인코딩 오류가 발생했습니다. UTF-8 또는 EUC-KR로 저장된 CSV 파일을 업로드해주세요.")
        st.stop()

# 컬럼 전처리
df.columns = [col.replace('2025년06월_계_', '').replace('세', '') for col in df.columns]

# 비숫자 컬럼 제거 (예: '100 이상')
numeric_cols = []
for col in df.columns:
    if col in ['행정구역', '총인구수']:
        continue
    if col.replace('.', '', 1).isdigit():
        numeric_cols.append(col)
    else:
        df = df.drop(columns=[col], errors='ignore')

# 데이터 용융 (long format으로 변환)
if not numeric_cols:
    st.error("연령 관련 숫자 컬럼이 없습니다. 데이터 형식을 확인해주세요.")
    st.stop()

df_long = pd.melt(
    df, 
    id_vars=['행정구역', '총인구수'], 
    value_vars=numeric_cols, 
    var_name='연령', 
    value_name='인구수'
)
df_long['연령'] = df_long['연령'].astype(int)

# 상위 5개 행정구역 추출
try:
    top_regions = df.groupby('행정구역')['총인구수'].sum().nlargest(5).index.tolist()
    df_top = df_long[df_long['행정구역'].isin(top_regions)]
except KeyError:
    st.error("데이터에 필요한 컬럼이 없습니다. '행정구역' 또는 '총인구수' 컬럼을 확인해주세요.")
    st.stop()

# 시각화
chart = alt.Chart(df_top).mark_line().encode(
    x=alt.X('인구수:Q', title='인구 수', scale=alt.Scale(type='log')),
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
st.dataframe(
    df.groupby('행정구역')['총인구수'].sum()
    .nlargest(5)
    .reset_index()
    .style.format({'총인구수': '{:,}명'})
)

# 데이터 샘플 표시
st.subheader('📊 원본 데이터 샘플')
st.dataframe(df.head(3))
