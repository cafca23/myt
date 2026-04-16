import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="API 진단기")
st.title("🛠️ Gemini API 모델 진단기")

try:
    # 1. API 키 불러오기
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    st.success("✅ API 키 정상 인식됨!")

    # 2. 사용 가능한 모델 목록 불러오기
    st.subheader("이 API 키로 사용 가능한 텍스트 분석 모델 목록:")
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    if available_models:
        for name in available_models:
            st.write(f"- `{name}`")
            
        st.info("👆 위 목록에 있는 이름 중 하나(예: models/gemini-1.5-flash)를 'models/'를 제외하고 코드에 넣으시면 됩니다.")
    else:
        st.error("사용 가능한 모델이 없습니다. API 키의 권한을 확인해야 합니다.")

except Exception as e:
    st.error(f"❌ 에러 발생: {e}")
