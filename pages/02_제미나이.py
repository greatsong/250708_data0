import streamlit as st
import pandas as pd
import altair as alt
import re

# Streamlit 앱의 페이지 설정을 넓은 레이아웃으로 변경
st.set_page_config(layout="wide")

st.title('📊 연령별 인구 현황 분석 대시보드')
st.write("CSV 파일을 업로드하거나 기본 제공되는 2025년 6월 데이터를 사용하여, '총인구수' 기준 상위 5개 행정구역의 연령별 인구 분포를 확인합니다.")

# 데이터 전처리 및 로드 함수 정의
@st.cache_data
def load_and_preprocess_data(file):
    """
    파일을 읽고 명시된 전처리 규칙에 따라 데이터를 가공합니다.
    - 인코딩 감지 (UTF-8, EUC-KR)
    - 데이터 타입 변환 (문자열 -> 숫자)
    - 컬럼 이름 정리
    - 분석에 적합한 행정구역 필터링
    """
    try:
        # UTF-8으로 파일 읽기 시도
        raw_df = pd.read_csv(file, encoding='utf-8')
    except UnicodeDecodeError:
        # 실패 시 EUC-KR로 재시도
        file.seek(0) # 파일 포인터를 처음으로 되돌림
        raw_df = pd.read_csv(file, encoding='euc-kr')

    df = raw_df.copy()

    # 1. 불필요한 열 제거
    if '2025년06월_계_연령구간인구수' in df.columns:
        df = df.drop(columns=['2025년06월_계_연령구간인구수'])

    # 2. 총인구수 컬럼 이름 변경 및 타입 변환
    if '2025년06월_계_총인구수' in df.columns:
        df.rename(columns={'2025년06월_계_총인구수': '총인구수'}, inplace=True)
        df['총인구수'] = df['총인구수'].str.replace(',', '').astype(int)
    else:
        # 만약 '총인구수' 컬럼이 없다면, 다른 컬럼들을 합산하여 생성
        numeric_cols = df.columns.drop('행정구역')
        for col in numeric_cols:
             df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        df.fillna(0, inplace=True)
        df['총인구수'] = df[numeric_cols].sum(axis=1)


    # 3. 연령별 인구 데이터 전처리
    age_cols = [col for col in df.columns if '세' in col]
    for col in age_cols:
        df[col] = df[col].astype(str).str.replace(',', '').astype(int)

    # 4. 연령 컬럼 이름에서 숫자만 추출
    def extract_age(col_name):
        # '100세 이상'과 같은 패턴을 처리
        match = re.search(r'(\d+)', col_name)
        if match:
            return int(match.group(1))
        return None

    new_column_names = {col: extract_age(col) for col in df.columns if '세' in col}
    df.rename(columns=new_column_names, inplace=True)
    
    # 정수형 컬럼만 필터링
    new_column_names = {k:v for k,v in new_column_names.items() if isinstance(v, int)}
    
    # 5. 행정구역 필터링 ('시/군/구' 단위만 선택)
    # '특별시', '광역시', '특별자치시', '도', '특별자치도' 제외
    special_cities = ['서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', '세종특별자치시']
    provinces = ['경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도']
    
    # 광역자치단체 및 '읍/면/동'이 포함된 행정구역 제외
    df = df[~df['행정구역'].str.contains('읍|면|동', na=False)]
    df = df[~df['행정구역'].isin(special_cities)]
    df = df[~df['행정구역'].isin(provinces)]
    # '전국' 데이터 제외
    df = df[df['행정구역'] != '전국']


    # 6. 데이터 구조 변경 (Wide to Long)
    id_vars = ['행정구역', '총인구수']
    value_vars = sorted([col for col in new_column_names.values() if isinstance(col, int)])

    long_df = pd.melt(df, id_vars=id_vars, value_vars=value_vars,
                      var_name='연령', value_name='인구수')

    return df, long_df

# 파일 업로더 UI
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type="csv")

# 파일 처리 로직
data_file = None
if uploaded_file is not None:
    data_file = uploaded_file
else:
    try:
        # 기본 파일 사용
        data_file = open('202506_202506_연령별인구현황_월간.csv', 'rb')
    except FileNotFoundError:
        st.error("기본 데이터 파일('202506_202506_연령별인구현황_월간.csv')을 찾을 수 없습니다. 파일을 업로드해주세요.")
        st.stop()

# 데이터 로드 및 전처리
try:
    wide_df, long_df = load_and_preprocess_data(data_file)
    
    # 총인구수 기준 상위 5개 행정구역 필터링
    top5_districts = wide_df.nlargest(5, '총인구수')['행정구역'].tolist()
    
    st.subheader(f"총인구수 기준 상위 5개 행정구역 (2025년 6월 기준)")

    # 상위 5개 행정구역 데이터프레임 표시 (총인구수, 행정구역 순으로)
    st.dataframe(wide_df[wide_df['행정구역'].isin(top5_districts)][['행정구역', '총인구수']].sort_values(by='총인구수', ascending=False).reset_index(drop=True))
    
    # 시각화를 위한 데이터 필터링
    top5_long_df = long_df[long_df['행정구역'].isin(top5_districts)]

    # Altair 선 그래프 생성
    st.subheader("상위 5개 행정구역 연령별 인구 분포")
    
    chart = alt.Chart(top5_long_df).mark_line().encode(
        y=alt.Y('연령:Q', title='연령', axis=alt.Axis(format='d')), # 'd'는 정수 포맷
        x=alt.X('인구수:Q', title='인구수'),
        color=alt.Color('행정구역:N', title='행정구역'),
        tooltip=['행정구역', '연령', '인구수']
    ).properties(
        title='연령별 인구 분포 (상위 5개 행정구역)',
        width='container' # 컨테이너 너비에 맞춤
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
finally:
    # 파일 객체를 열었다면 닫아줌
    if data_file is not None and not hasattr(data_file, 'name'):
        data_file.close()
