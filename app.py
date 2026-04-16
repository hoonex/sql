import streamlit as st
import csv
import io

st.set_page_config(page_title="SQL to CSV Converter", layout="centered")

st.title("📂 사전 DB 변환기 (SQL → CSV)")
st.write("SQL 덤프 파일에서 단어 데이터를 추출하여 CSV로 변환합니다.")

# 파일 업로더
uploaded_file = st.file_uploader("db.txt 또는 .sql 파일을 업로드하세요", type=["txt", "sql"])

if uploaded_file is not None:
    # 처리 시작 버튼
    if st.button("변환 시작"):
        output = io.StringIO()
        # dictionary.csv와 동일한 형식 설정 (모든 필드 따옴표 처리)
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # 헤더 작성
        headers = ['_id', 'type', 'mean', 'hit', 'flag', 'theme']
        writer.writerow(headers)
        
        # 상태 표시 및 변환 로직
        is_data_block = False
        row_count = 0
        
        try:
            # 파일을 줄 단위로 읽어 메모리 효율적 처리
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            
            for line in stringio:
                # 데이터 시작점 탐색 (kkutu_ko 테이블 기준)
                if line.startswith('COPY kkutu_ko '):
                    is_data_block = True
                    continue
                
                if is_data_block:
                    # 데이터 블록 종료 확인
                    if line.strip() == '\\.':
                        break
                    
                    # 탭으로 구분된 데이터 분리
                    row = line.strip('\n').split('\t')
                    
                    # 컬럼 수가 맞는지 확인 후 기록
                    if len(row) >= 6:
                        writer.writerow(row[:6])
                        row_count += 1
            
            if row_count > 0:
                st.success(f"성공적으로 {row_count:,}개의 단어를 추출했습니다!")
                
                # 결과 파일 다운로드 버튼
                st.download_button(
                    label="변환된 dictionary_full.csv 다운로드",
                    data=output.getvalue(),
                    file_name="dictionary_full.csv",
                    mime="text/csv"
                )
            else:
                st.warning("추출할 데이터를 찾지 못했습니다. 테이블 이름이 'kkutu_ko'인지 확인해주세요.")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

st.divider()
st.info("💡 팁: GitHub에 이 코드를 올리고 Streamlit Cloud에 연결하면 모바일 브라우저에서도 바로 사용 가능합니다.")
