import streamlit as st
import google.generativeai as genai
import pdfplumber
import requests
import datetime
import urllib.parse
import pandas as pd
import time
import urllib3

# 정부 사이트 SSL 인증서 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# ⚙️ 1. 기본 설정 및 API 키
# ==========================================
st.set_page_config(page_title="마이티시스템 입찰 플랫폼", layout="wide")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
KONEPS_API_KEY = "fc9942134c063694eeb5dad340a314eec93995f86031e3653cddb5d4d38dfbd3"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 👤 2. 마이티시스템 AI 프로필
# ==========================================
mighty_profile = """
당신은 '마이티시스템'의 입찰 담당 전문 AI 비서입니다. 
아래의 우리 회사 자격 요건을 공고문과 1:1로 대조하여 입찰 적격 여부를 분석해 주세요.

[1. 조달청 등록 및 기본 자격]
- 나라장터 경쟁입찰참가자격등록 업체 (정상)
- 소기업/소상공인 (중소기업확인서 보유)
- 기업신용평가등급: BBO (유효기간 내)

[2. 등록 업종 및 시공능력]
- 정보통신공사업 (업종코드: 0036) / 시공능력평가액: 5,595,600,000원
- 소프트웨어사업자(패키지소프트웨어개발.공급사업) (업종코드: 1426)
- 소프트웨어사업자(컴퓨터관련서비스사업) (업종코드: 1468)
- 소프트웨어사업자(데이터베이스제작및검색서비스사업) (업종코드: 1470)

[3. 제조물품 (직생 보유)] 8111229901(SW유지지원), 8111159801(패키지SW), 8111159901(정보시스템개발), 8111179901(정보인프라구축), 8111181101(운영위탁), 8111189901(정보시스템유지관리) 등
[4. 공급물품] 4321150301(노트북), 4320180201(디스크어레이), 4321150102(컴퓨터서버), 4322261201(네트워크스위치) 등
[5. 공장등록] 판교이노베이션랩 지식산업센터 (성남시 소재)

[분석 및 출력 가이드]
0. 📋 [공고 기본 정보]: 공고명, 입찰공고번호, 수요기관을 상단에 명시.
1. [참여 가능 여부]: 🟢가능 / 🟡조건부 / 🔴불가 중 판정하여 크게 표시.
2. [자격 매칭 리스트]: 업종코드, 물품번호(품명), 시평액, 직생 여부가 일치하는지 '통과/확인필요'로 표시.
3. [제한 사항 경고]: 지역 제한, 실적 제한 여부 요약.
4. [행정 및 주의사항]: 투찰 마감 시간, 제안서 제출 방식 등 요약.
"""

# ==========================================
# 🌐 3. UI 및 메인 로직 구성 (상하 분할)
# ==========================================
st.title("🚀 마이티시스템 올인원 입찰 플랫폼")
st.markdown("---")

# ------------------------------------------
# ⬇️ 위쪽 화면 (1단계): 나라장터 실시간 공고 검색기
# ------------------------------------------
st.header("📊 1단계: 맞춤 공고 검색")
st.write("마이티시스템의 주요 키워드가 포함된 최근 7일 공고를 수집합니다.")

if "bids_df" not in st.session_state:
    st.session_state.bids_df = None

if st.button("🔍 나라장터 실시간 검색 실행", type="primary"):
    with st.status("조달청 서버에서 공고를 가져오는 중...", expanded=True) as status:
        keywords = ['정보시스템', '전산시스템', '서버', '스토리지', '인프라', '유지관리', '유지보수']
        today = datetime.datetime.now()
        start_date = (today - datetime.timedelta(days=7)).strftime('%Y%m%d0000')
        end_date = today.strftime('%Y%m%d2359')
        
        urls = {
            "물품": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoThngPPSSrch",
            "용역": "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        all_bids = []

        for kind, base_url in urls.items():
            st.write(f"📂 **{kind} 분야** 검색 중...")
            for kw in keywords:
                encoded_kw = urllib.parse.quote(kw)
                req_url = f"{base_url}?ServiceKey={KONEPS_API_KEY}&numOfRows=30&pageNo=1&inqryDiv=1&inqryBgnDt={start_date}&inqryEndDt={end_date}&bidNtceNm={encoded_kw}&type=json"
                try:
                    res = requests.get(req_url, headers=headers, timeout=15, verify=False)
                    if res.status_code == 200:
                        data = res.json()
                        if 'response' in data and 'header' in data['response']:
                            if data['response']['header'].get('resultCode') == '00':
                                items = data['response']['body'].get('items', [])
                                for item in items:
                                    all_bids.append({
                                        '상세링크': item.get('bidNtceDtlUrl', ''), 
                                        '분류': kind,                  
                                        '공고명': item.get('bidNtceNm', ''),
                                        '수요기관': item.get('ntceInsttNm', ''),
                                        '마감일시': item.get('bidClseDt', ''),
                                        '공고번호': item.get('bidNtceNo', '')
                                    })
                    time.sleep(0.3)
                except Exception as e:
                    pass
        
        if all_bids:
            df = pd.DataFrame(all_bids)
            df = df.drop_duplicates(subset=['공고번호'], keep='first')
            st.session_state.bids_df = df.sort_values(by='마감일시', ascending=True)
            status.update(label=f"✅ 수집 완료! (총 {len(st.session_state.bids_df)}건)", state="complete", expanded=False)
        else:
            status.update(label="❌ 조건에 맞는 공고가 없습니다.", state="error")
            st.session_state.bids_df = None

if st.session_state.bids_df is not None:
    st.dataframe(
        st.session_state.bids_df,
        use_container_width=True,
        height=400,
        column_config={
            "상세링크": st.column_config.LinkColumn(
                "상세보기", 
                display_text="👉 이동하기", 
                help="클릭하면 나라장터 공고 원본 페이지가 새 창으로 열립니다."
            ),
            "공고명": st.column_config.TextColumn("공고명", width="large")
        }
    )
    
    csv = st.session_state.bids_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 엑셀(CSV) 파일로 다운로드",
        data=csv,
        file_name=f"마이티시스템_입찰목록_{datetime.date.today()}.csv",
        mime="text/csv",
    )

# ------------------------------------------
# 구역을 나누는 시각적 구분선
st.markdown("<br><hr><br>", unsafe_allow_html=True)
# ------------------------------------------

# ------------------------------------------
# ⬇️ 아래쪽 화면 (2단계): AI 입찰 공고서(PDF) 분석기
# ------------------------------------------
st.header("🤖 2단계: AI 입찰 자격 분석")
st.write("위 표에서 '이동하기'를 눌러 원본을 확인하고, 다운받은 PDF 공고문을 올려주세요.")

uploaded_file = st.file_uploader("입찰공고서 PDF 업로드", type="pdf")

if uploaded_file is not None:
    with st.spinner("마이티시스템 스펙과 공고문을 정밀 대조 중입니다..."):
        try:
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            if text.strip():
                prompt = mighty_profile + "\n\n[입찰공고서 내용]\n" + text
                response = model.generate_content(prompt)
                
                st.success("✅ 분석 완료!")
                with st.container(border=True):
                    st.markdown(response.text)
            else:
                st.error("PDF에서 텍스트를 읽을 수 없습니다. (스캔본 여부 확인)")
                
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
