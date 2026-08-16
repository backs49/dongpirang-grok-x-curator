from __future__ import annotations

import idea_jobs
import idea_job_runner


def test_submit_creates_job_then_starts_detached_worker(tmp_path):
    started = []

    job = idea_job_runner.submit_job(
        "AI",
        280,
        "auto",
        "Codex CLI",
        jobs_path=tmp_path / "idea_jobs.json",
        popen=lambda args, **kwargs: started.append((args, kwargs)),
    )

    assert job["status"] == "queued"
    assert started[0][0][-2:] == ["--job-id", job["id"]]
    assert started[0][1]["start_new_session"] is True
    assert started[0][1]["cwd"] == idea_job_runner.REPO_ROOT


def test_submit_records_spawn_failure_in_the_job(tmp_path):
    path = tmp_path / "idea_jobs.json"

    def failing_popen(*args, **kwargs):
        raise OSError("worker could not start")

    job = idea_job_runner.submit_job(
        "AI", 0, "auto", "Grok CLI", jobs_path=path, popen=failing_popen
    )

    assert job["status"] == "failed"
    assert job["error"] == "worker could not start"
    assert idea_jobs.get_job(job["id"], path=path)["status"] == "failed"
