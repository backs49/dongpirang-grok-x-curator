"""
동피랑 Grok X 추천기 — Design System

토큰 기반 CSS 변수 시스템으로 라이트/다크 두 테마를 지원한다.
사용법:
    from design import inject_css
    inject_css(theme="light")  # 또는 "dark"
"""

import streamlit as st


# ─── 컬러 토큰 (테마별) ───────────────────────────────
LIGHT_TOKENS = {
    "--bg":            "#FBF7F2",
    "--bg-elevated":   "#FFFFFF",
    "--bg-sidebar":    "#F4ECE2",
    "--bg-hover":      "#F0E6D7",
    "--text":          "#1F1A15",
    "--text-strong":   "#0F0A05",
    "--text-muted":    "#6B5A4A",
    "--accent":        "#C9521E",
    "--accent-hover": "#A8401A",
    "--accent-soft":   "rgba(201, 82, 30, 0.12)",
    "--border":        "#E5D8C8",
    "--border-strong": "#C9B8A2",
    "--success":       "#2D7A4F",
    "--warning":       "#B8761F",
    "--danger":        "#B53929",
    "--alert-info-bg":    "#FCF1E6",
    "--alert-success-bg": "#E8F4ED",
    "--alert-warning-bg": "#FBF1DC",
    "--alert-error-bg":   "#FBE8E5",
    "--scrollbar-track":  "#F0E6D7",
    "--scrollbar-thumb":  "#C9B8A2",
}

DARK_TOKENS = {
    "--bg":            "#1A130E",
    "--bg-elevated":   "#2A1F17",
    "--bg-sidebar":    "#221A13",
    "--bg-hover":      "#33261C",
    "--text":          "#F5EADE",
    "--text-strong":   "#FFFFFF",
    "--text-muted":    "#B89880",
    "--accent":        "#E07840",
    "--accent-hover":  "#C9521E",
    "--accent-soft":   "rgba(224, 120, 64, 0.18)",
    "--border":        "#4A3525",
    "--border-strong": "#6B4F38",
    "--success":       "#5BA080",
    "--warning":       "#D4922B",
    "--danger":        "#D9534F",
    "--alert-info-bg":    "#2E1F12",
    "--alert-success-bg": "#142E20",
    "--alert-warning-bg": "#2E2310",
    "--alert-error-bg":   "#2E1410",
    "--scrollbar-track":  "#221A13",
    "--scrollbar-thumb":  "#4A3525",
}

# ─── 타이포/간격/기타 토큰 (테마 공통) ────────────────
SHARED_TOKENS = {
    "--font-sans":      "'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif",
    "--text-xs":        "12px",
    "--text-sm":        "13px",
    "--text-base":      "15px",
    "--text-lg":        "17px",
    "--text-xl":        "22px",
    "--text-2xl":       "28px",
    "--text-3xl":       "34px",
    "--leading-tight":  "1.3",
    "--leading-normal": "1.55",
    "--space-1":        "4px",
    "--space-2":        "8px",
    "--space-3":        "12px",
    "--space-4":        "16px",
    "--space-5":        "20px",
    "--space-6":        "24px",
    "--space-8":        "32px",
    "--radius-sm":      "4px",
    "--radius-md":      "6px",
    "--radius-lg":      "10px",
    "--shadow-sm":      "0 1px 2px rgba(0, 0, 0, 0.05)",
    "--shadow-md":      "0 4px 12px rgba(0, 0, 0, 0.08)",
}


# ─── 컴포넌트 CSS (토큰만 참조) ───────────────────────
_COMPONENT_CSS = """
/* ── 전역 폰트/배경 ─────────────────────────────── */
html, body, [class*="css"] {
    font-family: var(--font-sans);
}

.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── 사이드바 ────────────────────────────────────── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {
    background-color: var(--bg-sidebar) !important;
}

section[data-testid="stSidebar"] {
    border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-strong) !important;
}

/* 사이드바 섹션 라벨 */
.sidebar-section-label {
    display: block;
    font-size: var(--text-xs);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    font-weight: 600;
    margin-bottom: var(--space-2);
}

/* ── 본문 텍스트 가독성 ─────────────────────────── */
.stMarkdown p, .stMarkdown li {
    font-size: var(--text-base) !important;
    line-height: var(--leading-normal) !important;
    color: var(--text) !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    font-size: var(--text-xs) !important;
    color: var(--text-muted) !important;
}

/* ── 페이지 헤더 타이틀 ──────────────────────────── */
h1 {
    color: var(--text-strong) !important;
    font-weight: 700 !important;
    font-size: var(--text-3xl) !important;
    letter-spacing: -0.02em;
}

h2 {
    color: var(--text-strong) !important;
    font-weight: 600 !important;
    font-size: var(--text-2xl) !important;
}

h3 {
    color: var(--text-strong) !important;
    font-weight: 600 !important;
    font-size: var(--text-xl) !important;
}

/* ── 탭 네비게이션 ───────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: var(--text-sm);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
    transition: color 0.15s, background 0.15s;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-strong) !important;
    background: var(--bg-hover) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    background: transparent !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 600;
}

/* ── 버튼 ────────────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    border-radius: var(--radius-md) !important;
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    padding: var(--space-2) var(--space-5) !important;
    transition: background 0.15s, color 0.15s, box-shadow 0.15s !important;
}

.stButton > button:hover {
    background: var(--accent) !important;
    color: var(--bg-elevated) !important;
}

.stButton > button:focus {
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
    outline: none !important;
}

.stButton > button:active {
    transform: scale(0.98);
}

.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: var(--bg-elevated) !important;
}

.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}

/* ── 링크 버튼 ───────────────────────────────────── */
.stLinkButton > a {
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
    border-radius: var(--radius-md) !important;
    font-size: var(--text-sm) !important;
    background: transparent !important;
    transition: background 0.15s, color 0.15s !important;
}

.stLinkButton > a:hover {
    background: var(--accent) !important;
    color: var(--bg-elevated) !important;
    text-decoration: none !important;
}

/* ── 입력 필드 ───────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
    font-size: var(--text-base) !important;
    padding: 10px 14px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ── st.metric ───────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: var(--space-4) var(--space-5) !important;
    box-shadow: var(--shadow-sm);
}

[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-size: var(--text-2xl) !important;
    font-weight: 700 !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: var(--text-sm) !important;
}

/* ── st.code ─────────────────────────────────────── */
.stCodeBlock {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-elevated) !important;
}

/* ── st.expander ─────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-elevated) !important;
}

[data-testid="stExpander"] summary {
    color: var(--text) !important;
    font-size: var(--text-sm) !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--accent) !important;
}

/* ── 알림 (info / success / warning / error) ────── */
[data-testid="stNotificationContentInfo"] {
    background: var(--alert-info-bg) !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
}

[data-testid="stNotificationContentSuccess"] {
    background: var(--alert-success-bg) !important;
    border-left: 3px solid var(--success) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
}

[data-testid="stNotificationContentWarning"] {
    background: var(--alert-warning-bg) !important;
    border-left: 3px solid var(--warning) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
}

[data-testid="stNotificationContentError"] {
    background: var(--alert-error-bg) !important;
    border-left: 3px solid var(--danger) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text) !important;
}

/* ── 체크박스 ─────────────────────────────────────── */
.stCheckbox > label > span {
    border-color: var(--border-strong) !important;
}

.stCheckbox > label > span[aria-checked="true"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}

/* ── 구분선 ───────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
}

/* ── 스크롤바 ─────────────────────────────────────── */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: var(--scrollbar-track);
}
::-webkit-scrollbar-thumb {
    background: var(--scrollbar-thumb);
    border-radius: var(--radius-sm);
}
::-webkit-scrollbar-thumb:hover {
    background: var(--accent);
}

/* ── 카드 (st.container border=True) ─────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-elevated);
    box-shadow: var(--shadow-sm);
    padding: var(--space-4) var(--space-5) !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border-strong) !important;
    box-shadow: var(--shadow-md);
}

/* ── footer 숨기기 ───────────────────────────────── */
footer {
    visibility: hidden;
}
"""

# ─── Google Fonts 링크 ────────────────────────────────
_FONT_LINK = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
"""


def _build_root_block(theme: str) -> str:
    color_tokens = DARK_TOKENS if theme == "dark" else LIGHT_TOKENS
    all_tokens = {**color_tokens, **SHARED_TOKENS}
    lines = "\n".join(f"  {k}: {v};" for k, v in all_tokens.items())
    return f":root {{\n{lines}\n}}"


def inject_css(theme: str = "light") -> None:
    """선택된 테마의 토큰을 :root 블록으로 emit하고 컴포넌트 CSS를 주입한다.

    theme: 'light' 또는 'dark'. 그 외 값은 'light'로 간주.
    """
    root_block = _build_root_block(theme)
    payload = f"<style>\n{root_block}\n{_COMPONENT_CSS}\n</style>\n{_FONT_LINK}"
    st.markdown(payload, unsafe_allow_html=True)
