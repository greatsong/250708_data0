import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="연령별 인구 시각화", layout="wide")
st.title("📊 2025년 6월 기준 연령별 인구 현황 분석")

# 파일 업로드 또는 기본 경로 설정
uploaded_file = st.file_uploader("CSV 파일 업로드 (없으면 기본 파일 사용)", type=["csv"])
default_path = "202506_202506_연령별인구현황_월간.csv"

# CSV 불러오기 함수 (인코딩 자동 감지 + 업로드/로컬 모두 대응)
def load_csv_safely(source):
    encodings = ['utf-8', 'euc-kr']
    for enc in encodings:
        try:
            if isinstance(source, str):  # 기본 경로
                return pd.read_csv(source, encoding=enc)
            else:  # 업로드된 파일 처리
                content = source.read()
                text = content.decode(enc)
                return pd.read_csv(io.StringIO(text))
        except Exception:
            try:
                source.seek(0)
            except Exception:
                pass
    return None

# 파일 선택 및 불러오기
if uploaded_file is not None:
    data_source = uploaded_file
    st.info("✅ 업로드된 파일을 사용합니다.")
else:
    try:
        open(default_path)
        data_source = default_path
        st.info("📂 기본 파일을 사용합니다.")
    except FileNotFoundError:
        st.error("❌ 기본 파일이 없습니다. CSV를 업로드해주세요.")
        st.stop()

df = load_csv_safely(data_source)
if df is None:
    st.error("❌ 파일을 불러올 수 없습니다. UTF-8 또는 EUC-KR 인코딩을 확인하세요.")
    st.stop()

# 첫 번째 컬럼명 보정
df.columns.values[0] = '행정구역'

# 시도 추출
df['시도'] = df['행정구역'].str.extract(r'^(.*?[시도])')

# 총인구수 처리
if '총인구수' not in df.columns:
    df['총인구수'] = df['2025년06월_계_총인구수'].astype(str).str.replace(',', '').astype(int)

# 연령별 컬럼 추출
age_cols = [col for col in df.columns if '2025년06월_계_' in col and '세' in col]
age_renamed = {
    col: '100' if '100세 이상' in col else col.split('_')[-1].replace('세', '')
    for col in age_cols
}
df = df[['시도', '총인구수'] + age_cols].rename(columns=age_renamed)

# 숫자형 변환
for col in age_renamed.values():
    df[col] = df[col].astype(str).str.replace(',', '').astype(int)

# 시도별 그룹화 및 상위 5개 추출
df_grouped = df.groupby('시도').sum(numeric_only=True).reset_index()
top5 = df_grouped.nlargest(5, '총인구수')

# Melt
melted = top5.melt(id_vars=['시도', '총인구수'], var_name='연령', value_name='인구수')
melted['연령'] = melted['연령'].astype(int)
melted = melted.sort_values(by='연령')

# Altair 시각화
chart = alt.Chart(melted).mark_line().encode(
    x=alt.X('연령:O', title='연령'),
    y=alt.Y('인구수:Q', title='인구 수'),
    color='시도:N'
).properties(
    width=800,
    height=450,
    title='상위 5개 시도별 연령대별 인구 분포'
)

st.altair_chart(chart, use_container_width=True)
