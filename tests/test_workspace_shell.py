"""모바일 워크스페이스 셸 — 하단 3영역, 설정 다이얼로그, 카피/테마 토큰."""

from nicegui import ui
from nicegui.testing import user_simulation

from workspace_ui import theme
from workspace_ui.app import ENGINE_OPTIONS, STORAGE_DEFAULTS, build_workspace
from workspace_ui.copy import copy
from workspace_ui.theme import WORKSPACE_CSS


async def test_shell_shows_three_mobile_areas():
    async with user_simulation(build_workspace) as user:
        await user.open("/")
        await user.should_see("만들기")
        await user.should_see("다듬기")
        await user.should_see("발행")


async def test_settings_offers_local_engines_and_never_asks_for_a_key():
    async with user_simulation(build_workspace) as user:
        await user.open("/")
        # 설정은 열기 전에는 화면에 없다 — 다이얼로그는 눌렀을 때 만들어진다.
        await user.should_not_see(marker="settings-dialog")

        user.find(marker="open-settings").click()
        await user.should_see(marker="settings-dialog")
        await user.should_see(marker="settings-api-notice")

        with user.client:
            engine_select = next(iter(user.find(marker="settings-engine").elements))
        assert engine_select.options == list(ENGINE_OPTIONS)
        assert "xAI API" not in engine_select.options
        # 어떤 종류의 키/비밀번호 입력란도 이 화면에 존재하면 안 된다.
        await user.should_not_see(kind=ui.input)


async def test_changing_the_language_rebuilds_the_bottom_navigation():
    async with user_simulation(build_workspace) as user:
        await user.open("/")
        await user.should_see("만들기")

        user.find(marker="open-settings").click()
        user.find(marker="settings-language").click()
        user.find("English").click()
        user.find(marker="settings-save").click()

        # 서버 재시작 없이 같은 세션에서 문구가 바뀐다.
        await user.should_see("Create")
        await user.should_see("Polish")
        await user.should_see("Publish")
        await user.should_not_see("만들기")


async def test_dark_theme_turns_on_the_quasar_dark_toggle():
    def dark_page() -> None:
        theme.apply("dark")

    async with user_simulation(dark_page) as user:
        await user.open("/")
        with user.client:
            dark_mode = next(iter(user.find(kind=ui.dark_mode).elements))
        assert dark_mode.value is True


def test_unknown_theme_falls_back_to_light():
    assert theme.normalize_theme("dark") == "dark"
    assert theme.normalize_theme("sepia") == "light"
    assert theme.normalize_theme(None) == "light"


def test_user_storage_defaults_carry_no_credentials():
    assert set(STORAGE_DEFAULTS) == {
        "language",
        "theme",
        "engine",
        "last_area",
        "create_input",
        "polish_input",
    }
    assert STORAGE_DEFAULTS["language"] == "ko"
    assert STORAGE_DEFAULTS["engine"] == "Grok CLI"
    forbidden = ("key", "token", "secret", "password", "credential")
    assert not [name for name in STORAGE_DEFAULTS if any(w in name for w in forbidden)]


def test_engine_options_are_local_clis_plus_demo_only():
    assert ENGINE_OPTIONS == ("Grok CLI", "Claude CLI", "Codex CLI", "Demo")


def test_copy_uses_the_workspace_mapping_and_falls_back_to_i18n():
    assert copy("nav_create", "ko") == "만들기"
    assert copy("nav_polish", "en") == "Polish"
    assert copy("nav_publish", "ja") == "公開"
    # 워크스페이스 매핑에 없는 키는 기존 i18n 사전으로 위임한다.
    assert copy("app_title", "en") == "Dongpirang Cat Grok 𝕏"
    # 알 수 없는 언어는 한국어로 떨어진다.
    assert copy("nav_create", "fr") == "만들기"


def test_theme_css_covers_both_modes_and_mobile_safe_area():
    assert ":root" in WORKSPACE_CSS
    assert "body.workspace-dark" in WORKSPACE_CSS
    assert "env(safe-area-inset-bottom" in WORKSPACE_CSS
