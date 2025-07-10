import streamlit as st
import pandas as pd
import altair as alt
import os
from io import StringIO

st.title('📊 2025년 6월 연령별 인구 현황 분석')

# 파일 업로드 및 기본 파일 로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")
file_path = 'data.csv' if not uploaded_file else None

def try_read_file(file_obj, encodings):
    """여러 인코딩을 시도하여 파일 읽기"""
    for encoding in encodings:
        try:
            if isinstance(file_obj, str):  # 파일 경로인 경우
                df = pd.read_csv(file_obj, encoding=encoding, nrows=100, on_bad_lines='skip')
            else:  # 업로드 파일인 경우
                file_obj.seek(0)
                content = file_obj.read().decode(encoding)
                df = pd.read_csv(StringIO(content), nrows=100, on_bad_lines='skip')
            if not df.empty:
                return df, encoding
        except Exception as e:
            continue
    raise Exception("모든 인코딩 시도 실패")

try:
    if uploaded_file is not None:
        # 업로드된 파일 처리
        df, encoding_used = try_read_file(
            uploaded_file, 
            ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
        )
    else:
        # 기본 파일 처리
        if not os.path.exists(file_path):
            st.error("기본 파일(data.csv)이 존재하지 않습니다. CSV 파일을 업로드해주세요.")
            st.stop()
        df, encoding_used = try_read_file(
            file_path, 
            ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
        )
except Exception:
    st.error("파일 인코딩을 자동으로 감지하지 못했습니다. UTF-8 또는 CP949/EUC-KR 인코딩으로 저장된 CSV 파일을 사용해주세요.")
    st.stop()

# 전체 데이터 로드
try:
    if uploaded_file:
        uploaded_file.seek(0)
        content = uploaded_file.read().decode(encoding_used)
        df_full = pd.read_csv(StringIO(content), on_bad_lines='skip')
    else:
        df_full = pd.read_csv(file_path, encoding=encoding_used, on_bad_lines='skip')
except Exception as e:
    st.error(f"데이터 로드 실패: {str(e)}. 파일 형식을 확인해주세요.")
    st.stop()

# 컬럼 전처리 (행정구역, 총인구수는 보존)
new_columns = []
for col in df_full.columns:
    if '행정구역' in str(col) or '총인구수' in str(col):
        new_columns.append(col)
    else:
        cleaned = str(col).replace('2025년06월_계_', '').replace('세', '').strip()
        new_columns.append(cleaned)
df_full.columns = new_columns

# 디버그: 전처리 전후 컬럼명 비교
with st.expander("🔍 전처리 전후 컬럼명 비교"):
    try:
        if uploaded_file:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode(encoding_used)
            temp_df = pd.read_csv(StringIO(content), nrows=1, on_bad_lines='skip')
        else:
            temp_df = pd.read_csv(file_path, nrows=1, encoding=encoding_used, on_bad_lines='skip')
        original_cols = temp_df.columns.tolist() if not temp_df.empty else []
        st.write("원본 컬럼명:", original_cols)
        st.write("전처리 후 컬럼명:", df_full.columns.tolist())
    except Exception as e:
        st.warning(f"디버그 정보 로드 실패: {str(e)}. 헤더 정보가 없을 수 있습니다.")
        st.write("전처리 후 컬럼명:", df_full.columns.tolist())

# 필수 컬럼 존재 여부 검증
required_cols = ['행정구역', '총인구수']
missing_cols = [col for col in required_cols if col not in df_full.columns]
if missing_cols:
    st.error(f"필수 컬럼이 누락되었습니다: {', '.join(missing_cols)}. 데이터 형식을 확인해주세요.")
    st.stop()

# 숫자형 컬럼 추출
numeric_cols = []
for col in df_full.columns:
    if col in required_cols:
        continue
    if col.replace('.', '', 1).isdigit():
        numeric_cols.append(col)
    else:
        df_full = df_full.drop(columns=[col], errors='ignore')

# 숫자형 컬럼이 없는 경우 처리
if not numeric_cols:
    st.error("연령 관련 숫자 컬럼이 없습니다. 데이터 형식을 확인해주세요.")
    st.stop()

# 데이터 용융 (long format으로 변환)
try:
    df_long = pd.melt(
        df_full, 
        id_vars=required_cols, 
        value_vars=numeric_cols, 
        var_name='연령', 
        value_name='인구수'
    )
    df_long['연령'] = df_long['연령'].astype(int)
except Exception as e:
    st.error(f"데이터 용융 실패: {str(e)}. 컬럼 형식 확인 필요")
    st.stop()

# 상위 5개 행정구역 추출
try:
    top_regions = df_full.groupby('행정구역')['총인구수'].sum().nlargest(5).index.tolist()
    df_top = df_long[df_long['행정구역'].isin(top_regions)]
except Exception as e:
    st.error(f"데이터 처리 중 오류 발생: {str(e)}. '행정구역' 또는 '총인구수' 컬럼을 확인해주세요.")
    st.stop()

# 시각화
try:
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
except Exception as e:
    st.error(f"시각화 생성 실패: {str(e)}. 데이터 구조 확인 필요")

# 상위 5개 행정구역 표 표시
try:
    st.subheader('🏆 총인구수 상위 5개 행정구역')
    top_regions_df = df_full.groupby('행정구역')['총인구수'].sum().nlargest(5).reset_index()
    st.dataframe(top_regions_df.style.format({'총인구수': '{:,}명'}))
except Exception as e:
    st.error(f"결과 표시 실패: {str(e)}")
