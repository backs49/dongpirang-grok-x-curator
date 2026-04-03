import streamlit as st
import extra_streamlit_components as stx
from grok_client import GrokClient
from utils import (
    generate_tweet_intent_url,
    generate_follow_url,
    append_viral_tag,
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

# ─── API 키 검증 ───
if not api_key:
    st.warning("⚠️ API 키를 입력해주세요. 사이드바에서 Grok API Key를 입력하면 시작됩니다.")
    st.info("👉 [console.x.ai](https://console.x.ai)에서 Grok API Key를 발급받을 수 있습니다.")
    st.stop()

# ─── Grok 클라이언트 초기화 ───
if (
    "grok_client" not in st.session_state
    or st.session_state.get("_model") != model
    or st.session_state.get("_api_key") != api_key
):
    st.session_state.grok_client = GrokClient(api_key=api_key, model=model)
    st.session_state._model = model
    st.session_state._api_key = api_key

grok: GrokClient = st.session_state.grok_client

# ─── 메인 타이틀 ───
st.title("🔥 동피랑 Grok X 추천기")
st.caption("x-algorithm의 Phoenix Scorer & Candidate Pipeline 원리 기반")

# ─── 엔터키로 트리거된 작업 처리 (탭 렌더링 전) ───
if st.session_state.pop("run_ideas", False):
    kw = st.session_state.get("keywords_input", "")
    if kw.strip():
        with st.spinner("Grok이 x-algorithm 최적화 아이디어 생성 중..."):
            _result = grok.generate_ideas(kw)
        if "error" not in _result:
            st.session_state.ideas_result = _result
        else:
            st.session_state.ideas_error = _result["error"]

if st.session_state.pop("run_curator", False):
    inp = st.session_state.get("curator_interests", "")
    if inp.strip():
        with st.spinner("Grok이 X에서 실시간 검색 중..."):
            _result = grok.curate_feed(inp)
        if "error" not in _result:
            st.session_state.curator_result = _result
        else:
            st.session_state.curator_error = _result["error"]

# ─── 탭 ───
tab1, tab2, tab3 = st.tabs(["📝 포스트 최적화", "💡 아이디어 생성", "🔍 피드 큐레이터"])

# ━━━ Tab 1: 포스트 최적화 ━━━
with tab1:
    st.subheader("포스트 Optimizer & Engagement Predictor")
    st.caption("x-algorithm의 Multi-Action Prediction 원리로 포스트를 분석합니다")

    post_text = st.text_area(
        "포스트 내용",
        height=120,
        placeholder="분석하고 싶은 포스트 내용을 입력하세요...",
    )

    col1, col2 = st.columns(2)
    with col1:
        image_desc = st.text_input("🖼️ 이미지 설명 (선택)", placeholder="예: 일몰 사진, 코드 스크린샷")
    with col2:
        hashtags = st.text_input("#️⃣ 해시태그 (선택)", placeholder="예: #AI #개발 #Python")

    if st.button("🔍 x-algorithm 분석", use_container_width=True, type="primary"):
        if not post_text.strip():
            st.warning("포스트 내용을 입력해주세요.")
        else:
            with st.spinner("Grok이 x-algorithm 분석 중..."):
                result = grok.optimize_post(post_text, image_desc, hashtags)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.optimize_result = result

    if "optimize_result" in st.session_state:
        result = st.session_state.optimize_result

        col_score, col_level = st.columns([1, 2])
        with col_score:
            score = result.get("score", 0)
            st.metric("x-algorithm 점수", f"{score}/100")
        with col_level:
            level = result.get("engagement_level", "Unknown")
            level_colors = {
                "Very High": "🟢", "High": "🔵", "Medium": "🟡", "Low": "🔴"
            }
            st.metric("참여 예측 등급", f"{level_colors.get(level, '⚪')} {level}")

        with st.expander("📊 분석 이유", expanded=True):
            for reason in result.get("reasons", []):
                st.markdown(f"- {reason}")

        with st.expander("💡 개선 제안", expanded=True):
            for suggestion in result.get("suggestions", []):
                st.markdown(f"- {suggestion}")

        st.subheader("✨ 최적화된 포스트")
        optimized = result.get("optimized_post", "")

        add_viral = st.checkbox(
            f"최적화된 포스트에 '{VIRAL_TAG}' 자동 추가",
            value=False,
        )

        if add_viral:
            optimized = append_viral_tag(optimized, VIRAL_TAG)

        st.code(optimized, language=None)

        share_text = f"이 포스트를 동피랑 Grok X 추천기로 분석했더니 점수 {score}/100! 🔥\n\n{APP_URL}\n\n@mangodaon"
        share_url = generate_tweet_intent_url(share_text)
        st.link_button("🐦 X에 공유하기", share_url, use_container_width=True)

# ━━━ Tab 2: 아이디어 생성 ━━━
with tab2:
    st.subheader("오늘 올릴 포스트 아이디어 5개")
    st.caption("x-algorithm 최적화된 포스트 아이디어를 생성합니다")

    keywords = st.text_input(
        "관심사 / 키워드",
        placeholder="예: AI, 프로그래밍, 스타트업, 한국 여행",
        key="keywords_input",
        on_change=lambda: st.session_state.update(run_ideas=True),
    )

    if st.button("💡 아이디어 생성", use_container_width=True, type="primary"):
        if not keywords.strip():
            st.warning("관심사나 키워드를 입력해주세요.")
        else:
            with st.spinner("Grok이 x-algorithm 최적화 아이디어 생성 중..."):
                result = grok.generate_ideas(keywords)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.ideas_result = result

    if "ideas_error" in st.session_state:
        st.error(st.session_state.pop("ideas_error"))

    if "ideas_result" in st.session_state:
        ideas = st.session_state.ideas_result.get("ideas", [])
        for i, idea in enumerate(ideas):
            with st.container(border=True):
                col_num, col_content = st.columns([1, 10])
                with col_num:
                    st.markdown(f"### #{i + 1}")
                with col_content:
                    st.markdown(f"**{idea.get('title', '')}**")
                    st.markdown(idea.get("content", ""))

                    detail_col1, detail_col2, detail_col3 = st.columns(3)
                    with detail_col1:
                        st.caption(f"📊 {idea.get('engagement_level', '')}")
                    with detail_col2:
                        st.caption(f"⏰ {idea.get('best_time', '')}")
                    with detail_col3:
                        actions = ", ".join(idea.get("target_actions", []))
                        st.caption(f"🎯 {actions}")

                    with st.expander("전략 보기"):
                        st.markdown(idea.get("strategy", ""))

# ━━━ Tab 3: 피드 큐레이터 ━━━
with tab3:
    st.subheader("Personalized Feed Curator")
    st.caption("Grok의 실시간 검색으로 관심사 기반 추천 포스트를 찾습니다")

    interests = st.text_input(
        "관심사 입력",
        placeholder="예: 머신러닝, 웹개발, 한국 테크 뉴스",
        key="curator_interests",
        on_change=lambda: st.session_state.update(run_curator=True),
    )

    if st.button("🔍 실시간 추천", use_container_width=True, type="primary"):
        if not interests.strip():
            st.warning("관심사를 입력해주세요.")
        else:
            with st.spinner("Grok이 X에서 실시간 검색 중..."):
                result = grok.curate_feed(interests)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.curator_result = result

    if "curator_error" in st.session_state:
        st.error(st.session_state.pop("curator_error"))

    if "curator_result" in st.session_state:
        recs = st.session_state.curator_result.get("recommendations", [])
        for i, rec in enumerate(recs):
            with st.container(border=True):
                st.markdown(f"**추천 #{i + 1}**")
                st.markdown(rec.get("summary", ""))
                st.caption(f"💡 추천 이유: {rec.get('why_recommended', '')}")
                st.caption(f"🤝 {rec.get('engagement_hint', '')}")

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
