"""런타임 임포트 스모크 테스트.

app.py는 테스트에서 직접 임포트하지 않으므로, 의존성 업그레이드가 만든
임포트 시한폭탄(예: altair 5.5.0의 Py3.14 TypedDict closed= 가드 버그)은
전체 스위트가 초록이어도 앱 재시작 때 터진다. 여기서 실제 임포트 체인을
미리 밟아 그 구멍을 막는다.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_import_chain_is_importable():
    import altair  # noqa: F401  (streamlit_analytics2 → altair 체인)
    import streamlit_analytics2  # noqa: F401


def test_nicegui_app_entry_is_importable():
    import nicegui_app  # noqa: F401


def test_i18n_import_does_not_load_streamlit():
    """i18n.py는 get_lang() 안에서만 streamlit을 지연 임포트해야 한다 —
    모듈 최상단에서 임포트하면 워커 프로세스마다 streamlit 임포트 비용을
    물게 되므로, 단순 `import i18n`만으로는 sys.modules에 streamlit이
    올라오지 않아야 한다. 현재 프로세스(pytest)는 streamlit을 이미
    로드했을 수 있어 검증은 반드시 서브프로세스 안에서 해야 한다."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import i18n, sys; raise SystemExit(1 if 'streamlit' in sys.modules else 0)",
        ],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0


def test_worker_import_chain_does_not_load_streamlit():
    """워커 임포트 체인(provider_selection → grok_client·providers.xai_api → i18n)도
    streamlit을 끌어오면 안 된다 — 워커 경로는 런타임에 get_lang()을 호출하지
    않으므로, 이 체인을 타는 것만으로 streamlit이 로드되면 지연 임포트가 깨진
    것이다."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import provider_selection, sys; raise SystemExit(1 if 'streamlit' in sys.modules else 0)",
        ],
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
