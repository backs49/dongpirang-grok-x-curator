from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

import workspace_jobs


def _rewrite_job(path, job_id, **updates):
    """저장된 잡 레코드를 직접 고쳐 과거 시각·깨진 값 같은 상태를 만든다."""
    data = json.loads(path.read_text(encoding="utf-8"))
    for job in data["jobs"]:
        if job["id"] == job_id:
            job.update(updates)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _stamp(delta: timedelta) -> str:
    return (datetime.now() - delta).isoformat(timespec="seconds")


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


def test_prune_removes_terminal_jobs_older_than_ttl(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    old = workspace_jobs.create_job(
        "optimize", {"text": "옛글"}, engine="Grok CLI", language="ko", path=path
    )
    workspace_jobs.complete_job(old["id"], {"optimized_post": "x"}, path=path)
    _rewrite_job(
        path, old["id"],
        updated_at=_stamp(timedelta(days=workspace_jobs.PRUNE_TTL_DAYS, hours=1)),
    )

    fresh = workspace_jobs.create_job(
        "optimize", {"text": "새글"}, engine="Grok CLI", language="ko", path=path
    )

    assert workspace_jobs.get_job(old["id"], path=path) is None
    assert workspace_jobs.get_job(fresh["id"], path=path) is not None


def test_prune_never_removes_pending_jobs_regardless_of_age(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    stale = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )
    _rewrite_job(path, stale["id"], updated_at=_stamp(timedelta(days=365)))

    workspace_jobs.create_job(
        "optimize", {"text": "다른 요청"}, engine="Grok CLI", language="ko", path=path
    )

    assert workspace_jobs.get_job(stale["id"], path=path) is not None


def test_prune_keeps_terminal_jobs_with_unparseable_timestamps(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    done = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko", path=path
    )
    workspace_jobs.complete_job(done["id"], {"optimized_post": "x"}, path=path)
    _rewrite_job(path, done["id"], updated_at="not-a-date")

    workspace_jobs.create_job(
        "optimize", {"text": "새 요청"}, engine="Grok CLI", language="ko", path=path
    )

    assert workspace_jobs.get_job(done["id"], path=path) is not None


def test_prune_caps_terminal_jobs_keeping_newest(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace_jobs, "PRUNE_MAX_TERMINAL", 2)
    path = tmp_path / "workspace_jobs.json"
    ids = []
    for i in range(4):
        job = workspace_jobs.create_job(
            "optimize", {"text": f"글{i}"}, engine="Grok CLI", language="ko", path=path
        )
        workspace_jobs.complete_job(job["id"], {"optimized_post": "x"}, path=path)
        _rewrite_job(path, job["id"], updated_at=_stamp(timedelta(minutes=40 - i * 10)))
        ids.append(job["id"])

    workspace_jobs.create_job(
        "optimize", {"text": "트리거"}, engine="Grok CLI", language="ko", path=path
    )

    assert workspace_jobs.get_job(ids[0], path=path) is None
    assert workspace_jobs.get_job(ids[1], path=path) is None
    assert workspace_jobs.get_job(ids[2], path=path) is not None
    assert workspace_jobs.get_job(ids[3], path=path) is not None


def test_prune_keeps_idless_pending_job_next_to_idless_stale_terminal(tmp_path):
    """id 가 빠진 기형 레코드가 섞여도 pending 잡은 절대 지워지면 안 된다 —
    id 필드 기반 제거는 None 키 충돌로 이 불변식을 깼었다."""
    path = tmp_path / "workspace_jobs.json"
    stale_terminal = {
        "status": "completed", "kind": "optimize",
        "created_at": _stamp(timedelta(days=30)), "updated_at": _stamp(timedelta(days=30)),
        "request": {"text": "옛글"}, "engine": "Grok CLI", "language": "ko",
    }
    idless_pending = {
        "status": "queued", "kind": "directions",
        "created_at": _stamp(timedelta(days=30)), "updated_at": _stamp(timedelta(days=30)),
        "request": {"keywords": "고양이"}, "engine": "Grok CLI", "language": "ko",
    }
    path.write_text(
        json.dumps({"jobs": [stale_terminal, idless_pending]}, ensure_ascii=False),
        encoding="utf-8",
    )

    workspace_jobs.create_job(
        "optimize", {"text": "새 요청"}, engine="Grok CLI", language="ko", path=path
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    statuses = [job["status"] for job in data["jobs"]]
    assert "queued" in statuses  # id 없는 pending 잡이 살아남았다
    assert "completed" not in statuses  # TTL 넘긴 terminal 잡은 정리됐다


def test_dedup_requires_same_kind(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    directions = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )
    post = workspace_jobs.create_job(
        "post", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )

    assert post["id"] != directions["id"]


def test_duplicate_pending_request_returns_same_job(tmp_path):
    """탭 두 개가 같은 요청을 보내도 잡은 하나만 만들어진다 — 중복 과금 방지의
    스토어 수준 방어선이다."""
    path = tmp_path / "workspace_jobs.json"
    first = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수"}, engine="Grok CLI", language="ko", path=path
    )

    second = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수"}, engine="Grok CLI", language="ko", path=path
    )
    assert second["id"] == first["id"]

    workspace_jobs.claim_job(first["id"], path=path)
    third = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수"}, engine="Grok CLI", language="ko", path=path
    )
    assert third["id"] == first["id"]

    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["jobs"]) == 1


def test_different_request_engine_or_language_is_not_deduplicated(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    base = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )

    other_request = workspace_jobs.create_job(
        "directions", {"keywords": "강아지"}, engine="Grok CLI", language="ko", path=path
    )
    other_engine = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Codex CLI", language="ko", path=path
    )
    other_language = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="en", path=path
    )

    assert len({base["id"], other_request["id"], other_engine["id"], other_language["id"]}) == 4


def test_terminal_job_does_not_block_resubmission(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    first = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko", path=path
    )
    workspace_jobs.fail_job(first["id"], "provider down", path=path)

    retry = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko", path=path
    )

    assert retry["id"] != first["id"]


def test_stale_pending_job_beyond_window_is_not_deduplicated(tmp_path):
    """워커가 죽어 오래 queued 로 남은 잡이 재제출을 영구히 막으면 안 된다."""
    path = tmp_path / "workspace_jobs.json"
    first = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )
    _rewrite_job(
        path, first["id"],
        updated_at=_stamp(timedelta(minutes=workspace_jobs.DEDUP_WINDOW_MINUTES + 1)),
    )

    second = workspace_jobs.create_job(
        "directions", {"keywords": "고양이"}, engine="Grok CLI", language="ko", path=path
    )

    assert second["id"] != first["id"]
    assert workspace_jobs.get_job(first["id"], path=path) is not None
