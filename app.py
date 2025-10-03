import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import re

# .env 파일에서 API 키를 불러와 환경변수에 설정
load_dotenv()

# --- 비밀번호 확인 함수 ---
def check_password():
    password = st.text_input("비밀번호를 입력하세요", type="password")
    correct_password = os.environ.get("PASSWORD") or st.secrets.get("PASSWORD")
    if password == correct_password:
        return True
    elif password:
        st.warning("비밀번호가 틀렸습니다.")
    return False

# --- Perplexity API 클라이언트 설정 ---
try:
    api_key = os.environ.get("PERPLEXITY_API_KEY") or st.secrets.get("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError("API 키가 로드되지 않았습니다. .env 또는 Streamlit Secrets를 확인해주세요.")
    
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
except Exception as e:
    st.error(f"API 클라이언트 설정 중 오류가 발생했습니다: {e}")
    client = None

# --- Streamlit UI 구성 ---
st.set_page_config(page_title="AI 증상 진단기", page_icon="🩺")
st.title("🩺 AI 증상 진단 프로토타입")

if client and check_password():
    st.info("AI 어시스턴트에게 증상을 설명해주세요. 예상 질병과 대응 방법을 알려드립니다.")
    
    with st.form("diagnosis_form"):
        st.subheader("1. 환자 정보")
        cols = st.columns(2)
        age = cols[0].number_input("나이", min_value=1, max_value=120, value=25)
        gender_display = cols[1].selectbox("성별", ["남성", "여성", "기타"])
        history = st.text_area("과거 병력, 복용 약, 알레르기 등 (선택 사항)")

        st.subheader("2. 주요 증상")
        symptom_category = st.radio(
            "가장 불편한 증상의 종류를 선택하세요.",
            ["호흡기 증상 (기침, 콧물, 인후통 등)", "소화기 증상 (복통, 설사, 구토 등)", "전신 증상 (고열, 근육통, 피로 등)", "기타 (직접 입력)"],
            horizontal=True
        )
        
        symptom_detail = st.text_area("증상을 더 자세히 설명해주세요.", placeholder="예: 이틀 전부터 마른기침이 나고, 오늘 아침부터는 목이 칼칼하게 아픕니다.", height=150)
        submitted = st.form_submit_button("AI 진단 결과 보기")

    if submitted:
        if symptom_category == "기타 (직접 입력)":
            final_symptom_text = symptom_detail
        else:
            final_symptom_text = f"주요 증상 카테고리: {symptom_category}. 상세 설명: {symptom_detail}"

        if not final_symptom_text.strip() or (symptom_category != "기타 (직접 입력)" and not symptom_detail.strip()):
            st.warning("증상 카테고리를 선택하고, 상세 설명을 반드시 입력해주세요.")
        else:
            MODEL_NAME = "sonar-small" # 빠르고 저렴한 모델 사용
            with st.spinner(f"`{MODEL_NAME}` 모델이 사용자 정보를 분석하고 있습니다..."):
                try:
                    user_profile = f"나이: {age}, 성별: {gender_display}, 추가 정보: {history if history else '없음'}"
                    messages = [
                        {"role": "system", "content": "당신은 사용자의 증상을 분석하여 신뢰도 높은 의학 정보를 제공하는 유능한 AI 의료 어시스턴트입니다. 최신 데이터를 참조하여 객관적이고 체계적인 답변을 제공해야 합니다."},
                        {"role": "user", "content": f"[환자 정보]\n{user_profile}\n\n[주요 증상]\n{final_symptom_text}\n\n---\n위 정보를 바탕으로, 다음의 엄격한 형식에 맞춰 답변해주세요:\n\n1. **환자 증상 요약**: 사용자가 입력한 핵심 증상을 간략히 요약합니다.\n2. **예상 질환**: 가장 가능성이 높은 질병 2가지를 예측하여, 각각 아래 항목을 반드시 포함하여 설명해주세요.\n    - **질병 설명**: 어떤 질병인지 일반인이 이해하기 쉽게 설명.\n    - **주요 근거**: 사용자가 제시한 정보 중 어떤 것 때문에 이 질병을 의심했는지 명확히 짚어주세요.\n    - **함께 나타날 수 있는 증상**: **\"아래 증상들이 함께 나타난다면, 해당 질병일 가능성이 더 높습니다.\"** 와 같이 설명의 의도를 먼저 안내해주세요. 그 다음, 각 예상 질환과 흔히 동반되는 대표적인 증상 2가지를 나열해주세요.\n    - **추천 진료과**: 어떤 병원의 무슨 과를 방문해야 하는지 명확히 알려주세요.\n3. **결론 및 고지**: 이 내용은 정보 제공을 목적으로 하며, 의사의 전문적인 진단을 대체할 수 없다는 점을 강력하게 고지하는 문구로 마무리해주세요."}
                    ]
                    
                    response = client.chat.completions.create(model=MODEL_NAME, messages=messages)
                    
                    st.subheader("🤖 AI 어시스턴트 분석 결과")

                    # [버그 수정] AI의 답변을 한 번만 가져와서 처리하고, 한 번만 출력합니다.
                    raw_response = response.choices[0].message.content
                    cleaned_response = re.sub(r'\[\d+\]', '', raw_response)
                    st.markdown(cleaned_response)

                except Exception as e:
                    st.error(f"API 호출 중 오류가 발생했습니다: {e}")
                    st.error("API 키가 유효한지, 월 사용 한도를 초과하지 않았는지 확인해주세요.")
