from __future__ import annotations

import subprocess
import sys

import workspace_jobs
import workspace_job_runner


def test_submit_creates_job_then_starts_detached_worker(tmp_path):
    started = []

    job = workspace_job_runner.submit_job(
        "directions",
        {"keywords": "AI", "mode": "auto"},
        engine="Codex CLI",
        language="ko",
        jobs_path=tmp_path / "workspace_jobs.json",
        popen=lambda args, **kwargs: started.append((args, kwargs)),
    )

    assert job["status"] == "queued"
    assert started[0][0][0] == sys.executable
    assert started[0][0][-2:] == ["--job-id", job["id"]]
    assert started[0][1]["start_new_session"] is True
    assert started[0][1]["cwd"] == workspace_job_runner.REPO_ROOT


def test_submit_sends_both_streams_to_devnull(tmp_path):
    started = []

    workspace_job_runner.submit_job(
        "optimize",
        {"text": "원문"},
        engine="Grok CLI",
        language="ko",
        jobs_path=tmp_path / "workspace_jobs.json",
        popen=lambda args, **kwargs: started.append((args, kwargs)),
    )

    assert started[0][1]["stdout"] == subprocess.DEVNULL
    assert started[0][1]["stderr"] == subprocess.DEVNULL


def test_submit_records_spawn_failure_in_the_job(tmp_path):
    path = tmp_path / "workspace_jobs.json"

    def failing_popen(*args, **kwargs):
        raise OSError("worker could not start")

    job = workspace_job_runner.submit_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko",
        jobs_path=path, popen=failing_popen,
    )

    assert job["status"] == "failed"
    assert job["error"] == "worker could not start"
    assert workspace_jobs.get_job(job["id"], path=path)["status"] == "failed"


def test_submit_persists_request_and_engine_before_starting_worker(tmp_path):
    job = workspace_job_runner.submit_job(
        "post",
        {"keywords": "AI", "direction": {"title": "A"}, "length": 280, "mode": "auto"},
        engine="Claude CLI",
        language="en",
        jobs_path=tmp_path / "workspace_jobs.json",
        popen=lambda *args, **kwargs: None,
    )

    assert job["kind"] == "post"
    assert job["request"]["direction"] == {"title": "A"}
    assert job["engine"] == "Claude CLI"
    assert job["language"] == "en"
