import streamlit as st
import google.generativeai as genai
# import pdfplumber (PDF 추출용)

# 1. API 키 세팅 (시스템 환경변수로 관리 권장)
genai.configure(api_key="발급받은_API_KEY")
model = genai.GenerativeModel('gemini-1.5-pro')

# 2. 마이티시스템 기본 스펙 (프롬프트로 고정)
mighty_profile = """
우리는 '마이티시스템'이야. 아래 입찰 공고를 보고 우리가 참여 가능한지 분석해줘.
- 본점: 경기도 분당
- 자격: 소프트웨어사업자, 정보통신공사업 면허 보유
- 기업분류: 중소기업
"""

# 3. 웹 화면 UI 구성 (Streamlit)
st.title("🚀 마이티시스템 입찰 분석 봇")
st.write("입찰공고서(PDF)를 올리면 참여 가능 여부를 1분 안에 분석합니다.")

uploaded_file = st.file_uploader("입찰공고서 PDF 업로드", type="pdf")

if uploaded_file is not None:
    # (여기에 PDF에서 텍스트를 추출하는 코드 들어감)
    extracted_text = "임시로 추출된 공고서 텍스트..." 
    
    st.info("AI가 공고서를 분석 중입니다. 잠시만 기다려주세요...")
    
    # 4. AI에게 질문 던지기
    prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + extracted_text
    response = model.generate_content(prompt)
    
    # 5. 결과 화면 출력
    st.success("분석 완료!")
    st.markdown(response.text)
