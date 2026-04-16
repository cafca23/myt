import streamlit as st
import google.generativeai as genai
import pdfplumber

# 1. API 키 세팅 및 모델 지정
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 💡 차장님 API 키에 맞춰 가장 최신/빠른 2.5 Flash 모델로 지정!
model = genai.GenerativeModel('gemini-2.5-flash')

# 2. 마이티시스템 입찰 스펙 프로필
mighty_profile = """
당신은 '마이티시스템'의 입찰 담당 전문 AI 비서입니다.
우리 회사는 다음과 같은 자격을 보유하고 있습니다:
1. 기업 구분: 중소기업 (중소기업확인서 보유)
2. 필수 면허: 소프트웨어사업자 신고 완료, 정보통신공사업 등록 완료
3. 제조 및 생산: 공장등록확인증 보유 (판교지점), 직접생산확인증명서 보유 (전체)
4. 재무 기준: 기업신용평가등급확인서 보유

업로드된 PDF 공고문에서 '참가 자격'을 찾아 우리 스펙과 대조 분석해 주세요.
출력 시 [참여 가능 여부], [항목별 검증 결과 (통과/불가 사유)], [주의사항 및 추가 확인 필요 실적] 순서로 보기 좋게 정리해 주세요.
"""

# 3. UI 구성
st.set_page_config(page_title="마이티시스템 입찰 분석기", layout="wide")
st.title("📄 마이티시스템 입찰공고서 자동 분석 시스템")
st.markdown("---")
st.write("입찰공고서(PDF)를 업로드하면 마이티시스템의 자격 요건과 대조하여 참여 가능 여부를 1분 안에 판독합니다.")

uploaded_file = st.file_uploader("분석할 입찰공고서 PDF 파일을 업로드하세요.", type="pdf")

if uploaded_file is not None:
    with st.spinner("PDF 문서를 읽고 마이티시스템 자격과 대조 중입니다... 잠시만 기다려주세요."):
        try:
            # 4. PDF 텍스트 추출
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            # 5. AI 분석 요청 및 결과 출력
            if text.strip():
                prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + text
                response = model.generate_content(prompt)
                
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.text)
            else:
                st.error("PDF에서 글자를 읽어올 수 없습니다. 스캔된 이미지(사진) 형태의 PDF인지 확인해 주세요.")
                
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
