"""워치독이 Funnel(공개) 대신 Tailscale Serve(사설)로 두 앱을 붙이는지 검증한다.

이 노드에는 :443(→8790)과 :8443(→ai-trader 8502)이 함께 붙어 있다.
`tailscale serve reset` / `tailscale funnel reset` 은 포트를 가리지 않고 전부
지우므로 스크립트 어디에도 그 형태가 남아 있으면 안 된다. 포트 단위 명령만 쓴다.

:10000 은 예전에 Funnel(공개)로 열려 있었다. 사설 전환 때 한 번은 꺼야 하지만,
매 실행마다 무조건 끄면 serve 핸들러까지 함께 지워져서 1시간마다 접속이 끊긴다.
그래서 AllowFunnel 항목이 실제로 남아 있을 때만 끄는 가드를 요구한다.

앱 쪽은 접속 비밀번호 게이트와 쿠키 영속화가 사라졌는지 본다 — 노출 경계가
테일넷으로 옮겨갔으므로 앱 자체 게이트는 중복이고, 쿠키 컴포넌트(iframe)는
탭 점프 버그의 원인이었다.
"""

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WATCH_SCRIPT = REPO / "scripts" / "tunnel_watch.sh"
APP_ENTRY = REPO / "app.py"
REQUIREMENTS = REPO / "requirements.txt"

WORKSPACE_SERVE_CMD = 'serve --bg --https="$WORKSPACE_PORT" "http://127.0.0.1:$NICEGUI_PORT"'
LEGACY_SERVE_CMD = 'serve --bg --https="$LEGACY_PORT" "http://127.0.0.1:$LEGACY_APP_PORT"'
FUNNEL_OFF_CMD = 'funnel --https="$WORKSPACE_PORT" off'


def _script() -> str:
    return WATCH_SCRIPT.read_text(encoding="utf-8")


def _app_source() -> str:
    return APP_ENTRY.read_text(encoding="utf-8")


class TestServePorts:
    def test_watchdog_declares_local_and_serve_ports(self):
        script = _script()
        assert "NICEGUI_PORT=8080" in script
        assert "LEGACY_APP_PORT=8501" in script
        assert "WORKSPACE_PORT=10000" in script
        assert "LEGACY_PORT=10001" in script

    def test_watchdog_configures_both_private_serve_endpoints(self):
        script = _script()
        assert WORKSPACE_SERVE_CMD in script
        assert LEGACY_SERVE_CMD in script
        assert script.count('"$TS_BIN" serve --bg') == 2

    def test_watchdog_starts_both_local_apps(self):
        script = _script()
        assert 'NICEGUI_PORT="$NICEGUI_PORT" nohup "$PYTHON" nicegui_app.py' in script
        assert '"$LOG_DIR/nicegui.log"' in script
        assert '-m streamlit run app.py' in script
        assert '--server.port "$LEGACY_APP_PORT"' in script

    def test_watchdog_records_both_urls_and_drops_funnel_url_file(self):
        script = _script()
        assert "workspace.url" in script
        assert "legacy.url" in script
        assert "funnel.url" not in script


class TestNoPublicExposure:
    def test_watchdog_never_enables_funnel(self):
        """Funnel 활성화(--bg)가 남아 있으면 앱이 다시 공개로 열린다."""
        assert "funnel --bg" not in _script()

    def test_watchdog_never_resets_tailscale_config(self):
        """reset 계열은 :443/:8443 형제 서비스까지 통째로 날린다."""
        script = _script()
        assert "serve reset" not in script
        assert "funnel reset" not in script
        assert "--reset" not in script

    def test_funnel_off_is_guarded_by_allowfunnel_probe(self):
        script = _script()
        assert FUNNEL_OFF_CMD in script, "구 Funnel(:10000)을 끄는 명령이 없다"
        assert "AllowFunnel" in script, "AllowFunnel 확인 없이 끄면 매시간 serve가 지워진다"
        assert "serve status --json" in script

        lines = script.splitlines()
        off_lines = [i for i, line in enumerate(lines) if FUNNEL_OFF_CMD in line]
        assert len(off_lines) == 1
        off_idx = off_lines[0]
        assert lines[off_idx].startswith((" ", "\t")), (
            "funnel off 가 무조건 실행된다 — 조건 블록 안으로 들여써야 한다"
        )
        assert any(
            line.strip().startswith("if ") for line in lines[:off_idx]
        ), "funnel off 앞에 조건 가드가 없다"

        allow_idx = next(i for i, line in enumerate(lines) if "AllowFunnel" in line)
        assert allow_idx < off_idx, "가드 조회가 off 명령보다 뒤에 있다"


class TestPreservedWatchdogPolicy:
    def test_launchd_path_export_survives(self):
        assert 'export PATH="$HOME/.npm-global/bin:' in _script()

    def test_sleep_window_policy_survives(self):
        assert "10#$HOUR_NOW < 7" in _script()

    def test_single_admin_notification_without_password_copy(self):
        script = _script()
        assert script.count("notify_admin.py") == 1, "URL 변경 알림은 한 번만 나가야 한다"
        assert "비밀번호" not in script, "앱 비밀번호를 안내하는 옛 문구가 남아 있다"
        assert "워크스페이스" in script and "레거시" in script


class TestLegacyStreamlitEntry:
    def test_no_password_gate_or_cookie_component(self):
        source = _app_source()
        assert "APP_ACCESS_PASSWORD" not in source
        assert "CookieManager" not in source
        assert "extra_streamlit_components" not in source
        assert "access_auth" not in source

    def test_api_key_input_stays_session_only(self):
        source = _app_source()
        assert 'saved_key = ""' in source
        assert "api_key = _untracked_text_input(" in source
        assert "cookie_manager" not in source
        assert "remember_key" not in source

    def test_access_auth_module_and_test_are_deleted(self):
        assert not (REPO / "access_auth.py").exists()
        assert not (REPO / "tests" / "test_access_auth.py").exists()

    def test_cookie_component_dependency_dropped(self):
        assert "extra-streamlit-components" not in REQUIREMENTS.read_text(encoding="utf-8")
