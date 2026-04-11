"""
동피랑 Grok X 추천기 — Design System
app.py에서 import 후 inject_css() 한 번만 호출하면 됩니다.

사용법:
    from design import inject_css
    inject_css()
"""

import streamlit as st


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


_CSS = """
<style>

/* ── 전역 폰트/배경 ─────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', -apple-system, sans-serif;
}

/* ── 사이드바 ────────────────────────────────────── */
/* Streamlit Cloud에서 config.toml secondaryBackgroundColor가
   사이드바에 잘 안 먹히는 경우 CSS로 강제 덮어쓰기 */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"] {
    background-color: #221A15 !important;
}

section[data-testid="stSidebar"] {
    border-right: 1px solid #3D2A20 !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #F2E8DF;
}

/* ── 탭 네비게이션 ───────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #3D2A20 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: 13px;
    padding: 8px 14px;
    border-radius: 6px 6px 0 0;
    color: #A08070 !important;
    background: transparent !important;
    border: none !important;
    transition: color 0.15s;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #F2E8DF !important;
    background: #2E1F17 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #D4622A !important;
    background: transparent !important;
    border-bottom: 2px solid #D4622A !important;
    font-weight: 600;
}

/* ── 버튼 ────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #D4622A !important;
    color: #D4622A !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 18px !important;
    transition: background 0.15s, color 0.15s !important;
}

.stButton > button:hover {
    background: #D4622A !important;
    color: #F2E8DF !important;
}

.stButton > button:active {
    transform: scale(0.98);
}

/* Primary 버튼 (type="primary") */
.stButton > button[kind="primary"] {
    background: #D4622A !important;
    color: #F2E8DF !important;
}

.stButton > button[kind="primary"]:hover {
    background: #B8501E !important;
}

/* ── 링크 버튼 (X 공유, 팔로우 등) ─────────────────
   테라코타 아웃라인으로 통일 — 사이드바/메인 모두 일관성 */
.stLinkButton > a {
    border: 1px solid #D4622A !important;
    color: #D4622A !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    background: transparent !important;
    transition: background 0.15s, color 0.15s !important;
}

.stLinkButton > a:hover {
    background: #D4622A !important;
    color: #F2E8DF !important;
    text-decoration: none !important;
}

/* 사이드바 내 링크버튼은 좀 더 차분하게 */
section[data-testid="stSidebar"] .stLinkButton > a {
    border-color: #6B4030 !important;
    color: #C07050 !important;
}

section[data-testid="stSidebar"] .stLinkButton > a:hover {
    border-color: #D4622A !important;
    background: #D4622A !important;
    color: #F2E8DF !important;
}

/* ── 입력 필드 ───────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: #2A1E17 !important;
    border: 1px solid #4A3020 !important;
    border-radius: 6px !important;
    color: #F2E8DF !important;
    font-size: 14px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #D4622A !important;
    box-shadow: 0 0 0 2px rgba(212, 98, 42, 0.15) !important;
}

/* ── st.metric ───────────────────────────────────── */
[data-testid="stMetric"] {
    background: #221A15;
    border: 1px solid #3D2A20;
    border-radius: 8px;
    padding: 14px 18px !important;
}

[data-testid="stMetricValue"] {
    color: #D4622A !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: #A08070 !important;
    font-size: 12px !important;
}

/* ── st.code ─────────────────────────────────────── */
.stCodeBlock {
    border: 1px solid #3D2A20 !important;
    border-radius: 8px !important;
    background: #1E1510 !important;
}

/* ── st.expander ─────────────────────────────────── */
.streamlit-expanderHeader {
    background: #221A15 !important;
    border: 1px solid #3D2A20 !important;
    border-radius: 6px !important;
    color: #F2E8DF !important;
    font-size: 13px !important;
}

.streamlit-expanderHeader:hover {
    border-color: #D4622A !important;
}

.streamlit-expanderContent {
    background: #1A1008 !important;
    border: 1px solid #3D2A20 !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
}

/* ── st.warning / st.error / st.success ─────────── */
[data-testid="stNotificationContentWarning"] {
    background: #2E2010 !important;
    border-left: 3px solid #D4622A !important;
    border-radius: 6px !important;
}

[data-testid="stNotificationContentError"] {
    background: #2E1010 !important;
    border-left: 3px solid #C0392B !important;
    border-radius: 6px !important;
}

[data-testid="stNotificationContentSuccess"] {
    background: #102E20 !important;
    border-left: 3px solid #5BA090 !important;
    border-radius: 6px !important;
}

/* ── st.info ─────────────────────────────────────── */
[data-testid="stNotificationContentInfo"] {
    background: #1E1A10 !important;
    border-left: 3px solid #D4622A !important;
    border-radius: 6px !important;
}

/* ── 체크박스 ─────────────────────────────────────── */
.stCheckbox > label > span {
    border-color: #4A3020 !important;
}

.stCheckbox > label > span[aria-checked="true"] {
    background: #D4622A !important;
    border-color: #D4622A !important;
}

/* ── 구분선 ───────────────────────────────────────── */
hr {
    border-color: #3D2A20 !important;
}

/* ── 스크롤바 ─────────────────────────────────────── */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #16110E;
}
::-webkit-scrollbar-thumb {
    background: #4A3020;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #D4622A;
}

/* ── 아이디어/큐레이터 카드 (st.container) ────────── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
    border: 1px solid #3D2A20;
    border-radius: 8px;
    padding: 12px 16px;
    background: #1E1510;
    transition: border-color 0.15s;
}

[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:hover {
    border-color: #D4622A;
}

/* ── 페이지 헤더 타이틀 ──────────────────────────── */
h1 {
    color: #F2E8DF !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

h2, h3 {
    color: #E0C8B8 !important;
    font-weight: 600 !important;
}

/* ── footer 숨기기 ───────────────────────────────── */
footer {
    visibility: hidden;
}

</style>

<!-- Google Fonts: Noto Sans KR -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
"""
