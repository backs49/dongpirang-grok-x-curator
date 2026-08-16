from __future__ import annotations

import pytest

import workspace_jobs


def test_claim_allows_one_worker_and_restores_terminal_result(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수", "mode": "builder_note"},
        engine="Grok CLI", language="ko", path=path,
    )
    assert workspace_jobs.claim_job(job["id"], path=path)["status"] == "running"
    assert workspace_jobs.claim_job(job["id"], path=path) is None
    workspace_jobs.complete_job(job["id"], {"directions": []}, path=path)
    assert workspace_jobs.get_job(job["id"], path=path)["status"] == "completed"


def test_create_job_stores_request_engine_and_language_snapshot(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "post",
        {"keywords": "배포", "direction": {"title": "A"}, "length": 280, "mode": "auto"},
        engine="Codex CLI",
        language="en",
        path=path,
    )

    assert job["status"] == "queued"
    assert job["kind"] == "post"
    assert job["engine"] == "Codex CLI"
    assert job["language"] == "en"
    assert job["request"] == {
        "keywords": "배포", "direction": {"title": "A"}, "length": 280, "mode": "auto",
    }


def test_create_job_rejects_unknown_kind(tmp_path):
    path = tmp_path / "workspace_jobs.json"

    with pytest.raises(ValueError):
        workspace_jobs.create_job(
            "summary", {"text": "x"}, engine="Grok CLI", language="ko", path=path
        )

    assert not path.exists()


def test_create_job_rejects_blank_request(tmp_path):
    path = tmp_path / "workspace_jobs.json"

    with pytest.raises(ValueError):
        workspace_jobs.create_job("optimize", {}, engine="Grok CLI", language="ko", path=path)

    assert not path.exists()


def test_complete_and_fail_are_recoverable_after_reload(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    complete = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko", path=path
    )
    failed = workspace_jobs.create_job(
        "post",
        {"keywords": "AI", "direction": {}, "length": 0, "mode": "auto"},
        engine="Claude CLI",
        language="ko",
        path=path,
    )

    workspace_jobs.complete_job(complete["id"], {"optimized_post": "고친 글"}, path=path)
    workspace_jobs.fail_job(failed["id"], "provider down", path=path)

    restored_complete = workspace_jobs.get_job(complete["id"], path=path)
    restored_failed = workspace_jobs.get_job(failed["id"], path=path)
    assert restored_complete["status"] == "completed"
    assert restored_complete["result"] == {"optimized_post": "고친 글"}
    assert "error" not in restored_complete
    assert restored_failed["status"] == "failed"
    assert restored_failed["error"] == "provider down"
    assert "result" not in restored_failed


def test_unknown_job_is_not_returned_or_mutated(tmp_path):
    path = tmp_path / "workspace_jobs.json"

    assert workspace_jobs.get_job("unknown", path=path) is None
    assert workspace_jobs.claim_job("unknown", path=path) is None
    assert workspace_jobs.complete_job("unknown", {"optimized_post": "x"}, path=path) is None
    assert workspace_jobs.fail_job("unknown", "boom", path=path) is None


def test_job_store_rejects_non_json_serializable_request(tmp_path):
    """request 는 JSON 직렬화 가능한 평범한 데이터여야 한다 — API 키/쿠키/객체를
    담은 프로바이더 같은 것을 실수로 저장소에 흘려보내지 않도록 방어한다."""
    path = tmp_path / "workspace_jobs.json"

    class NotSerializable:
        pass

    with pytest.raises(ValueError):
        workspace_jobs.create_job(
            "optimize", {"text": "원문", "provider": NotSerializable()},
            engine="Grok CLI", language="ko", path=path,
        )
