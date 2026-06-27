import streamlit as st
import csv
import io
import json
import zipfile
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image

st.set_page_config(page_title="통합 데이터 도구", layout="centered")

st.title("📂 통합 데이터 & 유틸리티 도구")

tab1, tab2, tab3, tab4 = st.tabs(["SQL → CSV 변환", "ipynb → Text 변환", "얼굴 찐 분석기 👤", "인스타 언팔 확인 🔍"])

# ==========================================
# 탭 1: SQL -> CSV 변환
# ==========================================
with tab1:
    st.subheader("사전 DB 변환기 (SQL → CSV)")
    uploaded_sql = st.file_uploader("db.txt 또는 .sql 파일을 업로드하세요", type=["txt", "sql"], key="sql_uploader")

    if uploaded_sql is not None:
        if st.button("CSV 변환 시작"):
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(['_id', 'type', 'mean', 'hit', 'flag', 'theme'])
            
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
                    st.success(f"{row_count:,}개 단어 추출 성공!")
                    st.download_button("dictionary_full.csv 다운로드", output.getvalue(), "dictionary_full.csv", "text/csv")
            except Exception as e:
                st.error(f"오류: {e}")

# ==========================================
# 탭 2: ipynb -> Text 변환
# ==========================================
with tab2:
    st.subheader("노트북 변환기 (ipynb → Text)")
    uploaded_ipynb = st.file_uploader(".ipynb 파일을 업로드하세요", type=["ipynb"], key="ipynb_uploader")
    
    if uploaded_ipynb is not None:
        if st.button("텍스트 추출 시작"):
            try:
                notebook = json.loads(uploaded_ipynb.getvalue().decode("utf-8"))
                extracted_text = ""
                for i, cell in enumerate(notebook.get("cells", [])):
                    cell_type = cell.get("cell_type", "unknown")
                    source = "".join(cell.get("source", []))
                    extracted_text += f"========== [ {i+1}번 셀 : {cell_type.upper()} ] ==========\n{source}\n\n"
                
                st.success("텍스트 추출 완료!")
                st.text_area("미리보기", extracted_text, height=400)
                st.download_button("추출된 텍스트 다운로드", extracted_text, "extracted.txt", "text/plain")
            except Exception as e:
                st.error(f"오류: {e}")

# ==========================================
# 탭 3: 얼굴 상세 분석기 (MediaPipe AI 적용)
# ==========================================
with tab3:
    st.subheader("🤖 AI 안면 구조 및 랜드마크 분석기")
    st.write("Google MediaPipe AI를 사용하여 이목구비의 실제 좌표를 468개의 랜드마크로 스캔합니다.")
    
    uploaded_img = st.file_uploader("정면 얼굴 사진 업로드", type=["jpg", "jpeg", "png"], key="img_uploader")
    
    if uploaded_img is not None:
        image = Image.open(uploaded_img).convert('RGB')
        
        if st.button("AI 정밀 스캔 시작"):
            with st.spinner("AI 모델이 얼굴 랜드마크를 추출 중입니다..."):
                try:
                    img_array = np.array(image)
                    
                    # MediaPipe 호출 
                    mp_face_mesh = mp.solutions.face_mesh
                    mp_drawing = mp.solutions.drawing_utils
                    mp_drawing_styles = mp.solutions.drawing_styles
                    
                    with mp_face_mesh.FaceMesh(
                        static_image_mode=True, 
                        max_num_faces=1, 
                        refine_landmarks=True, 
                        min_detection_confidence=0.5
                    ) as face_mesh:
                        results = face_mesh.process(img_array)
                        
                        if not results.multi_face_landmarks:
                            st.error("얼굴을 찾을 수 없습니다. 정면이 잘 보이는 사진을 올려주세요.")
                        else:
                            annotated_image = img_array.copy()
                            face_landmarks = results.multi_face_landmarks[0]
                            
                            # 468개 좌표 그리기
                            mp_drawing.draw_landmarks(
                                image=annotated_image,
                                landmark_list=face_landmarks,
                                connections=mp_face_mesh.FACEMESH_TESSELATION,
                                landmark_drawing_spec=None,
                                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                            )
                            mp_drawing.draw_landmarks(
                                image=annotated_image,
                                landmark_list=face_landmarks,
                                connections=mp_face_mesh.FACEMESH_CONTOURS,
                                landmark_drawing_spec=None,
                                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
                            )
                            
                            st.image(annotated_image, caption="AI 랜드마크 스캔 완료", use_container_width=True)
                            
                            # 픽셀 좌표 거리 계산
                            h, w, _ = img_array.shape
                            left_eye = face_landmarks.landmark[33]
                            right_eye = face_landmarks.landmark[263]
                            nose_tip = face_landmarks.landmark[1]
                            chin = face_landmarks.landmark[152]
                            
                            lx, ly = int(left_eye.x * w), int(left_eye.y * h)
                            rx, ry = int(right_eye.x * w), int(right_eye.y * h)
                            nx, ny = int(nose_tip.x * w), int(nose_tip.y * h)
                            cx, cy = int(chin.x * w), int(chin.y * h)
                            
                            eye_distance = np.sqrt((rx - lx)**2 + (ry - ly)**2)
                            nose_to_chin = cy - ny
                            
                            st.success("✅ 실제 AI 안면 분석이 완료되었습니다.")
                            st.markdown(f"""
                            ### 📊 실제 측정 데이터 기반 리포트
                            
                            **1. 감지된 특징점**
                            - 모델이 얼굴에서 총 **468개**의 3D 랜드마크를 성공적으로 인식했습니다.
                            
                            **2. 주요 비율 분석 (Real Data)**
                            - 양 눈의 양끝 픽셀 거리: `{eye_distance:.2f}px`
                            - 코끝에서 턱끝까지의 수직 거리: `{nose_to_chin:.2f}px`
                            - **분석 코멘트**: "MediaPipe 텐서플로우 모델이 얼굴 윤곽과 이목구비 깊이를 정상적으로 추적했습니다."
                            """)
                except Exception as e:
                    st.error(f"MediaPipe 분석 중 오류 발생 (requirements.txt 버전을 확인하세요): {e}")

# ==========================================
# 탭 4: 인스타그램 언팔 확인기 (강력해진 최신버전)
# ==========================================
with tab4:
    st.subheader("🕵️ 인스타그램 언팔로워(맞팔) 자동 분석기")
    st.markdown("인스타그램에서 다운받은 **.zip 파일**을 그대로 업로드하세요. 쪼개진 모든 팔로워 파일을 합쳐서 정확히 분석합니다.")
    
    uploaded_zip = st.file_uploader("인스타 정보 다운로드 파일 (.zip)", type=["zip"], key="ig_zip")

    if st.button("내 ZIP 파일 분석하기"):
        if uploaded_zip:
            try:
                followers_data_list = []
                following_data_list = []
                
                # ZIP 파일 내부의 모든 follower/following 관련 JSON 파일 찾기
                with zipfile.ZipFile(uploaded_zip, 'r') as z:
                    for filename in z.namelist():
                        lower_name = filename.lower()
                        if lower_name.endswith('.json'):
                            if 'follower' in lower_name:
                                with z.open(filename) as f:
                                    followers_data_list.append(json.load(f))
                            elif 'following' in lower_name:
                                with z.open(filename) as f:
                                    following_data_list.append(json.load(f))
                
                if not followers_data_list or not following_data_list:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 데이터가 없습니다. 인스타에서 전체 데이터를 다운받았는지 확인하세요.")
                else:
                    # 인스타 최신/구형 데이터 구조 모두 대응하는 파싱 함수
                    def extract_usernames(json_list):
                        usernames = set()
                        def search_keys(obj):
                            if isinstance(obj, dict):
                                # 최신 인스타 포맷
                                if "string_list_data" in obj and isinstance(obj["string_list_data"], list):
                                    for item in obj["string_list_data"]:
                                        if isinstance(item, dict) and "value" in item:
                                            usernames.add(item["value"])
                                # 구형 인스타 포맷
                                elif "href" in obj and "value" in obj and isinstance(obj["href"], str) and "instagram.com" in obj["href"]:
                                    usernames.add(obj["value"])
                                else:
                                    for k, v in obj.items():
                                        search_keys(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    search_keys(item)
                        
                        for data in json_list:
                            search_keys(data)
                        return usernames

                    my_followers = extract_usernames(followers_data_list)
                    my_following = extract_usernames(following_data_list)

                    unfollowers = my_following - my_followers
                    
                    st.success(f"분석 완료! 내가 팔로우하지만 나를 맞팔하지 않는 사람은 총 **{len(unfollowers)}명**입니다.")
                    
                    if len(unfollowers) > 0:
                        st.text_area("배신자(언팔) 목록 😡", "\n".join(sorted(list(unfollowers))), height=300)
                    else:
                        st.balloons()
                        st.write("와우! 모든 사람이 당신을 맞팔하고 있습니다! 🎉")
                        
            except Exception as e:
                st.error(f"ZIP 파일 분석 중 오류가 발생했습니다: {e}")
        else:
            st.warning("인스타그램에서 다운받은 ZIP 파일을 올려주세요.")
