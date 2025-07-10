import streamlit as st
import pandas as pd
import altair as alt
import os

st.title('📊 2025년 6월 연령별 인구 현황 분석')

# 파일 업로드 및 기본 파일 로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")
file_path = 'data.csv' if not uploaded_file else None

df = None
encoding_used = None  # 사용할 인코딩 저장

def try_read_file(file_obj, encodings):
    """여러 인코딩을 시도하여 파일 읽기"""
    for encoding in encodings:
        try:
            df = pd.read_csv(file_obj, encoding=encoding, nrows=100)
            if not df.empty:
                return df, encoding
        except Exception:
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

# 디버그: 원본 데이터 구조 확인 (인코딩 사용)
with st.expander("🔍 원본 데이터 구조 확인"):
    try:
        # 디버그 시 여러 인코딩 재시도
        for encoding in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']:
            try:
                sample = pd.read_csv(
                    uploaded_file if uploaded_file else file_path, 
                    nrows=3, 
                    encoding=encoding
                )
                st.write("성공 인코딩:", encoding)
                st.write("원본 컬럼명:", sample.columns.tolist())
                st.write("데이터 샘플:", sample)
                break
            except Exception:
                continue
        else:
            st.warning("모든 인코딩 시도 실패: 파일 손상 또는 지원되지 않는 인코딩일 수 있음")
    except Exception as e:
        st.warning(f"디버그 정보 로드 실패: {str(e)}")

# 전체 데이터 로드
try:
    df_full = pd.read_csv(
        uploaded_file if uploaded_file else file_path, 
        encoding=encoding_used
    )
except Exception as e:
    st.error(f"데이터 로드 실패: {str(e)}. 파일 형식을 확인해주세요.")
    st.stop()

# 나머지 코드는 이전과 동일...
