import streamlit as st
import csv
import io
import json
import os
import tempfile
import yt_dlp  # 새로 추가된 라이브러리

st.set_page_config(page_title="Data Converter", layout="centered")

st.title("📂 통합 데이터 변환기")

# 탭을 3개로 확장하여 유튜브 기능 추가
tab1, tab2, tab3 = st.tabs(["SQL → CSV 변환", "ipynb → Text 변환", "YouTube 다운로더"])

with tab1:
    st.subheader("사전 DB 변환기 (SQL → CSV)")
    st.write("SQL 덤프 파일에서 단어 데이터를 추출하여 CSV로 변환합니다.")

    uploaded_sql = st.file_uploader("db.txt 또는 .sql 파일을 업로드하세요", type=["txt", "sql"], key="sql_uploader")

    if uploaded_sql is not None:
        if st.button("CSV 변환 시작"):
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            
            headers = ['_id', 'type', 'mean', 'hit', 'flag', 'theme']
            writer.writerow(headers)
            
            is_data_block = False
            row_count = 0
            
            try:
                stringio = io.StringIO(uploaded_sql.getvalue().decode("utf-8"))
                
                for line in stringio:
                    if line.startswith('COPY kkutu_ko '):
                        is_data_block = True
                        continue
                    
                    if is_data_block:
                        if line.strip() == '\\.':
                            break
                        
                        row = line.strip('\n').split('\t')
                        
                        if len(row) >= 6:
                            writer.writerow(row[:6])
                            row_count += 1
                
                if row_count > 0:
                    st.success(f"성공적으로 {row_count:,}개의 단어를 추출했습니다!")
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
                notebook = json.loads(uploaded_ipynb.getvalue().decode("utf-8"))
                extracted_text = ""
                
                for i, cell in enumerate(notebook.get("cells", [])):
                    cell_type = cell.get("cell_type", "unknown")
                    source = "".join(cell.get("source", []))
                    
                    extracted_text += f"========== [ {i+1}번 셀 : {cell_type.upper()} ] ==========\n"
                    extracted_text += source
                    if not source.endswith('\n'):
                        extracted_text += "\n"
                    extracted_text += "\n\n"
                
                st.success("텍스트 추출을 완료했습니다!")
                st.text_area("추출된 텍스트 미리보기", extracted_text, height=400)
                st.download_button(
                    label="추출된 텍스트 파일(.txt) 다운로드",
                    data=extracted_text,
                    file_name="extracted_notebook.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

with tab3:
    st.subheader("유튜브 변환기 (YouTube → MP3/MP4)")
    st.write("유튜브 영상 링크를 입력하면 음원(MP3) 또는 영상(MP4) 파일로 변환하여 다운로드합니다.")
    
    url = st.text_input("유튜브 영상 링크(URL)를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")
    format_choice = st.radio("다운로드 형식 선택", ["MP4 (영상)", "MP3 (음원)"])
    
    if st.button("변환 및 다운로드 준비"):
        if not url:
            st.warning("유튜브 링크를 입력해주세요.")
        else:
            with st.spinner("영상을 변환 중입니다. (파일 크기에 따라 다소 시간이 걸릴 수 있습니다)"):
                try:
                    # 안전한 다운로드를 위한 임시 폴더 생성
                    temp_dir = tempfile.mkdtemp()
                    
                    ydl_opts = {
                        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                    }
                    
                    if format_choice == "MP3 (음원)":
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    else:
                        # 영상과 오디오를 합친 가장 좋은 품질의 MP4를 가져오거나 단일 파일 사용
                        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # 다운로드 실행
                        info = ydl.extract_info(url, download=True)
                        
                        # 다운로드된 파일 찾기
                        downloaded_file = None
                        for f in os.listdir(temp_dir):
                            downloaded_file = os.path.join(temp_dir, f)
                            break
                    
                    if downloaded_file and os.path.exists(downloaded_file):
                        file_name = os.path.basename(downloaded_file)
                        with open(downloaded_file, "rb") as file:
                            st.success("변환이 완료되었습니다! 아래 버튼을 눌러 파일을 저장하세요.")
                            st.download_button(
                                label=f"📥 {file_name} 다운로드",
                                data=file,
                                file_name=file_name,
                                mime="audio/mpeg" if format_choice == "MP3 (음원)" else "video/mp4"
                            )
                    else:
                        st.error("파일 변환에 실패했습니다.")
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다. 링크가 정확한지 확인해 주세요.\n\n에러 내용: {e}")

st.divider()
st.info("💡 팁: GitHub에 이 코드를 올리고 Streamlit Cloud에 연결하면 모바일 브라우저에서도 바로 사용 가능합니다. \n\n⚠️ **주의:** 다운로드한 저작물은 개인 소장용으로만 사용해야 하며, 유튜브 서비스 약관 및 저작권법을 준수해 주세요.")
