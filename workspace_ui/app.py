"""모바일 워크스페이스 셸 — 헤더 한 줄, 본문 하나, 하단 탭 셋.

이 모듈은 껍데기만 책임진다. 만들기/다듬기/발행 세 영역의 실제 내용은
workspace_ui.create / polish / publish 가 채워 넣고, 여기서는 그 세
렌더러를 AREA_RENDERERS 에 그대로 꽂는다.

사용자 스토리지에는 자격 증명을 절대 넣지 않는다. 언어/테마/엔진 선택과
아직 보내지 않은 입력 텍스트처럼, 새어 나가도 무해한 값만 둔다.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import app, ui

from i18n import normalize_language
from workspace_ui import theme
from workspace_ui.copy import LANGUAGE_OPTIONS, copy
from workspace_ui.create import render_create
from workspace_ui.polish import render_polish
from workspace_ui.publish import render_publish


# 하단 내비 순서 = 글 한 편이 지나가는 순서.
AREAS = ("create", "polish", "publish")

AREA_ICONS = {
    "create": "edit_note",
    "polish": "auto_fix_high",
    "publish": "send",
}

# 로컬 CLI 와 데모만. xAI API 는 키를 받아야 하므로 레거시 Streamlit 앱에 남긴다.
ENGINE_OPTIONS = ("Grok CLI", "Claude CLI", "Codex CLI", "Demo")
DEFAULT_ENGINE = "Grok CLI"

# 서명된 사용자 스토리지의 초기값. 여기 없는 키는 각 영역이 직접 만든다.
STORAGE_DEFAULTS = {
    "language": "ko",
    "theme": theme.DEFAULT_THEME,
    "engine": DEFAULT_ENGINE,
    "last_area": AREAS[0],
    "create_input": "",
    "polish_input": "",
}


# ─────────────────────────────────────────────────────────────
# 영역 렌더러
# ─────────────────────────────────────────────────────────────

AREA_RENDERERS: dict[str, Callable[[], None]] = {
    "create": render_create,
    "polish": render_polish,
    "publish": render_publish,
}


# ─────────────────────────────────────────────────────────────
# 셸
# ─────────────────────────────────────────────────────────────

def build_workspace() -> None:
    """NiceGUI 루트 페이지. ui.run(root=build_workspace) 로 넘긴다."""
    settings = init_user_settings()
    theme.apply(settings["theme"])

    _render_header()

    with ui.footer(fixed=True).classes("workspace-bottom-nav"):
        with ui.tabs(value=settings["last_area"]).classes(
            "w-full justify-around workspace-tabs"
        ) as areas:
            for area in AREAS:
                ui.tab(area, label=copy(f"nav_{area}"), icon=AREA_ICONS[area]).mark(f"nav-{area}")

    with ui.tab_panels(areas, value=settings["last_area"]).classes("workspace-main"):
        for area in AREAS:
            with ui.tab_panel(area).classes("workspace-panel"):
                AREA_RENDERERS[area]()

    areas.on_value_change(lambda event: _remember_area(event.value))


def init_user_settings() -> dict:
    """비민감 기본값만 채우고 현재 설정을 돌려준다."""
    store = app.storage.user
    for key, value in STORAGE_DEFAULTS.items():
        store.setdefault(key, value)

    settings = {
        "language": normalize_language(store.get("language")),
        "theme": theme.normalize_theme(store.get("theme")),
        "engine": _normalize_engine(store.get("engine")),
        "last_area": _normalize_area(store.get("last_area")),
    }
    store.update(settings)
    return settings


def _normalize_engine(engine: str | None) -> str:
    return engine if engine in ENGINE_OPTIONS else DEFAULT_ENGINE


def _normalize_area(area: object) -> str:
    # ui.tabs 의 변경 이벤트는 탭 이름(문자열)을 준다 (NiceGUI 3.6+).
    return area if area in AREAS else AREAS[0]  # type: ignore[return-value]


def _remember_area(area: object) -> None:
    app.storage.user["last_area"] = _normalize_area(area)


def _render_header() -> None:
    with ui.header(fixed=True).classes("workspace-header items-center"):
        ui.html(theme.PAW_SVG, sanitize=False).classes("workspace-paw")
        ui.label(copy("app_title")).classes("workspace-title")
        ui.space()
        ui.button(icon="settings", on_click=open_settings) \
            .props("flat round dense color=inherit") \
            .classes("workspace-icon-button") \
            .tooltip(copy("settings_open")) \
            .mark("open-settings")


# ─────────────────────────────────────────────────────────────
# 설정 다이얼로그
# ─────────────────────────────────────────────────────────────

def open_settings() -> None:
    """언어 / 테마 / 엔진만 다룬다. 키 입력란은 두지 않는다."""
    settings = init_user_settings()

    with ui.dialog() as dialog, ui.column().classes("workspace-settings-card").mark("settings-dialog"):
        ui.label(copy("settings_title")).classes("workspace-settings-title")

        language = ui.select(
            dict(LANGUAGE_OPTIONS),
            value=settings["language"],
            label=copy("settings_language"),
        ).classes("w-full").mark("settings-language")

        theme_choice = ui.select(
            {"light": copy("settings_theme_light"), "dark": copy("settings_theme_dark")},
            value=settings["theme"],
            label=copy("settings_theme"),
        ).classes("w-full").mark("settings-theme")

        engine = ui.select(
            list(ENGINE_OPTIONS),
            value=settings["engine"],
            label=copy("settings_engine"),
        ).classes("w-full").mark("settings-engine")

        ui.label(copy("settings_engine_hint")).classes("workspace-hint")
        ui.label(copy("settings_api_notice")).classes("workspace-notice").mark("settings-api-notice")

        # 어두운 테마의 강조색은 밝아서 흰 글씨가 읽히지 않는다 — 대비를 뒤집는다.
        save_text_color = "white" if settings["theme"] == "light" else "dark"
        with ui.row().classes("w-full justify-end items-center"):
            ui.button(copy("settings_close"), on_click=dialog.close).props("flat")
            ui.button(
                copy("settings_save"),
                on_click=lambda: save_settings(language.value, theme_choice.value, engine.value),
            ).props(f"unelevated text-color={save_text_color}").mark("settings-save")

    # 열 때마다 새로 만드므로 닫히면 지운다 — 반복해서 열어도 요소가 쌓이지 않는다.
    dialog.on("hide", dialog.delete)
    dialog.open()


def save_settings(language: str, theme_name: str, engine: str) -> None:
    """선택을 저장하고 페이지를 다시 그린다. 서버 재시작은 필요 없다."""
    app.storage.user.update({
        "language": normalize_language(language),
        "theme": theme.normalize_theme(theme_name),
        "engine": _normalize_engine(engine),
    })
    ui.navigate.reload()
