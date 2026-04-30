import streamlit as st
import pandas as pd

# ==========================================
# 0. 페이지 세팅
# ==========================================
st.set_page_config(page_title="서버 변동 검출기", page_icon="🖥️", layout="wide")

st.title("🖥️ 월간 서버 수량 변동 자동 검출기")
st.write("파일을 드래그해서 넣으면, 파이썬이 알아서 공백을 제거하고 빠진 서버를 찾아냅니다.")
st.divider()

# ==========================================
# 1. 엑셀/CSV 파일 업로드부
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 지난달 서버 리스트 (기준)")
    file_past = st.file_uploader("파일을 올려주세요 (CSV/Excel)", type=['csv', 'xlsx'], key='past')

with col2:
    st.subheader("📅 이번 달 서버 리스트 (비교)")
    file_current = st.file_uploader("파일을 올려주세요 (CSV/Excel)", type=['csv', 'xlsx'], key='current')

# ==========================================
# 2. 데이터 분석 엔진
# ==========================================
if st.button("🚀 변동 내역 스캔 시작!", type="primary", use_container_width=True):
    if file_past is not None and file_current is not None:
        with st.spinner("파일을 뜯어서 서버 이름과 IP를 추출하고 있습니다... 🕵️‍♂️"):
            try:
                # 1) 판다스로 데이터 읽어오기
                if file_past.name.endswith('.csv'):
                    df_past = pd.read_csv(file_past, header=None)
                else:
                    df_past = pd.read_excel(file_past, header=None)
                    
                if file_current.name.endswith('.csv'):
                    df_current = pd.read_csv(file_current, header=None)
                else:
                    df_current = pd.read_excel(file_current, header=None)
                
                # 2) 빈 줄(결측치) 1차 폭파
                df_past = df_past.dropna(subset=[1])
                df_current = df_current.dropna(subset=[1])
                
                # 3) 서버명(열 인덱스 1)과 IP주소(열 인덱스 2)의 공백을 다림질하듯 쫙 폅니다.
                df_past[1] = df_past[1].astype(str).str.strip()
                df_current[1] = df_current[1].astype(str).str.strip()
                
                if 2 in df_past.columns:
                    df_past[2] = df_past[2].astype(str).str.strip()
                else:
                    df_past[2] = "IP 없음"
                    
                if 2 in df_current.columns:
                    df_current[2] = df_current[2].astype(str).str.strip()
                else:
                    df_current[2] = "IP 없음"
                
                # 가짜 서버명('nan' 또는 빈칸) 데이터 프레임에서 완전히 삭제
                df_past = df_past[~df_past[1].isin(['nan', ''])]
                df_current = df_current[~df_current[1].isin(['nan', ''])]
                
                # 4) 서버명만 추출해서 세트(Set)로 차집합 계산!
                past_servers = set(df_past[1])
                current_servers = set(df_current[1])
                
                missing_names = past_servers - current_servers
                new_names = current_servers - past_servers
                
                # 5) 💡 핵심: 빠지거나 새로 들어온 서버 이름을 가지고 원본에서 IP까지 세트로 묶어옵니다.
                df_missing = df_past[df_past[1].isin(missing_names)][[1, 2]]
                df_missing.columns = ["서버명", "IP 주소"]
                df_missing.reset_index(drop=True, inplace=True)
                df_missing.index = df_missing.index + 1
                
                df_new = df_current[df_current[1].isin(new_names)][[1, 2]]
                df_new.columns = ["서버명", "IP 주소"]
                df_new.reset_index(drop=True, inplace=True)
                df_new.index = df_new.index + 1
                
                # ==========================================
                # 3. 결과 출력부
                # ==========================================
                st.divider()
                st.header("📊 스캔 결과 보고서")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("지난달 총 수량", f"{len(past_servers)} 대")
                m2.metric("이번 달 총 수량", f"{len(current_servers)} 대", delta=f"{len(current_servers) - len(past_servers)} 대")
                m3.metric("🚨 빠진 서버 (확인 필요)", f"{len(missing_names)} 대", delta_color="inverse")
                m4.metric("✨ 신규 추가 서버", f"{len(new_names)} 대")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.error(f"🚨 **빠진 서버 목록 ({len(missing_names)}대)**")
                    if not df_missing.empty:
                        st.dataframe(df_missing, use_container_width=True)
                    else:
                        st.info("빠진 서버가 없습니다. (전원 생존!)")
                        
                with res_col2:
                    st.success(f"✨ **신규 추가 서버 목록 ({len(new_names)}대)**")
                    if not df_new.empty:
                        st.dataframe(df_new, use_container_width=True)
                    else:
                        st.info("새로 추가된 서버가 없습니다.")
                        
            except Exception as e:
                st.error(f"🚨 파일 형식이 예상과 다릅니다. 에러 원인: {e}")
    else:
        st.warning("⚠️ 파일을 모두 업로드해주세요!")
