import streamlit as st
import google.generativeai as genai
import pdfplumber

# 1. API 키 세팅 및 모델 지정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 차장님 API 키에 최적화된 최신 모델 사용
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 마이티시스템 입찰 스펙 프로필 (나라장터 등록증 내용 추가)
mighty_profile = """
당신은 '마이티시스템'의 입찰 담당 전문 AI 비서입니다.
우리 회사는 다음과 같은 자격을 보유하고 있습니다:

1. [조달청 등록] 경쟁입찰참가자격등록증 보유 (나라장터 등록 업체)
2. [기업 구분] 중소기업 (확인서 보유)
3. [필수 면허] 소프트웨어사업자(컴퓨터관련서비스사업), 정보통신공사업 보유
4. [제조 및 생산] 직접생산확인증명서(전체), 공장등록확인증(판교지점) 보유
5. [재무/기타] 기업신용평가등급확인서 보유

업로드된 PDF 공고문에서 '참가 자격'을 찾아 우리 스펙과 대조 분석해 주세요.
특히 다음 사항을 중점적으로 체크해 주세요:
- 조달청 입찰참가자격등록증에 등록된 물품/업종 제한이 있는지
- 직접생산확인증명서의 세부품목번호와 공고문의 요구사항 일치 여부
- 지역제한(경기도/분당 등) 및 실적 제한 여부
"""

# 3. UI 구성
st.set_page_config(page_title="마이티시스템 입찰 분석기", layout="wide")
st.title("🚀 마이티시스템 통합 입찰 분석 시스템")
st.markdown("---")
st.write("조달청 등록증을 포함한 모든 자격 서류가 연동되었습니다. 공고서 PDF를 올려주세요.")

uploaded_file = st.file_uploader("분석할 입찰공고서 PDF 파일을 업로드하세요.", type="pdf")

if uploaded_file is not None:
    with st.spinner("마이티시스템의 모든 면허/자격 요건과 대조 분석 중입니다..."):
        try:
            # PDF 텍스트 추출
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            if text.strip():
                # AI 분석 요청
                prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + text
                response = model.generate_content(prompt)
                
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.text)
            else:
                st.error("PDF에서 텍스트를 읽을 수 없습니다.")
                
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
