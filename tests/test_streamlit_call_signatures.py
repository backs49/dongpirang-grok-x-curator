"""레거시 Streamlit 화면이 설치된 Streamlit이 받지 않는 인자를 넘기지 않는지 확인."""

import ast
import inspect
from pathlib import Path

import pytest
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [ROOT / "app.py", *sorted((ROOT / "tabs").glob("*.py"))]


def _st_calls():
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "st"
            ):
                yield path.name, node.lineno, node.func.attr, node


@pytest.mark.parametrize("source", SOURCES, ids=lambda p: p.name)
def test_st_calls_use_supported_keywords(source):
    problems = []
    for name, lineno, attr, node in _st_calls():
        if name != source.name:
            continue
        func = getattr(st, attr, None)
        if func is None:
            problems.append(f"{name}:{lineno} st.{attr} 없음")
            continue
        try:
            params = inspect.signature(func).parameters
        except (TypeError, ValueError):
            continue
        if any(p.kind is p.VAR_KEYWORD for p in params.values()):
            continue
        for kw in node.keywords:
            if kw.arg is not None and kw.arg not in params:
                problems.append(f"{name}:{lineno} st.{attr}(..., {kw.arg}=)")
    assert not problems, problems
