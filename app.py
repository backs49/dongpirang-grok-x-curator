import streamlit as st
import extra_streamlit_components as stx
from grok_client import GrokClient
from utils import generate_tweet_intent_url, generate_follow_url
from tabs import (
    render_optimizer_tab,
    render_ideas_tab,
    render_curator_tab,
    render_thread_tab,
    render_scheduler_tab,
    render_ab_compare_tab,
    render_unfollow_tab,
    render_risk_check_tab,
)

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="동피랑 Grok X 추천기",
    page_icon="🔥",
    layout="wide",
)

APP_URL = "https://dongpirang-grok-x-curator.streamlit.app"
VIRAL_TAG = "동피랑 Grok X 추천기로 최적화됨 🔥 @mangodaon"
COOKIE_KEY = "dongpirang_grok_api_key"

# ─── 쿠키 매니저 ───
cookie_manager = stx.CookieManager()

# ─── 쿠키에서 저장된 키 불러오기 ───
saved_key = cookie_manager.get(COOKIE_KEY) or ""

# ─── 사이드바 ───
with st.sidebar:
    st.title("🔥 동피랑 Grok X 추천기")
    st.caption("x-algorithm 기반 X 포스트 최적화")

    st.divider()

    api_key = st.text_input(
        "🔑 Grok API Key 입력",
        type="password",
        help="console.x.ai에서 발급받으세요",
        placeholder="xai-...",
        value=saved_key,
    )

    remember_key = st.checkbox(
        "🔑 API 키 기억하기",
        value=bool(saved_key),
        help="브라우저 쿠키에 저장. 새로고침해도 유지됩니다.",
    )

    # 쿠키 저장/삭제 (값이 변경될 때만)
    if remember_key and api_key and api_key != saved_key:
        cookie_manager.set(COOKIE_KEY, api_key, key="save_cookie")
    elif not remember_key and saved_key:
        cookie_manager.delete(COOKIE_KEY, key="delete_cookie")

    st.caption("⚠️ Grok API Key는 한 번만 보여집니다.\n생성 즉시 저장하세요!")

    model = st.selectbox(
        "모델 선택",
        ["grok-4-1-fast-reasoning", "grok-4.20-reasoning"],
        help="grok-4-1-fast-reasoning: 빠른 응답 / grok-4.20-reasoning: 깊은 분석",
    )

    st.divider()

    follow_url = generate_follow_url("mangodaon")
    st.link_button("🐦 @mangodaon 팔로우하기", follow_url, use_container_width=True)

# ─── API 키 검증 & Grok 클라이언트 초기화 ───
grok = None
if api_key:
    if (
        "grok_client" not in st.session_state
        or st.session_state.get("_model") != model
        or st.session_state.get("_api_key") != api_key
    ):
        st.session_state.grok_client = GrokClient(api_key=api_key, model=model)
        st.session_state._model = model
        st.session_state._api_key = api_key
    grok = st.session_state.grok_client

_API_MSG = "⚠️ 이 기능을 사용하려면 사이드바에서 Grok API 키를 입력해주세요. 👉 [console.x.ai](https://console.x.ai)"

# ─── 메인 타이틀 ───
st.title("🔥 동피랑 Grok X 추천기")
st.caption("x-algorithm의 Phoenix Scorer & Candidate Pipeline 원리 기반")

# ─── 엔터키로 트리거된 작업 처리 (탭 렌더링 전) ───
if grok and st.session_state.pop("run_ideas", False):
    kw = st.session_state.get("keywords_input", "")
    if kw.strip():
        with st.spinner("Grok이 x-algorithm 최적화 아이디어 생성 중..."):
            _result = grok.generate_ideas(kw)
        if "error" not in _result:
            st.session_state.ideas_result = _result
        else:
            st.session_state.ideas_error = _result["error"]

if grok and st.session_state.pop("run_curator", False):
    inp = st.session_state.get("curator_interests", "")
    if inp.strip():
        with st.spinner("Grok이 X에서 실시간 검색 중..."):
            _result = grok.curate_feed(inp)
        if "error" not in _result:
            st.session_state.curator_result = _result
        else:
            st.session_state.curator_error = _result["error"]

# ─── 탭 ───
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📝 포스트 최적화",
    "💡 아이디어 생성",
    "🔍 피드 큐레이터",
    "🧵 스레드 최적화",
    "📅 포스팅 스케줄러",
    "⚖️ A/B 비교",
    "⚠️ 리스크 체크",
    "🔄 언팔 추적",
])

with tab1:
    if grok:
        render_optimizer_tab(grok, APP_URL, VIRAL_TAG)
    else:
        st.info(_API_MSG)
with tab2:
    if grok:
        render_ideas_tab(grok)
    else:
        st.info(_API_MSG)
with tab3:
    if grok:
        render_curator_tab(grok)
    else:
        st.info(_API_MSG)
with tab4:
    if grok:
        render_thread_tab(grok, APP_URL, VIRAL_TAG)
    else:
        st.info(_API_MSG)
with tab5:
    if grok:
        render_scheduler_tab(grok)
    else:
        st.info(_API_MSG)
with tab6:
    if grok:
        render_ab_compare_tab(grok, APP_URL, VIRAL_TAG)
    else:
        st.info(_API_MSG)
with tab7:
    if grok:
        render_risk_check_tab(grok)
    else:
        st.info(_API_MSG)
with tab8:
    render_unfollow_tab()

# ─── 하단 Footer ───
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**동피랑 Grok X 추천기** 🔥")
    st.caption("x-algorithm 기반 X 포스트 최적화 도구")

with footer_col2:
    promo_text = f"동피랑 Grok X 추천기로 X 포스트를 최적화하고 있어요! 🔥\nx-algorithm 기반 무료 분석\n\n{APP_URL}\n\n@mangodaon"
    promo_url = generate_tweet_intent_url(promo_text)
    st.link_button("🐦 이 앱을 X에 공유하기", promo_url, use_container_width=True)

with footer_col3:
    follow_url = generate_follow_url("mangodaon")
    st.link_button("👤 이 앱 만든 사람 팔로우하기 @mangodaon", follow_url, use_container_width=True)
