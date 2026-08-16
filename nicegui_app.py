"""동피랑고양이 모바일 워크스페이스 진입점 — 루프백에만 바인딩한다.

외부 노출은 Tailscale Serve 가 앞단에서 담당한다. 이 프로세스는 127.0.0.1
밖으로 나가지 않는다. 임포트만으로는 아무 일도 일어나지 않으며, 서버는
__main__ 으로 실행할 때만 뜬다(테스트가 이 모듈을 안전하게 임포트한다).

    NICEGUI_PORT=8080 venv/bin/python nicegui_app.py
"""

from __future__ import annotations

import os

from nicegui import ui

from workspace_settings import load_or_create_storage_secret
from workspace_ui.app import build_workspace


DEFAULT_PORT = 8080

# 루프백 고정. 이 값을 바꾸면 앱이 테일넷 밖으로 열린다.
HOST = "127.0.0.1"


def configured_port() -> int:
    """NICEGUI_PORT 를 읽는다. 비었거나 숫자가 아니면 기본 포트."""
    raw = os.environ.get("NICEGUI_PORT", "")
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_PORT


def run(port: int = DEFAULT_PORT) -> None:
    ui.run(
        root=build_workspace,
        host=HOST,
        port=port,
        reload=False,
        storage_secret=load_or_create_storage_secret(),
        reconnect_timeout=15.0,
        message_history_length=1000,
        title="동피랑고양이 워크스페이스",
        favicon="🐾",
        show=False,
        show_welcome_message=False,
    )


if __name__ == "__main__":
    run(configured_port())
