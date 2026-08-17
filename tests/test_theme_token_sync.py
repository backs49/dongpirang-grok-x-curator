"""팔레트 드리프트 잠금 — workspace_ui/theme.py 를 design.py 토큰에 고정한다.

두 앱(Streamlit 대시보드, NiceGUI 워크스페이스)은 같은 브랜드로 보여야 하는데
색값은 theme.py 에 하드코딩된 사본이라 design.py 쪽 색이 바뀌어도 아무 것도
깨지지 않는다 — 기존 구조 테스트(test_workspace_shell.py 등)는 다크 토글이
켜지는지, 카피가 맞는지는 보지만 색값 자체는 보지 않는다. 이 파일은 그 사각
지대를 메운다: design.py 를 유일한 출처로 놓고 theme.py 값을 대조해 드리프트가
나면 여기서 먼저 실패하게 한다.

의도적으로 대상에서 뺀 것들(드리프트 감시가 필요 없거나 애초에 대응 짝이
없는 값):
  - --ws-paw: 발바닥 브랜드 색(PAW_PINK). design.py 에 대응 토큰이 없다.
  - --ws-nav-height: 하단 내비 레이아웃 치수. 색이 아니고 워크스페이스 전용이다.
  - design.py 의 hover/alert/scrollbar 계열, SHARED_TOKENS(타이포·간격·그림자):
    워크스페이스 CSS 가 아예 참조하지 않는 토큰이다.
"""

from __future__ import annotations

import re

import design
from workspace_ui import theme


def _extract_block(css: str, selector: str) -> str:
    """`selector {...}` 블록 하나만 잘라낸다.

    ``:root``와 ``body.workspace-dark`` 두 블록이 같은 문자열 안에 나란히
    있어서, 블록을 먼저 분리하지 않고 전체 문자열에 정규식을 돌리면 라이트/
    다크 값이 섞인다.
    """
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert match, f"{selector!r} 블록을 WORKSPACE_CSS 에서 찾지 못했다"
    return match.group(1)


def _extract_tokens(block: str) -> dict[str, str]:
    """블록 안의 `--ws-<name>: <value>;` 선언을 이름→값(공백 정규화)으로 모은다."""
    return {
        name: re.sub(r"\s+", " ", value).strip()
        for name, value in re.findall(r"--(ws-[\w-]+):\s*([^;]+);", block)
    }


def _design_value(tokens: dict[str, str], key: str) -> str:
    return re.sub(r"\s+", " ", tokens[key]).strip()


# 라이트/다크 공통 매핑 — workspace 토큰 이름 → design.py 토큰 이름.
_TOKEN_MAP = {
    "ws-bg": "--bg",
    "ws-surface": "--bg-elevated",
    "ws-sunken": "--bg-sidebar",
    "ws-text": "--text",
    "ws-text-strong": "--text-strong",
    "ws-text-muted": "--text-muted",
    "ws-border": "--border",
    "ws-accent": "--accent",
    "ws-accent-soft": "--accent-soft",
}


def test_workspace_accent_constants_match_design_tokens():
    assert theme.ACCENT["light"] == design.LIGHT_TOKENS["--accent"]
    assert theme.ACCENT["dark"] == design.DARK_TOKENS["--accent"]


def test_workspace_dark_surface_constants_match_design_tokens():
    assert theme.SURFACE_DARK == design.DARK_TOKENS["--bg-elevated"]
    assert theme.PAGE_DARK == design.DARK_TOKENS["--bg"]


def test_workspace_light_palette_matches_design_tokens():
    root_block = _extract_block(theme.WORKSPACE_CSS, ":root")
    ws_tokens = _extract_tokens(root_block)

    for ws_name, design_key in _TOKEN_MAP.items():
        assert ws_tokens[ws_name] == _design_value(design.LIGHT_TOKENS, design_key), (
            f"--{ws_name} 가 라이트 design.py 의 {design_key} 와 어긋났다"
        )


def test_workspace_dark_palette_matches_design_tokens():
    dark_block = _extract_block(theme.WORKSPACE_CSS, "body.workspace-dark")
    ws_tokens = _extract_tokens(dark_block)

    # --ws-nav-height 는 :root 블록에만 있고 색 토큰도 아니므로 다크 블록에는
    # 애초에 등장하지 않는다 — 매핑에서 빼는 게 아니라 대조 대상 자체가 없다.
    assert "nav-height" not in ws_tokens

    for ws_name, design_key in _TOKEN_MAP.items():
        assert ws_tokens[ws_name] == _design_value(design.DARK_TOKENS, design_key), (
            f"--{ws_name} 가 다크 design.py 의 {design_key} 와 어긋났다"
        )
