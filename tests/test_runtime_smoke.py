"""런타임 임포트 스모크 테스트.

app.py는 테스트에서 직접 임포트하지 않으므로, 의존성 업그레이드가 만든
임포트 시한폭탄(예: altair 5.5.0의 Py3.14 TypedDict closed= 가드 버그)은
전체 스위트가 초록이어도 앱 재시작 때 터진다. 여기서 실제 임포트 체인을
미리 밟아 그 구멍을 막는다.
"""


def test_streamlit_app_import_chain_is_importable():
    import altair  # noqa: F401  (streamlit_analytics2 → altair 체인)
    import streamlit_analytics2  # noqa: F401


def test_nicegui_app_entry_is_importable():
    import nicegui_app  # noqa: F401
