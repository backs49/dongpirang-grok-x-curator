"""agy CLI 프로바이더 테스트 (D-012: plan+sandbox, 빈 임시 폴더, 봉투 언랩)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from providers.agy_cli import DEFAULT_AGY_MODEL, AgyCliProvider

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env(response, **extra) -> str:
    return json.dumps({"conversation_id": "x", "status": "SUCCESS", "response": response, **extra})


def _ok(stdout):
    return MagicMock(returncode=0, stdout=stdout, stderr="")


def _after(cmd, flag):
    return cmd[cmd.index(flag) + 1]


@patch("providers.cli.subprocess.run")
def test_command_flags_and_tempdir_cwd(mock_run):
    mock_run.return_value = _ok(_env('{"a": 1}'))
    AgyCliProvider().generate_json("S", "U", timeout=30)
    cmd = mock_run.call_args.args[0]
    assert cmd[:2] == ["agy", "-p"]
    assert _after(cmd, "--mode") == "plan"
    assert "--sandbox" in cmd
    assert _after(cmd, "--output-format") == "json"
    assert _after(cmd, "--model") == DEFAULT_AGY_MODEL
    # agy 가 스스로 끝낼 여유를 둔다 — 같은 순간에 강제 종료하면 토큰 갱신 중에 죽을 수 있다
    assert _after(cmd, "--print-timeout") == "20s"
    assert mock_run.call_args.kwargs["timeout"] == 30
    cwd = mock_run.call_args.kwargs["cwd"]
    assert cwd and Path(cwd).resolve() != REPO_ROOT
    assert os.path.exists(cwd) is False  # 호출이 끝나면 임시 폴더는 지워진다


@patch("providers.cli.subprocess.run")
def test_unwraps_plain_json_response(mock_run):
    mock_run.return_value = _ok(_env('{"score": 88}'))
    assert AgyCliProvider().generate_json("S", "U") == {"score": 88}


@patch("providers.cli.subprocess.run")
def test_unwraps_fenced_json_in_response(mock_run):
    mock_run.return_value = _ok(_env('```json\n{"a": 1}\n```'))
    assert AgyCliProvider().generate_json("S", "U") == {"a": 1}


@patch("providers.cli.subprocess.run")
def test_parses_last_envelope_line_after_noise(mock_run):
    mock_run.return_value = _ok("jetski: note\n" + _env('{"a": 1}'))
    assert AgyCliProvider().generate_json("S", "U") == {"a": 1}


@patch("providers.cli.subprocess.run")
def test_empty_response_is_error(mock_run):
    mock_run.return_value = _ok(_env(""))
    result = AgyCliProvider().generate_json("S", "U")
    assert result["error"].startswith("agy CLI error")


@patch("providers.cli.subprocess.run")
def test_denied_actions_is_error(mock_run):
    mock_run.return_value = _ok(_env("", denied_actions=[{"action": "command"}]))
    assert "command" in AgyCliProvider().generate_json("S", "U")["error"]


@patch("providers.cli.subprocess.run")
def test_non_success_status_is_error(mock_run):
    mock_run.return_value = _ok(_env('{"a": 1}', status="ERROR"))
    assert "error" in AgyCliProvider().generate_json("S", "U")


@patch("providers.cli.subprocess.run")
def test_missing_envelope_is_error(mock_run):
    mock_run.return_value = _ok("garbage")
    result = AgyCliProvider().generate_json("S", "U")
    assert result["error"].startswith("agy CLI error")


@patch("providers.cli.subprocess.run")
def test_timeout_returns_error_and_cleans_tempdir(mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired("agy", 1)
    result = AgyCliProvider().generate_json("S", "U", timeout=1)
    assert "timed out" in result["error"]
    assert os.path.exists(mock_run.call_args.kwargs["cwd"]) is False


@patch("providers.cli.subprocess.run")
def test_effort_comes_only_from_model_id_suffix(mock_run):
    # 설계: effort 장치는 하나만. 모델 id 접미사(-low)를 쓰고 --effort 는 넘기지 않는다.
    from grok_client import GrokClient

    mock_run.return_value = _ok(_env('{"a": 1}'))
    provider = AgyCliProvider()
    GrokClient(provider=provider)._write_json("S", "U")
    assert "--effort" not in mock_run.call_args.args[0]
    assert DEFAULT_AGY_MODEL.endswith("-low")


@patch("providers.cli.subprocess.run")
def test_generate_text_returns_response_or_error_string(mock_run):
    mock_run.return_value = _ok(_env("안녕"))
    assert AgyCliProvider().generate_text("S", "U") == "안녕"
    mock_run.return_value = _ok(_env(""))
    assert AgyCliProvider().generate_text("S", "U").startswith("agy CLI error")


def test_workspace_engine_options_include_agy():
    from workspace_ui.app import ENGINE_OPTIONS

    assert "agy CLI" in ENGINE_OPTIONS
    assert ENGINE_OPTIONS[0] == "Grok CLI"


def test_calls_are_serialized_across_open_handles(tmp_path, monkeypatch):
    # 2026-11-22: 병렬 8개 호출 중 agy 로그인이 풀렸다. 워커는 프로세스마다 따로
    # 돌기 때문에 파일 잠금으로 한 번에 하나만 부른다.
    import threading
    import time

    import providers.agy_cli as agy

    monkeypatch.setattr(agy, "AGY_LOCK_PATH", tmp_path / "agy.lock")
    spans = []

    def fake_run(self, cmd, *, timeout, cwd=None):
        start = time.monotonic()
        time.sleep(0.2)
        spans.append((start, time.monotonic()))
        return 0, _env('{"a": 1}'), ""

    monkeypatch.setattr(agy.AgyCliProvider, "_run", fake_run)
    threads = [threading.Thread(target=AgyCliProvider().generate_json, args=("S", "U")) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    (s1, e1), (s2, e2) = sorted(spans)
    assert s2 >= e1  # 두 번째 호출은 첫 호출이 끝난 뒤에 시작한다


def test_lock_wait_is_bounded_by_timeout(tmp_path, monkeypatch):
    import fcntl
    import time

    import providers.agy_cli as agy

    lock_path = tmp_path / "agy.lock"
    monkeypatch.setattr(agy, "AGY_LOCK_PATH", lock_path)
    called = []
    monkeypatch.setattr(agy.AgyCliProvider, "_run", lambda self, *a, **k: called.append(1))
    with open(lock_path, "a") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)  # 다른 호출이 잠금을 쥐고 안 놓는 상황
        start = time.monotonic()
        result = AgyCliProvider().generate_json("S", "U", timeout=1)
        elapsed = time.monotonic() - start
    assert result["error"].startswith("agy CLI error")
    assert "다른 agy 호출" in result["error"]
    assert elapsed < 3
    assert called == []
