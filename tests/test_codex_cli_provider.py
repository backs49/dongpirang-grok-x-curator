"""Codex CLI 텍스트 프로바이더 테스트 — subprocess 를 목으로 대체한다."""

from __future__ import annotations

import subprocess
from pathlib import Path

import providers.codex_cli as codex_mod
from providers.codex_cli import CodexCliProvider


def _fake_run_writing(payload: str, *, returncode: int = 0, stderr: str = ""):
    """codex exec 이 -o 파일에 최종 메시지를 쓰는 동작을 흉내낸다."""

    def fake_run(cmd, **kwargs):
        assert cmd[0] == "codex"
        assert cmd[1] == "exec"
        assert "--ephemeral" in cmd
        assert "read-only" in cmd
        assert cmd[cmd.index("-m") + 1] == "gpt-6-luna"
        assert any(c.startswith("model_reasoning_effort=") for c in cmd)
        out_idx = cmd.index("-o") + 1
        if returncode == 0:
            Path(cmd[out_idx]).write_text(payload, encoding="utf-8")

        class R:
            pass

        R.returncode = returncode
        R.stdout = "tokens used\n12,345\n"
        R.stderr = stderr
        return R()

    return fake_run


class TestCodexCliProvider:
    def test_is_available(self, monkeypatch):
        monkeypatch.setattr(codex_mod.shutil, "which", lambda _: "/usr/bin/codex")
        assert CodexCliProvider().is_available().available

    def test_generate_json_reads_last_message_file(self, monkeypatch):
        monkeypatch.setattr(
            codex_mod.subprocess, "run", _fake_run_writing('{"score": 88}')
        )
        result = CodexCliProvider().generate_json("system", "user")
        assert result == {"score": 88}

    def test_generate_json_extracts_from_noisy_output(self, monkeypatch):
        monkeypatch.setattr(
            codex_mod.subprocess,
            "run",
            _fake_run_writing('Here is the result:\n{"score": 42}\nDone.'),
        )
        result = CodexCliProvider().generate_json("system", "user")
        assert result == {"score": 42}

    def test_generate_json_error_on_nonzero_exit(self, monkeypatch):
        monkeypatch.setattr(
            codex_mod.subprocess,
            "run",
            _fake_run_writing("", returncode=1, stderr="not logged in"),
        )
        result = CodexCliProvider().generate_json("system", "user")
        assert "error" in result
        assert "not logged in" in result["error"]

    def test_generate_text(self, monkeypatch):
        monkeypatch.setattr(
            codex_mod.subprocess, "run", _fake_run_writing("  plain answer  ")
        )
        assert CodexCliProvider().generate_text("system", "user") == "plain answer"

    def test_timeout_returns_error_dict(self, monkeypatch):
        def fake_run(cmd, **kwargs):
            raise codex_mod.subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

        monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
        result = CodexCliProvider().generate_json("system", "user")
        assert "error" in result
        assert "timed out" in result["error"]


def test_codex_writing_calls_use_low_and_analysis_keeps_medium(monkeypatch):
    from grok_client import GrokClient
    from providers import codex_cli

    seen = []

    def fake_run(cmd, **kw):
        seen.append(cmd)
        Path(cmd[cmd.index("-o") + 1]).write_text('{"posts": [{"content": "x"}]}', encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)
    provider = codex_cli.CodexCliProvider()
    GrokClient(provider=provider).write_from_memo("테슬라", language="ko")
    provider.generate_json("s", "u")
    assert 'model_reasoning_effort="low"' in seen[0]
    assert 'model_reasoning_effort="medium"' in seen[1]
    assert seen[0][seen[0].index("-m") + 1] == "gpt-6-luna"
