import streamlit as st
import csv
import io
import json
import os
import tempfile
import yt_dlp
import re

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
        clean_url = url.split("?si=")[0] if "?si=" in url else url
        
        if not clean_url:
            st.warning("유튜브 링크를 입력해주세요.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent_str = d.get('_percent_str', '0.0%')
                    clean_percent = re.sub(r'\x1b\[[0-9;]*m', '', percent_str).replace('%', '').strip()
                    try:
                        percent = float(clean_percent)
                        progress_bar.progress(int(percent))
                        status_text.info(f"다운로드 진행 중... {percent}% 완료")
                    except ValueError:
                        pass
                elif d['status'] == 'finished':
                    progress_bar.progress(100)
                    status_text.success("다운로드 완료! 파일을 병합/변환하는 중입니다. 잠시만 기다려주세요...")

            with st.spinner("서버와 연결 중입니다..."):
                try:
                    temp_dir = tempfile.mkdtemp()
                    
                    # 🚀 초강력 403 에러 우회 옵션 (캐시 삭제, 다중 클라이언트, IP 강제, 쿠키 감지)
                    ydl_opts = {
                        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'nocheckcertificate': True,
                        'source_address': '0.0.0.0', # IPv4 강제 (클라우드 IPv6 차단 회피)
                        'rm_cachedir': True, # yt-dlp의 밴 기록 캐시를 매번 삭제
                        'geo_bypass': True, # 지역 제한 우회
                        'extractor_args': {
                            'youtube': ['player_client=mweb,android,tv', 'player_skip=webpage,configs'] 
                        },
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                        },
                        'sleep_interval_requests': 1,
                        'progress_hooks': [progress_hook],
                    }
                    
                    # 🚀 [가장 중요] 쿠키 파일이 같은 폴더에 있으면 무조건 적용
                    if os.path.exists("cookies.txt"):
                        ydl_opts['cookiefile'] = 'cookies.txt'
                    
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
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(clean_url, download=True)
                        
                        downloaded_file = None
                        for f in os.listdir(temp_dir):
                            downloaded_file = os.path.join(temp_dir, f)
                            break
                    
                    if downloaded_file and os.path.exists(downloaded_file):
                        file_name = os.path.basename(downloaded_file)
                        with open(downloaded_file, "rb") as file:
                            status_text.success("✨ 변환 및 준비가 모두 완료되었습니다! 아래 버튼을 눌러 저장하세요.")
                            st.download_button(
                                label=f"📥 {file_name} 다운로드",
                                data=file,
                                file_name=file_name,
                                mime="audio/mpeg" if format_choice == "MP3 (음원)" else "video/mp4"
                            )
                    else:
                        status_text.error("파일 변환에 실패했습니다.")
                        
                except Exception as e:
                    status_text.empty() 
                    st.error(f"오류가 발생했습니다. 링크가 정확한지 확인해 주세요.\n\n에러 내용: {e}")

st.divider()
st.info("💡 **마지막 팁:** 이 코드마저 Streamlit 서버에서 막힌다면, IP 자체가 영구 차단된 것입니다. 크롬 확장프로그램으로 유튜브 `cookies.txt`를 추출해 코드가 있는 폴더에 올리시거나, **본인의 컴퓨터에서 직접 실행**하시는 것 외에는 방법이 없습니다.")
