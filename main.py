import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="연령별 인구 시각화", layout="wide")
st.title("📊 2025년 6월 기준 연령별 인구 현황")

# 파일 업로드 or 기본 파일
uploaded_file = st.file_uploader("CSV 파일 업로드 (UTF-8 또는 EUC-KR)", type=["csv"])
default_path = "age.csv"

# 파일 로딩 함수
def load_csv(file):
    encodings = ["utf-8", "euc-kr"]
    for enc in encodings:
        try:
            df = pd.read_csv(file, encoding=enc)
            return df
        except:
            continue
    st.error("❌ 파일을 불러오는 데 실패했습니다. 인코딩을 확인해주세요.")
    return None

# 파일 로드
if uploaded_file:
    df_raw = load_csv(uploaded_file)
else:
    try:
        df_raw = pd.read_csv(default_path, encoding="utf-8")
    except:
        df_raw = pd.read_csv(default_path, encoding="euc-kr")

if df_raw is not None:
    df = df_raw.copy()

    # 연령 컬럼 선택
    age_columns = [col for col in df.columns if col.startswith("2025년06월_계_") and '세' in col]

    # 연령 컬럼 이름 정리
    age_map = {}
    for col in age_columns:
        if '100세 이상' in col:
            age_map[col] = 100
        else:
            age_num = int(col.split('_')[-1].replace('세', ''))
            age_map[col] = age_num

    df_age = df[['행정구역', '2025년06월_계_총인구수'] + age_columns].copy()
    df_age.rename(columns=age_map, inplace=True)

    # 시도 단위만 필터링 (코드: **00000000)
    df_age = df_age[df_age['행정구역'].str.contains(r'\(\d{2}00000000\)', regex=True)].copy()
    df_age['행정구역'] = df_age['행정구역'].str.replace(r'\s*\(\d+\)', '', regex=True)

    # 총인구수 정수 변환
    df_age['총인구수'] = df_age['2025년06월_계_총인구수']
    df_age = df_age.drop(columns=['2025년06월_계_총인구수'])

    # 상위 5개 시도
    top5_df = df_age.sort_values('총인구수', ascending=False).head(5)

    # melt로 변환: 연령별 선그래프용
    df_melted = top5_df.melt(id_vars=['행정구역', '총인구수'], var_name='연령', value_name='인구수')
    df_melted['연령'] = df_melted['연령'].astype(int)

    # Altair 시각화
    chart = alt.Chart(df_melted).mark_line(point=True).encode(
        x=alt.X('연령:O', title='연령', sort='ascending'),
        y=alt.Y('인구수:Q', title='인구수'),
        color=alt.Color('행정구역:N', title='시도'),
        tooltip=['행정구역', '연령', '인구수']
    ).properties(
        width=800,
        height=500,
        title='상위 5개 시도의 연령별 인구 분포'
    )

    st.altair_chart(chart, use_container_width=True)

    with st.expander("🔍 원본 데이터 보기"):
        st.dataframe(top5_df, use_container_width=True)
