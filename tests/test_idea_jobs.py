from __future__ import annotations

import idea_jobs


def test_create_then_claim_records_request_and_running_status(tmp_path):
    path = tmp_path / "idea_jobs.json"

    job = idea_jobs.create_job("AI 사이드프로젝트", 280, "auto", "Codex CLI", path=path)
    claimed = idea_jobs.claim_job(job["id"], path=path)

    assert job["status"] == "queued"
    assert claimed is not None
    assert claimed["status"] == "running"
    assert claimed["keywords"] == "AI 사이드프로젝트"
    assert claimed["length"] == 280
    assert claimed["mode"] == "auto"
    assert claimed["engine"] == "Codex CLI"


def test_claim_only_allows_one_worker_for_a_job(tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", path=path)

    assert idea_jobs.claim_job(job["id"], path=path) is not None
    assert idea_jobs.claim_job(job["id"], path=path) is None


def test_complete_and_fail_are_recoverable_after_reload(tmp_path):
    path = tmp_path / "idea_jobs.json"
    complete = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", path=path)
    failed = idea_jobs.create_job("Python", 120, "tip", "Claude CLI", path=path)

    idea_jobs.complete_job(complete["id"], {"ideas": [{"content": "완성된 글"}]}, path=path)
    idea_jobs.fail_job(failed["id"], "provider down", path=path)

    restored_complete = idea_jobs.get_job(complete["id"], path=path)
    restored_failed = idea_jobs.get_job(failed["id"], path=path)
    assert restored_complete == {
        **restored_complete,
        "id": complete["id"],
        "status": "completed",
        "result": {"ideas": [{"content": "완성된 글"}]},
    }
    assert restored_failed == {
        **restored_failed,
        "id": failed["id"],
        "status": "failed",
        "error": "provider down",
    }


def test_unknown_job_is_not_returned_or_mutated(tmp_path):
    path = tmp_path / "idea_jobs.json"

    assert idea_jobs.get_job("unknown", path=path) is None
    assert idea_jobs.claim_job("unknown", path=path) is None
    assert idea_jobs.complete_job("unknown", {"ideas": []}, path=path) is None


def test_job_persists_grounded_fields(tmp_path):
    job = idea_jobs.create_job(
        "수면",
        280,
        "hankang",
        "Claude CLI",
        content_type="grounded_tip",
        tip_category="health",
        references="WHO link",
        path=tmp_path / "jobs.json",
    )

    assert (job["content_type"], job["tip_category"], job["references"]) == (
        "grounded_tip",
        "health",
        "WHO link",
    )


def test_normal_job_defaults_to_ideas_fields(tmp_path):
    job = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", path=tmp_path / "jobs.json")

    assert job["content_type"] == "ideas"
    assert job["tip_category"] == ""
    assert job["references"] == ""
