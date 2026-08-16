from __future__ import annotations

from tabs.tab_ideas import _apply_terminal_job_state
from xalgo_prompts import PROMPT_VERSION


def test_completed_job_restores_result_once_into_session_state():
    state = {}
    job = {
        "id": "job-1",
        "status": "completed",
        "result": {"ideas": [{"content": "복원된 포스트"}]},
    }

    assert _apply_terminal_job_state(job, state) == "completed"
    assert state["ideas_result"] == job["result"]
    assert state["ideas_prompt_version"] == PROMPT_VERSION
    assert _apply_terminal_job_state(job, state) is None


def test_failed_job_restores_error_once_into_session_state():
    state = {}
    job = {"id": "job-2", "status": "failed", "error": "OAuth session expired"}

    assert _apply_terminal_job_state(job, state) == "failed"
    assert state["ideas_error"] == "OAuth session expired"
    assert _apply_terminal_job_state(job, state) is None


def test_non_terminal_job_does_not_change_session_state():
    state = {"ideas_result": {"ideas": []}}

    assert _apply_terminal_job_state({"id": "job-3", "status": "running"}, state) is None
    assert state == {"ideas_result": {"ideas": []}}
