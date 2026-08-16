from __future__ import annotations

from types import SimpleNamespace

import workspace_jobs
from scripts import workspace_worker


class Ready:
    message = "ready"


class FakeGrok:
    """브리핑 Step 1 예시 그대로. optimize_post 만 amendment 2(언어 전달)를
    깨지 않도록 language 키워드를 받아들이게 넓혔다 — 호출 검증은 여전히
    text 값만 본다."""

    def __init__(self, result):
        self.result = result
        self.optimize_calls = []

    def optimize_post(self, text, language=None):
        self.optimize_calls.append(text)
        return self.result


def test_worker_dispatches_only_the_requested_kind(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Codex CLI", language="ko", path=path
    )
    fake = FakeGrok({"optimized_post": "고친 글"})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.optimize_calls == ["원문"]


class DispatchFake:
    """분기별 호출 인자를 캡처하는 다목적 페이크. Task 2 의 GrokClient
    시그니처(키워드 전용 language 등)를 그대로 따른다."""

    def __init__(self, *, directions=None, post=None, optimize=None):
        self.directions_result = directions
        self.post_result = post
        self.optimize_result = optimize
        self.calls: dict = {}

    def generate_directions(self, keywords, *, mode, language):
        self.calls["directions"] = (keywords, mode, language)
        return self.directions_result

    def write_post(self, keywords, direction, *, length, mode, language):
        self.calls["post"] = (keywords, direction, length, mode, language)
        return self.post_result

    def write_grounded_post(
        self, keywords, direction, *, category, references, length, mode, language
    ):
        self.calls["grounded_post"] = (
            keywords, direction, category, references, length, mode, language,
        )
        return self.post_result

    def optimize_post(self, text, language=None):
        self.calls["optimize"] = (text, language)
        return self.optimize_result


def test_worker_runs_directions_job(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수", "mode": "builder_note"},
        engine="Grok CLI", language="ko", path=path,
    )
    fake = DispatchFake(directions={"directions": [{"title": "A"}]})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.calls["directions"] == ("배포 실수", "builder_note", "ko")
    assert workspace_jobs.get_job(job["id"], path=path)["result"] == {
        "directions": [{"title": "A"}]
    }


def test_worker_runs_normal_selected_post_job(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    direction = {"title": "A", "hook": "h", "angle": "a", "core_message": "m"}
    job = workspace_jobs.create_job(
        "post",
        {"keywords": "배포 실수", "direction": direction, "length": 280, "mode": "builder_note"},
        engine="Claude CLI", language="ko", path=path,
    )
    fake = DispatchFake(post={"post": {"content": "완성 글"}})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.calls["post"] == ("배포 실수", direction, 280, "builder_note", "ko")
    assert "grounded_post" not in fake.calls
    assert workspace_jobs.get_job(job["id"], path=path)["result"] == {
        "post": {"content": "완성 글"}
    }


def test_worker_runs_grounded_selected_post_job(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    direction = {"title": "A", "hook": "h", "angle": "a", "core_message": "m"}
    job = workspace_jobs.create_job(
        "post",
        {
            "content_type": "grounded_tip",
            "keywords": "수면 습관",
            "direction": direction,
            "category": "health",
            "references": "WHO link",
            "length": 280,
            "mode": "builder_note",
        },
        engine="Grok CLI", language="ko", path=path,
    )
    fake = DispatchFake(post={"post": {"content": "본문", "sources": []}})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.calls["grounded_post"] == (
        "수면 습관", direction, "health", "WHO link", 280, "builder_note", "ko",
    )
    assert "post" not in fake.calls


def test_worker_forwards_language_to_optimize(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="en", path=path
    )
    fake = DispatchFake(optimize={"optimized_post": "ok"})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.calls["optimize"] == ("원문", "en")


def test_worker_saves_unavailable_provider_message(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Codex CLI", language="ko", path=path
    )
    monkeypatch.setattr(
        workspace_worker, "build_provider",
        lambda engine: (None, SimpleNamespace(message="node executable not found")),
    )

    assert workspace_worker.run(job["id"], jobs_path=path) == "failed"
    assert workspace_jobs.get_job(job["id"], path=path)["error"] == "node executable not found"


def test_worker_saves_provider_error_dict(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "directions", {"keywords": "AI", "mode": "auto"}, engine="Grok CLI", language="ko", path=path
    )
    fake = DispatchFake(directions={"error": "invalid_directions"})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))

    assert workspace_worker.run(job["id"], jobs_path=path) == "failed"
    assert workspace_jobs.get_job(job["id"], path=path)["error"] == "invalid_directions"


def test_worker_does_not_run_job_claimed_by_another_worker(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Grok CLI", language="ko", path=path
    )
    workspace_jobs.claim_job(job["id"], path=path)
    build_calls = []
    monkeypatch.setattr(workspace_worker, "build_provider", lambda engine: build_calls.append(engine))

    assert workspace_worker.run(job["id"], jobs_path=path) == "not_claimed"
    assert build_calls == []


def test_worker_fails_cleanly_for_xai_api_engine_without_calling_a_cli(tmp_path):
    """xAI API 키는 브라우저 쿠키에만 있어 detached 워커가 접근할 수 없다.
    provider_selection.build_provider 는 api_key 없이 호출되면 이미 안전하게
    실패하므로, 워커는 별도 분기 없이 그 미가용 경로를 그대로 탄다."""
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="xAI API", language="ko", path=path
    )

    assert workspace_worker.run(job["id"], jobs_path=path) == "failed"
    saved = workspace_jobs.get_job(job["id"], path=path)
    assert saved["status"] == "failed"
    assert "key" in saved["error"].lower()


def test_worker_completes_demo_directions_without_building_a_provider(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "directions", {"keywords": "AI", "mode": "auto"}, engine="Demo", language="ko", path=path
    )
    build_calls = []
    monkeypatch.setattr(workspace_worker, "build_provider", lambda engine: build_calls.append(engine))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert build_calls == []
    result = workspace_jobs.get_job(job["id"], path=path)["result"]
    assert len(result["directions"]) == 3
    for card in result["directions"]:
        assert card["title"] and card["hook"] and card["angle"] and card["core_message"]


def test_worker_completes_demo_post_without_building_a_provider(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "post",
        {"keywords": "AI", "direction": {"title": "A"}, "length": 280, "mode": "auto"},
        engine="Demo", language="ko", path=path,
    )
    build_calls = []
    monkeypatch.setattr(workspace_worker, "build_provider", lambda engine: build_calls.append(engine))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert build_calls == []
    result = workspace_jobs.get_job(job["id"], path=path)["result"]
    assert result["post"]["content"]


def test_worker_completes_demo_optimize_without_building_a_provider(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "optimize", {"text": "원문"}, engine="Demo", language="ko", path=path
    )
    build_calls = []
    monkeypatch.setattr(workspace_worker, "build_provider", lambda engine: build_calls.append(engine))

    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert build_calls == []
    result = workspace_jobs.get_job(job["id"], path=path)["result"]
    assert "optimized_post" in result
