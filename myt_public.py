import streamlit as st
import google.generativeai as genai

# 1. API 키 세팅 (User 지침에 따라 GEMINI_API_KEY 사용)
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro')

# 2. 마이티시스템 입찰 스펙 프로필 (올려주신 증명서 기반)
# ※ 주의: 직접생산증명의 세부 '세부품목번호'와 신용평가 '정확한 등급'은 공고마다 기준이 다르므로 AI가 확인 요소로 짚어주도록 셋팅했습니다.
mighty_profile = """
당신은 '마이티시스템'의 입찰 담당 전문 AI 비서입니다.
아래는 우리 회사의 공식 자격 및 보유 증명서 내역입니다. 업로드되는 입찰공고서의 '입찰 참가자격'을 꼼꼼히 대조하여 우리가 입찰에 참여할 수 있는지 분석해 주세요.

[마이티시스템 기본 보유 자격]
1. 기업 구분: 중소기업 (중소기업확인서 보유)
2. 필수 면허: 
   - 소프트웨어사업자 신고 완료
   - 정보통신공사업 등록 완료
3. 제조 및 생산: 
   - 공장등록확인증 보유 (판교지점)
   - 직접생산확인증명서 보유 (전체)
4. 재무 기준: 기업신용평가등급확인서 보유

[분석 지침 및 출력 형식]
1. 합격 여부 요약: 🟢 참여 가능 / 🟡 조건부 가능(확인필요) / 🔴 참여 불가 중 하나로 시작할 것.
2. 참가 자격 검증: 공고서에서 요구하는 자격 중 우리가 충족하는 항목(소프트웨어, 정보통신, 중소기업 등)을 매칭하여 '통과'로 표시할 것.
3. ⚠️ 핵심 확인 필요 사항: 
   - 직접생산확인증명서의 '특정 세부품목번호'가 일치해야 하는지 파악하여 알려줄 것.
   - 신용평가등급의 '요구 하한선(예: B- 이상 등)'이 있다면 발췌해서 알려줄 것.
   - 지역 제한(본점 소재지)이나 특정 실적 제한(최근 X년 내 X억 이상)이 있다면 반드시 경고해 줄 것.
4. 설명회 등 기타: 제안요청서 설명회 참석 여부 등 일정이 있다면 요약해 줄 것.
"""

# 3. 웹 화면 UI 구성
st.set_page_config(page_title="마이티시스템 입찰 분석기", layout="wide")
st.title("🚀 마이티시스템 입찰 참가 자격 분석 봇")
st.markdown("---")
st.write("📂 **업로드 가능 파일:** 입찰공고서 텍스트 복사 붙여넣기 (추후 PDF 업로드 기능 연동 가능)")

# 현재는 테스트를 위해 텍스트 입력창으로 구성 (PDF 파서 연동 전 단계)
notice_text = st.text_area("입찰공고서의 '참가자격' 부분을 여기에 복사해서 붙여넣어 주세요.", height=300)

if st.button("참여 가능 여부 분석하기"):
    if notice_text.strip() == "":
        st.warning("입찰공고서 내용을 입력해 주세요.")
    else:
        with st.spinner("마이티시스템 자격 요건과 대조하여 분석 중입니다..."):
            # 4. AI에게 프로필과 공고서 내용 전달
            prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + notice_text
            response = model.generate_content(prompt)
            
            # 5. 결과 출력
            st.success("분석 완료!")
            st.markdown(response.text)
