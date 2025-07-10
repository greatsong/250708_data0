import streamlit as st
import pandas as pd
import altair as alt
import chardet
import io

def detect_encoding(file_content):
    """파일 인코딩을 감지합니다."""
    try:
        detected = chardet.detect(file_content)
        return detected['encoding']
    except:
        return 'utf-8'

def load_csv_file(file_path=None, uploaded_file=None):
    """CSV 파일을 로드하고 인코딩을 처리합니다."""
    if uploaded_file is not None:
        # 업로드된 파일 처리
        file_content = uploaded_file.read()
        encoding = detect_encoding(file_content)
        
        # 일반적인 한국어 인코딩들을 시도
        encodings_to_try = [encoding, 'euc-kr', 'cp949', 'utf-8']
        
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
                st.success(f"파일을 {enc} 인코딩으로 성공적으로 읽었습니다.")
                return df
            except:
                continue
        
        st.error("파일 인코딩을 인식할 수 없습니다.")
        return None
    
    elif file_path:
        # 기본 파일 처리
        encodings_to_try = ['euc-kr', 'cp949', 'utf-8']
        
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                st.success(f"기본 파일을 {encoding} 인코딩으로 성공적으로 읽었습니다.")
                return df
            except:
                continue
        
        st.error("기본 파일을 읽을 수 없습니다.")
        return None

def preprocess_data(df):
    """데이터 전처리를 수행합니다."""
    if df is None:
        return None
    
    # 컬럼명 정리
    df_processed = df.copy()
    
    # 행정구역 컬럼명 정리
    admin_col = [col for col in df_processed.columns if '행정구역' in col or col == '행정구역'][0]
    df_processed = df_processed.rename(columns={admin_col: '행정구역'})
    
    # 총인구수 컬럼 찾기
    total_pop_col = [col for col in df_processed.columns if '총인구수' in col][0]
    df_processed = df_processed.rename(columns={total_pop_col: '총인구수'})
    
    # 총인구수를 숫자로 변환
    if df_processed['총인구수'].dtype == 'object':
        df_processed['총인구수'] = df_processed['총인구수'].str.replace(',', '').astype(int)
    
    # 연령별 컬럼 찾기 및 이름 변경
    age_columns = {}
    for col in df_processed.columns:
        if '2025년06월_계_' in col and '세' in col:
            if '100세 이상' in col:
                age_columns[col] = '100'
            else:
                # 연령 추출
                age = col.split('_')[-1].replace('세', '')
                if age.isdigit():
                    age_columns[col] = age
    
    # 연령 컬럼만 선택하고 이름 변경
    age_df = df_processed[['행정구역', '총인구수']].copy()
    
    for old_col, age in age_columns.items():
        # 숫자 값으로 변환 (쉼표 제거)
        if df_processed[old_col].dtype == 'object':
            age_df[age] = df_processed[old_col].str.replace(',', '').astype(int)
        else:
            age_df[age] = df_processed[old_col]
    
    return age_df

def get_top_regions(df, top_n=5):
    """총인구수 기준 상위 N개 지역을 반환합니다."""
    return df.nlargest(top_n, '총인구수')

def create_age_population_chart(df):
    """연령별 인구 선 그래프를 생성합니다."""
    # 데이터를 long format으로 변환
    age_cols = [col for col in df.columns if col.isdigit()]
    age_cols = sorted(age_cols, key=int)
    
    # 멜트 데이터 준비
    chart_data = []
    for _, row in df.iterrows():
        region = row['행정구역']
        for age in age_cols:
            chart_data.append({
                '지역': region,
                '연령': int(age),
                '인구수': row[age]
            })
    
    chart_df = pd.DataFrame(chart_data)
    
    # Altair 차트 생성
    chart = alt.Chart(chart_df).mark_line(
        point=True,
        strokeWidth=2
    ).add_selection(
        alt.selection_single(fields=['지역'])
    ).encode(
        x=alt.X('연령:O', title='연령'),
        y=alt.Y('인구수:Q', title='인구수'),
        color=alt.Color('지역:N', title='지역'),
        tooltip=['지역:N', '연령:O', '인구수:Q']
    ).properties(
        width=800,
        height=500,
        title='상위 5개 지역 연령별 인구 현황'
    ).interactive()
    
    return chart

def main():
    st.set_page_config(
        page_title="연령별 인구현황 분석",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 2025년 6월 연령별 인구현황 분석")
    st.markdown("---")
    
    # 사이드바 설정
    st.sidebar.header("파일 설정")
    
    # 파일 선택 옵션
    file_option = st.sidebar.radio(
        "파일 선택 방법",
        ["기본 파일 사용", "파일 업로드"]
    )
    
    df = None
    
    if file_option == "기본 파일 사용":
        # 기본 파일 경로
        default_file = "202506_202506_연령별인구현황_월간.csv"
        try:
            df = load_csv_file(file_path=default_file)
        except FileNotFoundError:
            st.error(f"기본 파일 '{default_file}'을 찾을 수 없습니다. 파일 업로드를 사용해주세요.")
    
    else:
        # 파일 업로드
        uploaded_file = st.sidebar.file_uploader(
            "CSV 파일을 업로드하세요",
            type=['csv'],
            help="연령별 인구현황 CSV 파일을 업로드해주세요."
        )
        
        if uploaded_file is not None:
            df = load_csv_file(uploaded_file=uploaded_file)
    
    if df is not None:
        # 데이터 전처리
        with st.spinner("데이터를 전처리하고 있습니다..."):
            processed_df = preprocess_data(df)
        
        if processed_df is not None:
            # 상위 5개 지역 추출
            top_regions = get_top_regions(processed_df, 5)
            
            # 메인 컨텐츠
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📈 연령별 인구 분포")
                chart = create_age_population_chart(top_regions)
                st.altair_chart(chart, use_container_width=True)
            
            with col2:
                st.subheader("🏆 상위 5개 지역")
                display_df = top_regions[['행정구역', '총인구수']].copy()
                display_df['총인구수'] = display_df['총인구수'].apply(lambda x: f"{x:,}")
                display_df.index = range(1, len(display_df) + 1)
                st.dataframe(display_df, use_container_width=True)
                
                # 통계 정보
                st.subheader("📊 기본 통계")
                total_population = top_regions['총인구수'].sum()
                avg_population = top_regions['총인구수'].mean()
                
                st.metric("총 인구수 (상위 5개 지역)", f"{total_population:,}")
                st.metric("평균 인구수", f"{avg_population:,.0f}")
            
            # 상세 데이터 테이블
            st.markdown("---")
            st.subheader("📋 상세 데이터")
            
            # 연령 컬럼만 표시
            age_cols = [col for col in top_regions.columns if col.isdigit()]
            age_cols = sorted(age_cols, key=int)
            display_cols = ['행정구역', '총인구수'] + age_cols[:20]  # 처음 20개 연령만 표시
            
            detailed_df = top_regions[display_cols].copy()
            for col in display_cols[1:]:  # 행정구역 제외하고 숫자 포맷 적용
                if col in detailed_df.columns:
                    detailed_df[col] = detailed_df[col].apply(lambda x: f"{x:,}")
            
            st.dataframe(detailed_df, use_container_width=True)
            
            # 다운로드 버튼
            csv = top_regions.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 상위 5개 지역 데이터 다운로드",
                data=csv,
                file_name='top5_regions_age_population.csv',
                mime='text/csv'
            )
    
    else:
        st.info("📁 파일을 선택하거나 업로드해주세요.")
        st.markdown("""
        ### 사용 방법
        1. **기본 파일 사용**: 같은 폴더에 있는 CSV 파일을 자동으로 읽습니다.
        2. **파일 업로드**: 사이드바에서 CSV 파일을 업로드합니다.
        
        ### 지원하는 파일 형식
        - CSV 파일 (UTF-8, EUC-KR, CP949 인코딩)
        - 2025년 6월 연령별 인구현황 데이터
        """)

if __name__ == "__main__":
    main()
