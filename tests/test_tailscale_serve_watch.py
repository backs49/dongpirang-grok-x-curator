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
PUBLIC_PROBE = "workspace_port_is_public"


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

    def test_funnel_off_sits_inside_the_public_port_guard(self):
        """off 명령이 정확히 `if workspace_port_is_public` 블록 안에 있어야 한다.

        "앞 어딘가에 if 가 있다" 로는 부족하다 — 다른 조건문 안에 있어도 통과하기
        때문이다. 여는 줄과 짝이 되는 `fi` 사이에 들어 있는지를 본다.
        """
        script = _script()
        assert FUNNEL_OFF_CMD in script, "구 Funnel(:10000)을 끄는 명령이 없다"
        assert "AllowFunnel" in script, "AllowFunnel 확인 없이 끄면 매시간 serve가 지워진다"
        assert "serve status --json" in script

        lines = script.splitlines()
        off_lines = [i for i, line in enumerate(lines) if FUNNEL_OFF_CMD in line]
        assert len(off_lines) == 1
        off_idx = off_lines[0]

        guard_lines = [
            i for i, line in enumerate(lines) if line.strip() == f"if {PUBLIC_PROBE}; then"
        ]
        assert len(guard_lines) == 1, f"`if {PUBLIC_PROBE}; then` 가드를 찾을 수 없다"
        guard_idx = guard_lines[0]
        guard_indent = len(lines[guard_idx]) - len(lines[guard_idx].lstrip())
        close_idx = next(
            i
            for i, line in enumerate(lines[guard_idx + 1 :], start=guard_idx + 1)
            if line.strip() == "fi"
            and len(line) - len(line.lstrip()) == guard_indent
        )
        assert guard_idx < off_idx < close_idx, (
            "funnel off 가 공개 여부 가드 블록 밖에 있다 — 매시간 serve 핸들러가 지워진다"
        )

        allow_idx = next(i for i, line in enumerate(lines) if "AllowFunnel" in line)
        assert allow_idx < off_idx, "가드 조회가 off 명령보다 뒤에 있다"

    def test_guarded_teardown_is_actually_invoked(self):
        """정의만 해두고 부르지 않으면 공개 상태가 영원히 남는다."""
        lines = _script().splitlines()
        calls = [line for line in lines if line.strip() == "disable_workspace_funnel"]
        assert len(calls) == 1, "disable_workspace_funnel 호출이 정확히 한 번이어야 한다"
        assert not calls[0].startswith((" ", "\t")), (
            "스크립트 본문(최상위)에서 호출되지 않는다"
        )

        call_idx = lines.index(calls[0])
        serve_idx = next(i for i, line in enumerate(lines) if WORKSPACE_SERVE_CMD in line)
        serve_call_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "ensure_workspace_serve"
        )
        assert call_idx < serve_call_idx, (
            "funnel off 는 serve 설정보다 먼저 돌아야 한다 — off 가 웹 핸들러까지 지우기 때문"
        )
        assert serve_idx != call_idx

    def test_blind_probe_is_logged(self):
        """AllowFunnel 블록이 아예 안 보이면 파서가 깨진 것일 수 있다 — 조용히 넘기지 않는다."""
        script = _script()
        assert 'grep -q \'"AllowFunnel"\'' in script
        assert "funnel probe may be blind" in script


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
