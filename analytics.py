"""Google Analytics 4 주입 — Streamlit Community Cloud 호환.

st.components.v1.html 은 sandboxed iframe 안에서 실행돼 부모 페이지 방문을
추적할 수 없다. 대신 Streamlit 패키지의 static/index.html 을 컨테이너
시작 시점에 한 번만 패치해 GA4 스니펫을 <head> 에 주입한다.
"""

from __future__ import annotations

import pathlib

import streamlit as st

_GA_MARKER = "<!-- GA4_INJECTED -->"


def inject_ga4() -> None:
    try:
        measurement_id = st.secrets["GA_MEASUREMENT_ID"]
    except (KeyError, FileNotFoundError):
        return
    if not measurement_id:
        return

    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    try:
        html = index_path.read_text(encoding="utf-8")
    except OSError:
        return

    if _GA_MARKER in html:
        return

    snippet = (
        f"{_GA_MARKER}\n"
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{measurement_id}');\n"
        "</script>\n"
    )

    patched = html.replace("<head>", "<head>\n" + snippet, 1)
    try:
        index_path.write_text(patched, encoding="utf-8")
    except OSError:
        return
