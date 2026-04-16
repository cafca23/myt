import streamlit as st
import google.generativeai as genai
import pdfplumber

# 1. API 키 세팅 (Secrets 사용)
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# 2. 마이티시스템 입찰 스펙 프로필
mighty_profile = """
당신은 '마이티시스템'의 입찰 담당 전문 AI 비서입니다.
우리 회사는 다음과 같은 자격을 보유하고 있습니다:
- 중소기업 (확인서 보유)
- 소프트웨어사업자 및 정보통신공사업 면허 보유
- 판교지점 공장등록 및 직접생산확인증명서 보유
- 기업신용평가등급확인서 보유

업로드된 PDF 공고문에서 '참가 자격'을 찾아 우리 스펙과 대조 분석해 주세요.
출력 시 [참여 가능 여부], [항목별 검증 결과], [주의사항 및 추가 확인 필요 실적] 순서로 정리해 주세요.
"""

# 3. UI 구성
st.set_page_config(page_title="마이티시스템 입찰 분석기", layout="wide")
st.title("📄 입찰공고서 PDF 분석 시스템")
st.markdown("---")

uploaded_file = st.file_uploader("분석할 입찰공고서 PDF 파일을 업로드하세요.", type="pdf")

if uploaded_file is not None:
    with st.spinner("PDF에서 텍스트를 추출하고 분석 중입니다..."):
        # PDF 텍스트 추출
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        
        if text:
            # AI 분석 요청
            prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + text
            response = model.generate_content(prompt)
            
            st.success("분석이 완료되었습니다!")
            st.markdown(response.text)
        else:
            st.error("PDF에서 텍스트를 읽어올 수 없습니다. 스캔된 이미지 형태의 PDF인지 확인해 주세요.")
