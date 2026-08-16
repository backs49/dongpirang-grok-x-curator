"""워크스페이스 룩앤필 — 분홍 발바닥 정체성과 라이트/다크 토큰.

design.py(Streamlit 앱 디자인 시스템)의 색값을 그대로 가져와 두 앱이 같은
브랜드로 보이게 한다. 다만 여기는 대시보드가 아니라 손에 들고 쓰는 글쓰기
작업대라, 본문이 화면을 지배하고 헤더와 하단 내비는 최대한 얇다.

다크 모드는 한 가지 방식으로만 켠다: body 에 workspace-dark 클래스를 붙이고
(우리 토큰), 같은 값으로 NiceGUI 다크 토글을 켠다(Quasar 컴포넌트 크롬).
"""

from __future__ import annotations

from nicegui import ui


THEME_OPTIONS = ("light", "dark")
DEFAULT_THEME = "light"

# design.py 의 색값 그대로. Quasar 브랜드 색도 같은 값으로 맞춰 버튼과
# 선택 위젯이 기본 파랑 대신 우리 강조색을 쓰게 한다.
ACCENT = {"light": "#C9521E", "dark": "#E07840"}
SURFACE_DARK = "#2A1F17"
PAGE_DARK = "#1A130E"
PAW_PINK = "#F5B7C3"

# app.py 의 PINK_PAW_SVG 와 같은 모양. 색은 CSS 토큰(--ws-paw)이 정한다.
PAW_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
    'width="100%" height="100%" role="img" aria-label="동피랑고양이">'
    '<g>'
    '<g transform="translate(0,2)">'
    '<ellipse cx="8" cy="11" rx="3" ry="4"/>'
    '<ellipse cx="14" cy="6" rx="3" ry="4"/>'
    '<ellipse cx="20" cy="6" rx="3" ry="4"/>'
    '<ellipse cx="26" cy="11" rx="3" ry="4"/>'
    '<ellipse cx="17" cy="22" rx="8" ry="7"/>'
    '</g>'
    '<g transform="translate(30,32)">'
    '<ellipse cx="8" cy="11" rx="3" ry="4"/>'
    '<ellipse cx="14" cy="6" rx="3" ry="4"/>'
    '<ellipse cx="20" cy="6" rx="3" ry="4"/>'
    '<ellipse cx="26" cy="11" rx="3" ry="4"/>'
    '<ellipse cx="17" cy="22" rx="8" ry="7"/>'
    '</g>'
    '</g></svg>'
)

# 하단 내비 높이. 본문 하단 여백이 이 값을 기준으로 계산된다.
_NAV_HEIGHT = "58px"

WORKSPACE_CSS = f"""
:root {{
  --ws-bg: #FBF7F2;
  --ws-surface: #FFFFFF;
  --ws-sunken: #F4ECE2;
  --ws-text: #1F1A15;
  --ws-text-strong: #0F0A05;
  --ws-text-muted: #6B5A4A;
  --ws-border: #E5D8C8;
  --ws-accent: {ACCENT['light']};
  --ws-accent-soft: rgba(201, 82, 30, 0.12);
  --ws-paw: {PAW_PINK};
  --ws-nav-height: {_NAV_HEIGHT};
}}

body.workspace-dark {{
  --ws-bg: {PAGE_DARK};
  --ws-surface: {SURFACE_DARK};
  --ws-sunken: #221A13;
  --ws-text: #F5EADE;
  --ws-text-strong: #FFFFFF;
  --ws-text-muted: #B89880;
  --ws-border: #6B4F38;
  --ws-accent: {ACCENT['dark']};
  --ws-accent-soft: rgba(224, 120, 64, 0.18);
  --ws-paw: {PAW_PINK};
}}

body {{
  background: var(--ws-bg);
  color: var(--ws-text);
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-tap-highlight-color: transparent;
}}

/* NiceGUI 기본 본문 여백을 없앤다 — 여백은 각 영역이 직접 정한다. */
.nicegui-content {{
  padding: 0;
  gap: 0;
}}

/* ─── 헤더: 발바닥 + 이름 + 설정. 얇게 유지한다. ─── */
.workspace-header {{
  background: var(--ws-surface);
  color: var(--ws-text-strong);
  border-bottom: 1px solid var(--ws-border);
  box-shadow: none;
  min-height: 48px;
  padding: 4px 12px;
  gap: 8px;
}}
.workspace-paw {{
  width: 22px;
  height: 22px;
  flex: 0 0 auto;
  line-height: 0;
}}
.workspace-paw svg g {{
  fill: var(--ws-paw);
}}
.workspace-title {{
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--ws-text-strong);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.workspace-icon-button {{
  color: var(--ws-text-muted);
}}

/* ─── 본문: 화면을 지배하는 영역. ─── */
.workspace-main {{
  background: transparent;
  width: 100%;
  padding: 0;
  padding-bottom: calc(var(--ws-nav-height) + env(safe-area-inset-bottom, 0px) + 12px);
}}
.workspace-panel {{
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px 16px 8px;
}}
.workspace-area-title {{
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ws-text-strong);
}}
.workspace-hint {{
  font-size: 13px;
  line-height: 1.65;
  color: var(--ws-text-muted);
}}
.workspace-card {{
  background: var(--ws-surface);
  border: 1px solid var(--ws-border);
  border-radius: 16px;
  box-shadow: none;
  padding: 16px;
  gap: 10px;
}}
.workspace-notice {{
  background: var(--ws-accent-soft);
  border-left: 3px solid var(--ws-accent);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--ws-text);
}}

/* ─── 하단 내비: 고정, 엄지로 닿는 높이, 아이폰 홈 인디케이터 회피. ─── */
.workspace-bottom-nav {{
  background: var(--ws-surface);
  color: var(--ws-text-muted);
  border-top: 1px solid var(--ws-border);
  box-shadow: none;
  padding: 0;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}}
.workspace-tabs .q-tab {{
  min-height: var(--ws-nav-height);
  padding: 6px 0;
  color: var(--ws-text-muted);
}}
.workspace-tabs .q-tab__icon {{
  font-size: 22px;
}}
.workspace-tabs .q-tab__label {{
  margin-top: 2px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: -0.01em;
}}
.workspace-tabs .q-tab--active {{
  color: var(--ws-accent);
}}
.workspace-tabs .q-tab__indicator,
.workspace-tabs .q-focus-helper {{
  display: none;
}}

/* ─── 설정 다이얼로그 ─── */
.workspace-settings-card {{
  width: 100%;
  max-width: 380px;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--ws-border);
  border-radius: 18px;
  background: var(--ws-surface);
  color: var(--ws-text);
  box-shadow: none;
}}
.workspace-settings-title {{
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ws-text-strong);
}}

/* 태블릿/데스크톱에서도 한 손 폭을 유지한다 — 대시보드로 번지지 않게. */
@media (min-width: 640px) {{
  .workspace-panel {{
    width: 100%;
    max-width: 560px;
    margin: 0 auto;
  }}
}}
"""


def normalize_theme(theme: str | None) -> str:
    """알 수 없는 값은 밝은 테마로 떨어뜨린다."""
    return theme if theme in THEME_OPTIONS else DEFAULT_THEME


def apply(theme: str = DEFAULT_THEME) -> None:
    """현재 페이지에 워크스페이스 CSS 와 테마를 적용한다."""
    name = normalize_theme(theme)
    dark = name == "dark"
    ui.add_css(WORKSPACE_CSS)
    ui.colors(primary=ACCENT[name], accent=PAW_PINK, dark=SURFACE_DARK, dark_page=PAGE_DARK)
    ui.dark_mode(dark)
    if dark:
        ui.query("body").classes(add="workspace-dark")
