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
    "--border":        "#6B4F38",
    "--border-strong": "#8B6A4D",
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

/* config.toml의 정적 textColor가 다크 모드에서 새어나오는 것을 막기 위해
   메인 컨테이너 안의 모든 텍스트 디폴트 색을 토큰으로 강제. */
[data-testid="stAppViewContainer"] {
    color: var(--text) !important;
}

/* ── 상단 헤더 툴바 (Deploy 버튼 영역) ─────────────── */
body header,
body [data-testid="stHeader"],
body [data-testid="stHeader"] > div,
body .stAppHeader,
body [data-testid="stToolbar"],
body [data-testid="stDecoration"] {
    background: var(--bg) !important;
    background-color: var(--bg) !important;
}

body header *,
body [data-testid="stHeader"] *,
body .stAppHeader * {
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

/* 모든 마크다운 컨테이너 텍스트 — expander 헤더, dataframe 등
   Streamlit이 [data-testid="stMarkdownContainer"]에 emotion-cache 색을
   적용하기 때문에 토큰 색으로 강제해야 함. */
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMarkdownContainer"] span,
.stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stMarkdownContainer"] em {
    color: var(--text) !important;
}

/* 캡션은 더 흐리게 (markdown 룰을 이기도록 source order 뒤에 배치) */
.stApp .stCaption,
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaption"],
.stApp [data-testid="stCaptionContainer"] *,
.stApp [data-testid="stCaption"] * {
    font-size: var(--text-xs) !important;
    color: var(--text-muted) !important;
}

/* ── 위젯 라벨 (text input, textarea, selectbox 등의 윗줄) ─── */
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] *,
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stWidgetLabel"] [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"] [data-testid="stMarkdownContainer"] *,
.stApp label[data-baseweb="form-control-label"],
.stApp label[data-baseweb="form-control-label"] *,
.stApp .stTextInput label,
.stApp .stTextInput label *,
.stApp .stTextArea label,
.stApp .stTextArea label *,
.stApp .stSelectbox label,
.stApp .stSelectbox label *,
.stApp .stMultiSelect label,
.stApp .stMultiSelect label *,
.stApp .stNumberInput label,
.stApp .stNumberInput label *,
.stApp .stDateInput label,
.stApp .stTimeInput label,
.stApp .stRadio label,
.stApp .stCheckbox label,
.stApp .stFileUploader label,
.stApp .stColorPicker label,
.stApp .stSlider label {
    color: var(--text) !important;
}

.stApp [data-testid="stWidgetLabel"],
.stApp label[data-baseweb="form-control-label"] {
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
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

/* ── 탭 네비게이션 ─────────────────────────────────
   탭 레이블이 길어져 뷰포트를 넘칠 경우 마지막 탭이 잘리지 않도록
   tab-list를 가로 스크롤로 허용하고, 각 탭은 줄바꿈 없이 한 줄로 유지. */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid var(--border) !important;
    background: transparent !important;
    overflow-x: auto !important;
    flex-wrap: nowrap !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: var(--text-sm);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    color: var(--text-muted) !important;
    background: transparent !important;
    border: none !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
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

/* 다크 모드에서 입력 캐럿(커서)이 배경색과 섞여 보이지 않는 현상 방지.
   text/textarea/number/search 모든 입력 요소에 토큰 색을 강제. */
.stApp input,
.stApp textarea,
.stApp .stTextInput input,
.stApp .stTextArea textarea,
.stApp .stNumberInput input,
.stApp .stChatInput textarea {
    caret-color: var(--accent) !important;
}

/* text_input 내부 보조 컨트롤 (password 보기/숨기기 아이콘 등) —
   baseweb input wrapper가 secondaryBackgroundColor를 배경으로 깔아서
   다크 모드에서 라이트색으로 새어나오는 것을 막는다. */
.stApp .stTextInput div[data-baseweb="base-input"],
.stApp .stTextInput div[data-baseweb="input"] {
    background-color: var(--bg-elevated) !important;
}

.stApp .stTextInput div[data-baseweb="base-input"] button,
.stApp .stTextInput div[data-baseweb="input"] button {
    background-color: transparent !important;
    border: none !important;
    color: var(--text) !important;
}

.stApp .stTextInput div[data-baseweb="base-input"] button svg,
.stApp .stTextInput div[data-baseweb="input"] button svg {
    fill: var(--text) !important;
}

/* ── Selectbox 드롭다운 화살표 ──────────────────────
   baseweb select의 chevron svg가 fadedText로 렌더링되어 다크 모드에서
   거의 보이지 않음 → 본문 텍스트 색과 동일하게 강제. */
.stApp .stSelectbox svg,
.stApp [data-baseweb="select"] svg {
    fill: var(--text) !important;
    color: var(--text) !important;
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

/* ── st.code ─────────────────────────────────────────
   Streamlit은 react-syntax-highlighter로 st.code를 렌더하는데, 내부
   <pre>/<code>/<span>이 config.toml의 라이트 테마 색을 고정으로 박아두어
   다크 모드에서 배경/텍스트가 그대로 새어나온다. 바깥 래퍼(.stCodeBlock,
   [data-testid="stCode"])뿐 아니라 내부까지 토큰 색으로 강제 오버라이드. */
.stApp .stCodeBlock,
.stApp [data-testid="stCode"],
.stApp [data-testid="stCode"] pre,
.stApp [data-testid="stCode"] code,
.stApp .stCodeBlock pre,
.stApp .stCodeBlock code {
    background: var(--bg-elevated) !important;
    color: var(--text) !important;
}

.stApp .stCodeBlock {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
}

/* language="" 일 때 토큰 색을 유지(구문 강조 없음). 언어 지정된 코드의
   syntax token도 가독성을 위해 기본 텍스트 색으로 통일. */
.stApp [data-testid="stCode"] span,
.stApp .stCodeBlock span {
    color: var(--text) !important;
}

/* ── st.expander ─────────────────────────────────── */
.stApp [data-testid="stExpander"],
.stApp [data-testid="stExpanderDetails"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-elevated) !important;
}

/* Streamlit이 summary 요소에 secondaryBackgroundColor를 직접 박는 경우가
   있어 더 높은 specificity로 강제 오버라이드한다. */
.stApp [data-testid="stExpander"] details,
.stApp [data-testid="stExpander"] details > summary,
.stApp [data-testid="stExpander"] summary {
    background: var(--bg-elevated) !important;
}

.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary *,
.stApp details summary,
.stApp details summary * {
    color: var(--text) !important;
    font-size: var(--text-sm) !important;
}

.stApp [data-testid="stExpander"] summary:hover,
.stApp [data-testid="stExpander"] summary:hover * {
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

/* ── st.spinner ─────────────────────────────────────
   spinner 텍스트가 fadedText 색으로 렌더되어 다크 모드에서 거의 안 보이고,
   회전 원은 border-top만 accent로 남아있어 대비가 부족. 둘 다 토큰 색으로 강제. */
.stApp [data-testid="stSpinner"],
.stApp [data-testid="stSpinner"] > div {
    color: var(--text) !important;
}

.stApp [data-testid="stSpinner"] i,
.stApp [data-testid="stSpinner"] svg,
.stApp [data-testid="stSpinner"] div[role="progressbar"] {
    border-color: var(--border-strong) !important;
    border-top-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ── 카드 (st.container border=True / st.columns border=True) ─────
   Streamlit 1.50은 `st.container(border=True)`를 StyledFlexContainerBlock
   (emotion target="e196pkbe2")로, `st.columns(border=True)`를
   StyledColumn(data-testid="stColumn")으로 렌더링한다. 두 경우 모두 emotion이
   `border: 1px solid {theme.colors.borderColor}`를 직접 주입하는데, config.toml
   의 정적 borderColor가 다크 배경에서 거의 투명하므로 `border-color`만 토큰으로
   오버라이드한다. border-style이 없는 비-bordered 컨테이너에는 시각적 영향이
   없으므로 광범위 매칭이 안전하다. */
.stApp [class*="e196pkbe2"],
.stApp [data-testid="stColumn"] {
    border-color: var(--border-strong) !important;
    border-radius: var(--radius-lg) !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}

.stApp [class*="e196pkbe2"]:hover,
.stApp [data-testid="stColumn"]:hover {
    border-color: var(--accent) !important;
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


def _streamlit_var_overrides(color_tokens: dict) -> dict:
    """config.toml의 정적 색이 emotion-cache로 새어나오는 것을 막기 위해
    Streamlit 내부 CSS 변수를 우리 토큰으로 재바인딩한다."""
    return {
        "--background-color":            color_tokens["--bg"],
        "--secondary-background-color":  color_tokens["--bg-elevated"],
        "--text-color":                  color_tokens["--text"],
        "--primary-color":               color_tokens["--accent"],
        "--default-background-color":    color_tokens["--bg"],
        "--default-secondary-background-color": color_tokens["--bg-elevated"],
        "--default-text-color":          color_tokens["--text"],
        "--default-primary-color":       color_tokens["--accent"],
    }


def _build_root_block(theme: str) -> str:
    color_tokens = DARK_TOKENS if theme == "dark" else LIGHT_TOKENS
    streamlit_overrides = _streamlit_var_overrides(color_tokens)
    all_tokens = {**color_tokens, **SHARED_TOKENS, **streamlit_overrides}
    lines = "\n".join(f"  {k}: {v};" for k, v in all_tokens.items())
    return f":root {{\n{lines}\n}}"


def inject_css(theme: str = "light") -> None:
    """선택된 테마의 토큰을 :root 블록으로 emit하고 컴포넌트 CSS를 주입한다.

    theme: 'light' 또는 'dark'. 그 외 값은 'light'로 간주.
    """
    root_block = _build_root_block(theme)
    payload = f"<style>\n{root_block}\n{_COMPONENT_CSS}\n</style>\n{_FONT_LINK}"
    st.markdown(payload, unsafe_allow_html=True)
