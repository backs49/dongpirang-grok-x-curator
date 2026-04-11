import streamlit as st
import extra_streamlit_components as stx
from grok_client import GrokClient
from utils import generate_tweet_intent_url, generate_follow_url
from i18n import t, LANGUAGES, get_lang
from tabs.tab_optimizer import render_optimizer_tab
from tabs.tab_ideas import render_ideas_tab
from tabs.tab_curator import render_curator_tab
from tabs.tab_thread import render_thread_tab
from tabs.tab_scheduler import render_scheduler_tab
from tabs.tab_ab_compare import render_ab_compare_tab
from tabs.tab_unfollow import render_unfollow_tab
from tabs.tab_risk_check import render_risk_check_tab
from design import inject_css

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="동피랑 Grok X 추천기",
    page_icon="🔥",
    layout="wide",
)

APP_URL = "https://dongpirang-grok-x-curator.streamlit.app"
VIRAL_TAG = "동피랑 Grok X 추천기로 최적화됨 🔥 @mangodaon"
COOKIE_KEY = "dongpirang_grok_api_key"
THEME_COOKIE_KEY = "dongpirang_theme"

# ─── 쿠키 매니저 ───
cookie_manager = stx.CookieManager()

# ─── 쿠키에서 저장된 키 불러오기 ───
saved_key = cookie_manager.get(COOKIE_KEY) or ""
saved_theme = cookie_manager.get(THEME_COOKIE_KEY) or "light"
if saved_theme not in ("light", "dark"):
    saved_theme = "light"
if "theme" not in st.session_state:
    st.session_state.theme = saved_theme

inject_css(st.session_state.theme)

# ─── 사이드바 ───
with st.sidebar:
    st.title(t("app_title"))
    st.caption(t("app_caption"))

    # ─── 그룹 1: 환경 설정 ───
    with st.container(border=True):
        st.markdown(
            '<span class="sidebar-section-label">ENVIRONMENT</span>',
            unsafe_allow_html=True,
        )

        # 언어 선택
        lang_options = list(LANGUAGES.keys())
        current_lang = st.session_state.get("lang", "ko")
        lang_idx = lang_options.index(current_lang) if current_lang in lang_options else 0

        selected_lang = st.selectbox(
            t("lang_label"),
            lang_options,
            format_func=lambda k: LANGUAGES[k],
            index=lang_idx,
            key="lang_select",
        )
        if selected_lang != st.session_state.get("lang", "ko"):
            st.session_state.lang = selected_lang
            st.rerun()

        # 테마 선택
        THEME_OPTIONS = {"light": "☀ Light", "dark": "🌙 Dark"}
        current_theme = st.session_state.get("theme", "light")
        theme_keys = list(THEME_OPTIONS.keys())
        theme_idx = theme_keys.index(current_theme) if current_theme in theme_keys else 0

        selected_theme = st.selectbox(
            t("theme_label"),
            theme_keys,
            format_func=lambda k: THEME_OPTIONS[k],
            index=theme_idx,
            key="theme_select",
        )
        if selected_theme != st.session_state.get("theme", "light"):
            st.session_state.theme = selected_theme
            cookie_manager.set(
                THEME_COOKIE_KEY,
                selected_theme,
                key="save_theme_cookie",
            )
            st.rerun()

    # ─── 그룹 2: API 연결 ───
    with st.container(border=True):
        st.markdown(
            '<span class="sidebar-section-label">API CONNECTION</span>',
            unsafe_allow_html=True,
        )

        api_key = st.text_input(
            t("api_key_label"),
            type="password",
            help=t("api_key_help"),
            placeholder="xai-...",
            value=saved_key,
        )

        remember_key = st.checkbox(
            t("api_key_remember"),
            value=bool(saved_key),
            help=t("api_key_remember_help"),
        )

        # 쿠키 저장/삭제 (값이 변경될 때만)
        if remember_key and api_key and api_key != saved_key:
            cookie_manager.set(COOKIE_KEY, api_key, key="save_cookie")
        elif not remember_key and saved_key:
            cookie_manager.delete(COOKIE_KEY, key="delete_cookie")

        st.caption(t("api_key_warning"))

        model = st.selectbox(
            t("model_select"),
            ["grok-4-1-fast-reasoning", "grok-4.20-reasoning"],
            help=t("model_help"),
        )

        if get_lang() == "ja" and model == "grok-4-1-fast-reasoning":
            st.info(t("ja_model_warning"))

    # ─── CTA: 팔로우 버튼 (컨테이너 밖) ───
    follow_url = generate_follow_url("mangodaon")
    st.link_button(t("follow_btn"), follow_url, use_container_width=True)

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

_API_MSG = t("api_required")

# ─── 메인 타이틀 ───
st.title(t("app_title"))
st.caption(t("app_caption_main"))

# ─── 엔터키로 트리거된 작업 처리 (탭 렌더링 전) ───
if grok and st.session_state.pop("run_ideas", False):
    kw = st.session_state.get("keywords_input", "")
    if kw.strip():
        _length = st.session_state.get("post_length", 0)
        with st.spinner(t("ideas_spinner")):
            _result = grok.generate_ideas(kw, length=_length)
        if "error" not in _result:
            st.session_state.ideas_result = _result
        else:
            st.session_state.ideas_error = _result["error"]

if grok and st.session_state.pop("run_curator", False):
    inp = st.session_state.get("curator_interests", "")
    if inp.strip():
        with st.spinner(t("cur_spinner")):
            _result = grok.curate_feed(inp)
        if "error" not in _result:
            st.session_state.curator_result = _result
        else:
            st.session_state.curator_error = _result["error"]

# ─── 탭 ───
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    t("tab_optimizer"),
    t("tab_ideas"),
    t("tab_curator"),
    t("tab_thread"),
    t("tab_scheduler"),
    t("tab_ab"),
    t("tab_risk"),
    t("tab_unfollow"),
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
    st.markdown(t("footer_title"))
    st.caption(t("footer_caption"))

with footer_col2:
    promo_text = f"동피랑 Grok X 추천기로 X 포스트를 최적화하고 있어요! 🔥\nx-algorithm 기반 무료 분석\n\n{APP_URL}\n\n@mangodaon"
    promo_url = generate_tweet_intent_url(promo_text)
    st.link_button(t("footer_share"), promo_url, use_container_width=True)

with footer_col3:
    follow_url = generate_follow_url("mangodaon")
    st.link_button(t("footer_follow"), follow_url, use_container_width=True)
