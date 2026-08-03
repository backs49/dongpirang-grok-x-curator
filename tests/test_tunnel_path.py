"""tunnel_watch.sh 가 export 하는 PATH 로 CLI 프로바이더가 실제로 찾아지는지 검증한다.

launchd 는 최소 PATH(/usr/bin:/bin:/usr/sbin:/sbin)만 물려준다. 워치독이
streamlit 을 띄우므로 앱 프로세스도 그 PATH 를 상속받고, shutil.which() 로
CLI 를 찾는 프로바이더는 워치독이 추가한 디렉터리에서만 CLI 를 볼 수 있다.

2026-07-19 에 ~/.npm-global/bin 만 추가했는데(claude/codex 는 거기 있음)
같은 날 저녁 기본 엔진이 Grok CLI 로 바뀌었다. grok 은 ~/.local/bin 에
있어서 launchd 기동 시 "grok CLI not found" 가 됐다. 이 테스트가 그 회귀를
잡는다.

머신에 설치되지 않은 CLI 는 건너뛴다 — CI 나 다른 개발 머신에서 강제로
실패시키지 않기 위해서다.
"""

import os
import re
import shutil
from pathlib import Path

import pytest

from providers.claude_cli import ClaudeCliProvider
from providers.codex_cli import CodexCliProvider
from providers.codex_cli_image import CodexCliImageProvider
from providers.grok_cli import GrokCliProvider
from providers.grok_cli_media import GrokCliImageProvider, GrokCliVideoProvider

WATCH_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "tunnel_watch.sh"

# launchd 가 물려주는 최소 PATH.
LAUNCHD_MINIMAL_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"

CLI_PROVIDERS = [
    ClaudeCliProvider,
    CodexCliProvider,
    CodexCliImageProvider,
    GrokCliProvider,
    GrokCliImageProvider,
    GrokCliVideoProvider,
]


def _watchdog_path() -> str:
    """tunnel_watch.sh 의 export PATH 줄을 launchd 환경 기준으로 전개한다."""
    script = WATCH_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r'^export PATH="([^"]+)"', script, re.MULTILINE)
    assert match, "tunnel_watch.sh 에 export PATH 줄이 없다"
    raw = match.group(1)
    expanded = raw.replace("$HOME", os.path.expanduser("~"))
    expanded = expanded.replace("$PATH", LAUNCHD_MINIMAL_PATH)
    return expanded


def _commands() -> list[str]:
    return sorted({cls.command for cls in CLI_PROVIDERS if cls.command})


class TestWatchdogPath:
    def test_export_path_line_exists(self):
        assert WATCH_SCRIPT.is_file()
        assert _watchdog_path()

    def test_launchd_minimal_path_alone_is_insufficient(self):
        """전제 확인: 최소 PATH 만으로는 CLI 를 못 찾는다 (그래서 export 가 필요)."""
        installed = [c for c in _commands() if shutil.which(c)]
        if not installed:
            pytest.skip("이 머신에 설치된 CLI 프로바이더가 없다")
        assert not any(
            shutil.which(c, path=LAUNCHD_MINIMAL_PATH) for c in installed
        ), "최소 PATH 로도 CLI 가 찾아진다면 이 테스트의 전제가 틀렸다"

    @pytest.mark.parametrize("command", _commands())
    def test_installed_cli_is_reachable_from_watchdog_path(self, command):
        if not shutil.which(command):
            pytest.skip(f"{command} CLI 가 이 머신에 설치돼 있지 않다")
        resolved = shutil.which(command, path=_watchdog_path())
        assert resolved, (
            f"{command} 은 설치돼 있지만 tunnel_watch.sh 의 PATH 로는 찾을 수 없다. "
            f"launchd 로 기동된 앱에서 '{command} CLI not found' 가 된다. "
            f"설치 위치: {shutil.which(command)}"
        )
