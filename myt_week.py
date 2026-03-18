import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 0. AI 세팅
# ==========================================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

st.set_page_config(page_title="주간업무보고 생성기", page_icon="📝")

st.title("📝 3초 컷! 주간업무보고 생성기")
st.write("매일 쓴 일일보고(.txt) 파일들을 한 번에 드래그해서 올리면, 임원진 보고용 주간보고서로 세탁해 드립니다.")
st.divider()

# ==========================================
# 1. 파일 업로드 영역
# ==========================================
uploaded_files = st.file_uploader("📂 일주일 치 '일일업무보고 .txt' 파일들을 모두 선택해서 올려주세요!", type="txt", accept_multiple_files=True)

if uploaded_files:
    st.info(f"✅ 총 {len(uploaded_files)}개의 일일보고 파일이 정상적으로 업로드되었습니다.")
    
    if st.button("✨ 주간업무보고 굽기", type="primary", use_container_width=True):
        with st.spinner("흩어진 일일보고들을 분석하여 고객사별로 합치고 정제하는 중입니다... ⚙️"):
            
            combined_text = ""
            for file in uploaded_files:
                combined_text += f"\n\n--- [{file.name}] ---\n"
                
                # 💡 [핵심 해결책] UTF-8로 먼저 읽어보고, 실패하면 CP949(한국어 윈도우 방식)로 읽도록 예외 처리!
                try:
                    content = file.getvalue().decode("utf-8")
                except UnicodeDecodeError:
                    content = file.getvalue().decode("cp949", errors="ignore")
                    
                combined_text += content
                
            prompt = f"""
            당신은 최고의 IT 인프라 엔지니어이자 보고서 작성의 달인입니다.
            다음은 일주일 동안 흩어져서 작성된 여러 개의 '일일업무보고' 내용입니다.

            {combined_text}

            이 내용들을 종합하여 완벽한 '주간업무보고'를 작성해 주세요.

            [🚨 매우 중요한 작성 규칙]
            1. [인사말]: 도입부는 반드시 "안녕하세요. 정의랑 입니다.\n주간업무보고 드립니다." 로 고정하세요.
            2. [고객사별 그룹화]: 흩어진 업무들을 '1. KT알파 목동', '2. KT알파 분당', '3. 경기대학교' 등 사이트(고객사)별로 묶어서 넘버링하세요.
            3. [개조식 포맷팅]: 업무 내용은 줄글이 아니라, 글머리기호(*)를 사용하고 끝맺음은 "~함", "~됨", "~예정", "~확인" 등 보고용 명사형/개조식으로 깔끔하게 포맷팅하세요.
            4. [히스토리 요약]: 매일 반복된 트러블슈팅(예: 장애 발생 -> 분석 -> 조치 완료)은 일자별로 적지 말고, 하나의 매끄러운 진행 흐름으로 묶어서 요약하세요.
            5. [차주 일정 통합]: 각 일일보고 하단에 흩어져 있는 "내일은 ~ 방문합니다" 내용들을 모두 취합하여 중복을 제거한 뒤, 보고서 맨 마지막에 "다음주는 ~ 방문합니다." 라고 깔끔하게 한 줄로 요약해 주세요.
            6. [비즈니스 톤앤매너]: 인사말이나 군더더기 감정 표현은 모두 빼고, 오직 각 잡힌 엔터프라이즈급 인프라 업무 보고서의 톤을 유지하세요.
            """
            
            try:
                response = model.generate_content(prompt)
                st.success("🎉 완벽한 주간업무보고가 완성되었습니다! 바로 복사해서 결재 올리세요!")
                with st.container(border=True):
                    st.markdown(response.text)
            except ResourceExhausted:
                st.error("🚨 AI 과부하 상태입니다. 딱 1분만 기다렸다가 다시 눌러주세요!")
            except Exception as e:
                st.error(f"🚨 텍스트 변환 중 오류가 발생했습니다: {e}")
