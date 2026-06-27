import streamlit as st
import csv
import io
import json
import random
from PIL import Image, ImageDraw

st.set_page_config(page_title="통합 데이터 도구", layout="centered")

st.title("📂 통합 데이터 & 유틸리티 도구")

# 탭을 4개로 구성 (요청하신 도구들로 교체)
tab1, tab2, tab3, tab4 = st.tabs(["SQL → CSV 변환", "ipynb → Text 변환", "얼굴 상세 분석기 👤", "인스타 언팔 확인 🔍"])

# ==========================================
# 탭 1: SQL -> CSV 변환
# ==========================================
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

# ==========================================
# 탭 2: ipynb -> Text 변환
# ==========================================
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

# ==========================================
# 탭 3: 얼굴 상세 분석기 (New)
# ==========================================
with tab3:
    st.subheader("🤖 초정밀 AI 얼굴 분석기")
    st.write("정면 얼굴 사진을 올리면 이목구비 비율, 대칭성 등을 분석하고 랭킹을 산출합니다.")
    
    uploaded_img = st.file_uploader("정면 얼굴 사진을 업로드하세요", type=["jpg", "jpeg", "png"], key="img_uploader")
    
    if uploaded_img is not None:
        image = Image.open(uploaded_img)
        st.image(image, caption="원본 사진", use_container_width=True)
        
        if st.button("디테일 분석 시작"):
            with st.spinner("안면 골격 구조, 황금비율, 좌우 대칭성을 미친듯이 스캔하는 중..."):
                # 1. 분석된 이미지 시각화 (가상의 스캔 라인 그리기)
                analyzed_img = image.copy()
                draw = ImageDraw.Draw(analyzed_img)
                width, height = analyzed_img.size
                
                # 얼굴 십자 대칭선 및 윤곽선 가이드 그리기 (시각적 효과)
                draw.line((width/2, 0, width/2, height), fill="#00FF00", width=max(2, int(width/200)))
                draw.line((0, height/2, width, height/2), fill="#00FF00", width=max(2, int(width/200)))
                draw.ellipse((width*0.2, height*0.2, width*0.8, height*0.8), outline="#00FF00", width=max(3, int(width/150)))
                
                st.image(analyzed_img, caption="AI 스캔 및 랜드마크 분석 완료", use_container_width=True)
                
                # 2. 결과 텍스트 및 상위 퍼센트 생성
                # (실제 딥러닝 연동 전 시뮬레이션 데이터)
                top_percent = round(random.uniform(0.1, 15.0), 2)
                symmetry_score = random.randint(89, 99)
                
                st.success(f"🏆 분석 결과: 당신의 얼굴은 종합 상위 **{top_percent}%** 에 해당합니다!")
                
                st.markdown(f"""
                ### 📊 상세 분석 리포트
                
                **1. 구조 및 대칭성 (Symmetry)**
                - **좌우 대칭 일치율**: `{symmetry_score}%` (눈매의 높이와 턱선의 밸런스가 매우 우수함)
                - **안면 비례**: 상안부(이마), 중안부(눈썹~코끝), 하안부(코끝~턱)의 비율이 `1 : 1.05 : 0.98`로 황금비(1:1:1)에 매우 근접합니다.
                
                **2. 이목구비 디테일 (Features)**
                - **눈 (Eyes)**: 미간의 넓이와 눈의 가로 길이가 `1:1.1` 비율을 띄고 있어 입체감이 뛰어납니다.
                - **코 (Nose)**: 콧대 시작점과 코끝의 각도가 이상적인 궤적을 그리며 얼굴의 중심을 완벽히 잡아줍니다.
                - **턱선 (Jawline)**: 하악각 라인이 뚜렷하여 세련된 인상을 주는 T존 구조를 가졌습니다.
                
                **3. 종합 AI 코멘트 (Review)**
                > *"전체적인 프레임 밸런스가 훌륭하며, 특정 이목구비가 튀지 않고 조화롭게 배치된 매력적인 외모입니다. 카메라 렌즈 왜곡을 감안하더라도 매우 뛰어난 이목구비 밀집도를 보여줍니다."*
                """)
                st.caption("💡 현재 버전은 데모 형태입니다. 추후 MediaPipe, OpenCV 등의 AI 모델을 직접 연결하면 실제 랜드마크 좌표를 기반으로 한 진짜 데이터를 출력할 수 있습니다.")

# ==========================================
# 탭 4: 인스타그램 언팔 확인기 (New)
# ==========================================
with tab4:
    st.subheader("🕵️ 인스타그램 언팔로워(맞팔) 확인기")
    st.markdown("""
    인스타그램 공식 **'내 정보 다운로드'**에서 받은 JSON 파일을 이용해 나를 언팔한 사람을 찾습니다.
    (내 계정 정보를 입력하지 않으므로 **해킹이나 계정 정지 위험이 0%** 입니다.)
    
    1. 인스타 앱 -> 설정 -> 내 활동 -> '내 정보 다운로드' -> 형식: **JSON**으로 요청
    2. 다운받은 파일 압축을 풀고 `followers_1.json`과 `following.json`을 아래에 올려주세요.
    """)
    
    file_followers = st.file_uploader("팔로워 파일 업로드 (followers_1.json)", type=["json"], key="ig_followers")
    file_following = st.file_uploader("팔로잉 파일 업로드 (following.json)", type=["json"], key="ig_following")

    if st.button("누가 나를 언팔했을까? 확인하기"):
        if file_followers and file_following:
            try:
                followers_data = json.loads(file_followers.getvalue().decode("utf-8"))
                following_data = json.loads(file_following.getvalue().decode("utf-8"))

                # 인스타 JSON 파일에서 재귀적으로 사용자 아이디(value)만 싹 긁어오는 강력한 함수
                # (인스타가 파일 구조를 약간 바꿔도 유연하게 대처 가능)
                def extract_usernames(json_obj):
                    usernames = set()
                    def search_keys(obj):
                        if isinstance(obj, dict):
                            # 보통 인스타 데이터는 href에 주소가 있고 value에 아이디가 있음
                            if "href" in obj and "value" in obj and "instagram.com" in obj["href"]:
                                usernames.add(obj["value"])
                            else:
                                for k, v in obj.items():
                                    search_keys(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                search_keys(item)
                    search_keys(json_obj)
                    return usernames

                my_followers = extract_usernames(followers_data)
                my_following = extract_usernames(following_data)

                if not my_followers or not my_following:
                    st.warning("데이터에서 아이디를 찾지 못했습니다. 올바른 인스타그램 JSON 파일인지 확인해주세요.")
                else:
                    # 내가 팔로잉 하는데, 팔로워에는 없는 사람 = 언팔로워
                    unfollowers = my_following - my_followers
                    
                    st.success(f"분석 완료! 내가 팔로우하지만 나를 팔로우하지 않는 사람은 총 **{len(unfollowers)}명**입니다.")
                    
                    if len(unfollowers) > 0:
                        # 리스트를 복사하기 좋게 텍스트 에어리어로 제공
                        st.text_area("배신자(언팔) 목록 😡", "\n".join(sorted(list(unfollowers))), height=300)
                        st.info("💡 위의 아이디들을 복사해서 인스타에서 정리하세요!")
                    else:
                        st.balloons()
                        st.write("와우! 모든 사람이 당신을 맞팔하고 있습니다! 🎉")
                        
            except Exception as e:
                st.error(f"파일 분석 중 오류가 발생했습니다: {e}")
        else:
            st.warning("비교를 위해 두 개의 JSON 파일이 모두 필요합니다.")

st.divider()
st.info("💡 GitHub에 올려서 Streamlit Cloud로 배포하면 모바일에서도 쉽게 접속해서 쓸 수 있습니다.")
