import streamlit as st
import csv
import io
import json

st.set_page_config(page_title="Data Converter", layout="centered")

st.title("📂 데이터 변환기")

# 탭 생성해서 두 기능 분리
tab1, tab2 = st.tabs(["SQL → CSV 변환", "ipynb → Text 변환"])

with tab1:
    st.subheader("사전 DB 변환기 (SQL → CSV)")
    st.write("SQL 덤프 파일에서 단어 데이터를 추출하여 CSV로 변환합니다.")

    # 파일 업로더
    uploaded_sql = st.file_uploader("db.txt 또는 .sql 파일을 업로드하세요", type=["txt", "sql"], key="sql_uploader")

    if uploaded_sql is not None:
        # 처리 시작 버튼
        if st.button("CSV 변환 시작"):
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
                stringio = io.StringIO(uploaded_sql.getvalue().decode("utf-8"))
                
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

with tab2:
    st.subheader("노트북 변환기 (ipynb → Text)")
    st.write("Jupyter Notebook 파일의 코드와 마크다운을 칸 구분이 있는 텍스트로 추출합니다.")
    
    uploaded_ipynb = st.file_uploader(".ipynb 파일을 업로드하세요", type=["ipynb"], key="ipynb_uploader")
    
    if uploaded_ipynb is not None:
        if st.button("텍스트 추출 시작"):
            try:
                # ipynb 파일은 JSON 형식이므로 파싱
                notebook = json.loads(uploaded_ipynb.getvalue().decode("utf-8"))
                extracted_text = ""
                
                # 각 셀(cell)을 순회하며 텍스트 추출
                for i, cell in enumerate(notebook.get("cells", [])):
                    cell_type = cell.get("cell_type", "unknown")
                    source = "".join(cell.get("source", []))
                    
                    # 칸 구분을 위한 헤더 추가
                    extracted_text += f"========== [ {i+1}번 셀 : {cell_type.upper()} ] ==========\n"
                    extracted_text += source
                    if not source.endswith('\n'):
                        extracted_text += "\n"
                    extracted_text += "\n\n"
                
                st.success("텍스트 추출을 완료했습니다!")
                
                # 화면에 추출된 텍스트 보여주기 (복사 가능)
                st.text_area("추출된 텍스트 미리보기", extracted_text, height=400)
                
                # txt 파일로 다운로드
                st.download_button(
                    label="추출된 텍스트 파일(.txt) 다운로드",
                    data=extracted_text,
                    file_name="extracted_notebook.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

st.divider()
st.info("💡 팁: GitHub에 이 코드를 올리고 Streamlit Cloud에 연결하면 모바일 브라우저에서도 바로 사용 가능합니다.")
