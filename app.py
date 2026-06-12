import streamlit as st
import csv
import io
import json
import os
import tempfile
import yt_dlp

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
    st.write("유튜브 영상 링크를 입력하고 원하는 화질이나 음질을 선택해 다운로드하세요.")
    
    url = st.text_input("유튜브 영상 링크(URL)를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")
    
    # 다운로드 형식 및 화질/음질 동적 선택
    format_choice = st.radio("다운로드 형식 선택", ["MP4 (영상)", "MP3 (음원)"], horizontal=True)
    
    if format_choice == "MP4 (영상)":
        quality_choice = st.selectbox(
            "🎥 영상 화질 선택 (영상이 해당 화질을 지원하지 않으면 가능한 최고 화질로 자동 조정됩니다)", 
            ["최고 화질 (Best)", "1080p (FHD)", "720p (HD)", "480p", "360p"]
        )
    else:
        quality_choice = st.selectbox(
            "🎵 음원 품질 선택", 
            ["320kbps (최상 - 추천)", "192kbps (고음질)", "128kbps (일반)"]
        )
    
    if st.button("변환 및 다운로드 준비"):
        # URL의 지저분한 공유 파라미터(?si=...) 제거
        clean_url = url.split("?si=")[0] if "?si=" in url else url
        
        if not clean_url:
            st.warning("유튜브 링크를 입력해주세요.")
        else:
            with st.spinner("영상을 변환 중입니다. (선택한 품질과 파일 크기에 따라 다소 시간이 걸릴 수 있습니다)"):
                try:
                    temp_dir = tempfile.mkdtemp()
                    
                    # 🚀 해결책 1: 강력한 403 에러 우회 옵션
                    ydl_opts = {
                        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'nocheckcertificate': True,  # SSL 인증서 검사 무시
                        'extractor_args': {
                            # 클라이언트를 안드로이드 + 스마트 TV 조합으로 속임
                            'youtube': ['player_client=tv,android', 'player_skip=webpage'] 
                        },
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        }
                    }
                    
                    # 🚀 품질 옵션 설정
                    if format_choice == "MP3 (음원)":
                        ydl_opts['format'] = 'bestaudio/best'
                        bitrate = quality_choice.split("kbps")[0] 
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': bitrate,
                        }]
                    else:
                        if quality_choice == "최고 화질 (Best)":
                            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                        else:
                            height = quality_choice.split("p")[0]
                            ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
                    
                    # 다운로드 실행
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(clean_url, download=True)
                        
                        downloaded_file = None
                        for f in os.listdir(temp_dir):
                            downloaded_file = os.path.join(temp_dir, f)
                            break
                    
                    # 파일 제공
                    if downloaded_file and os.path.exists(downloaded_file):
                        file_name = os.path.basename(downloaded_file)
                        with open(downloaded_file, "rb") as file:
                            st.success("✨ 변환이 완료되었습니다! 아래 버튼을 눌러 저장하세요.")
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
