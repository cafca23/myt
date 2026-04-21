import streamlit as st
import google.generativeai as genai
import pdfplumber
import requests
import datetime
import urllib.parse
import pandas as pd
import time
import urllib3
from docx import Document # 보고서 생성용
from io import BytesIO

# 보안 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# ⚙️ 1. 기본 설정 및 API 키
# ==========================================
st.set_page_config(page_title="마이티시스템 입찰 플랫폼 V2", layout="wide")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
KONEPS_API_KEY = "fc9942134c063694eeb5dad340a314eec93995f86031e3653cddb5d4d38dfbd3"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 👤 2. 마이티시스템 고도화 프로필 (실적 없음 반영)
# ==========================================
mighty_profile = """
당신은 '마이티시스템'의 입찰 전문 전략 비서입니다. 
제공된 공고문과 과업지시서를 분석하여 우리 회사의 적격 여부를 진단하십시오.

[우리 회사 자격 요건]
1. 기본: 소기업/소상공인, 신용등급 BBO
2. 면허: 정보통신공사업(0036), SW사업자(1426, 1468, 1470)
3. 시공능력평가액: 5,595,600,000원
4. ★중요 실적 사항★: 
   - 우리 회사는 현재 신규 사업자로 **과거 수행 실적이 전혀 없음(0건)**.
   - 만약 공고문에서 '유사 사업 실적 제한'이나 '단일 건 얼마 이상의 실적'을 요구한다면 무조건 [🔴입찰 불가(실적 미달)]로 판정할 것.

[분석 지시서]
1. [공고 기본 정보]: 번호, 수요기관, 예산(배정예산) 추출.
2. [참여 가능 여부]: 🟢가능 / 🟡조건부(실적 외 만족) / 🔴불가(실적 제한 등) 중 선택.
3. [과업 핵심 요약]: 과업지시서(RFP)를 분석하여 우리가 납품해야 할 장비 스펙이나 기술적 핵심 요구사항 요약.
4. [위험 요소]: 독소 조항, 짧은 납기, 무리한 인력 요구사항 등 추출.
"""

# 보고서 생성 함수
def create_report(analysis_text):
    doc = Document()
    doc.add_heading('마이티시스템 입찰 적격성 분석 보고서', 0)
    doc.add_paragraph(f"분석 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    doc.add_paragraph("-" * 50)
    doc.add_paragraph(analysis_text)
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ==========================================
# 🌐 3. 메인 UI
# ==========================================
st.title("🚀 마이티시스템 입찰 플랫폼 V2 (실적/RFP 분석)")
st.markdown("---")

# --- 1단계: 검색 ---
st.header("📊 1단계: 나라장터 실시간 맞춤 검색")
if "bids_df" not in st.session_state: st.session_state.bids_df = None

if st.button("🔍 맞춤 공고 검색 시작", type="primary"):
    with st.status("공고 수집 중...", expanded=False) as status:
        keywords = ['정보시스템', '전산시스템', '서버', '스토리지', '인프라', '유지관리']
        all_bids = []
        # (검색 로직은 이전과 동일하게 최신 주소 사용)
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y%m%d0000')
        end_date = datetime.datetime.now().strftime('%Y%m%d2359')
        urls = {"물품": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
                "용역": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"}
        
        for kind, base_url in urls.items():
            for kw in keywords:
                encoded_kw = urllib.parse.quote(kw)
                req_url = f"{base_url}?ServiceKey={KONEPS_API_KEY}&numOfRows=30&pageNo=1&inqryDiv=1&inqryBgnDt={start_date}&inqryEndDt={end_date}&bidNtceNm={encoded_kw}&type=json"
                try:
                    res = requests.get(req_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, verify=False)
                    if res.status_code == 200:
                        items = res.json()['response']['body'].get('items', [])
                        for item in items:
                            all_bids.append({
                                '상세링크': item.get('bidNtceDtlUrl', ''), '분류': kind, '공고명': item.get('bidNtceNm', ''),
                                '수요기관': item.get('ntceInsttNm', ''), '마감일시': item.get('bidClseDt', ''), '공고번호': item.get('bidNtceNo', '')
                            })
                except: pass
        
        if all_bids:
            df = pd.DataFrame(all_bids).drop_duplicates(subset=['공고번호']).sort_values(by='마감일시')
            st.session_state.bids_df = df
            status.update(label="✅ 검색 완료", state="complete")

if st.session_state.bids_df is not None:
    st.dataframe(st.session_state.bids_df, use_container_width=True, column_config={"상세링크": st.column_config.LinkColumn("상세보기", display_text="👉 이동")})

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# --- 2단계: 심층 분석 ---
st.header("🤖 2단계: AI 심층 분석 (공고문 + 과업지시서)")
st.info("💡 공고문 PDF와 과업지시서(RFP) PDF를 함께 올리면 더 정확한 분석이 가능합니다.")

col1, col2 = st.columns(2)
with col1:
    notice_file = st.file_uploader("1️⃣ 입찰공고서 업로드", type="pdf")
with col2:
    rfp_file = st.file_uploader("2️⃣ 과업지시서/RFP 업로드 (선택)", type="pdf")

if notice_file:
    if st.button("🧐 AI 적격성 정밀 진단 시작"):
        with st.spinner("모든 문서를 읽고 실적 제한 여부를 검토 중입니다..."):
            full_text = ""
            for f in [notice_file, rfp_file]:
                if f:
                    with pdfplumber.open(f) as pdf:
                        for page in pdf.pages:
                            full_text += page.extract_text() + "\n"
            
            response = model.generate_content(mighty_profile + "\n\n[분석 대상 문서 내용]\n" + full_text)
            st.session_state.analysis_result = response.text
            
            st.success("✅ 진단이 완료되었습니다.")
            with st.container(border=True):
                st.markdown(st.session_state.analysis_result)
            
            # 리포트 다운로드 버튼
            report_data = create_report(st.session_state.analysis_result)
            st.download_button(
                label="📥 분석 결과 보고서(Word) 다운로드",
                data=report_data,
                file_name=f"입찰분석보고서_{datetime.date.today()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
