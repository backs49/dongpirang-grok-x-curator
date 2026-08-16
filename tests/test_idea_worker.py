from __future__ import annotations

from types import SimpleNamespace

import idea_jobs
from scripts import idea_worker


class FakeGrok:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.provider = SimpleNamespace(name="Fake CLI")

    def generate_ideas(self, keywords, length, mode):
        self.calls.append((keywords, length, mode))
        return self.result


def test_worker_claims_job_saves_success_and_appends_history(monkeypatch, tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 280, "auto", "Grok CLI", path=path)
    grok = FakeGrok({"ideas": [{"content": "완성된 포스트"}]})
    history = []

    monkeypatch.setattr(
        idea_worker,
        "build_provider",
        lambda engine: (grok, SimpleNamespace(message="ready")),
    )
    monkeypatch.setattr(idea_worker, "append_history", lambda *args, **kwargs: history.append((args, kwargs)))

    assert idea_worker.run(job["id"], jobs_path=path) == "completed"

    saved = idea_jobs.get_job(job["id"], path=path)
    assert saved["status"] == "completed"
    assert saved["result"] == {"ideas": [{"content": "완성된 포스트"}]}
    assert grok.calls == [("AI", 280, "auto")]
    assert len(history) == 1


def test_worker_saves_provider_error_without_writing_history(monkeypatch, tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "tip", "Claude CLI", path=path)
    grok = FakeGrok({"error": "OAuth session expired"})
    history = []

    monkeypatch.setattr(
        idea_worker,
        "build_provider",
        lambda engine: (grok, SimpleNamespace(message="ready")),
    )
    monkeypatch.setattr(idea_worker, "append_history", lambda *args, **kwargs: history.append((args, kwargs)))

    assert idea_worker.run(job["id"], jobs_path=path) == "failed"

    saved = idea_jobs.get_job(job["id"], path=path)
    assert saved["status"] == "failed"
    assert saved["error"] == "OAuth session expired"
    assert history == []


def test_worker_saves_unavailable_provider_message(monkeypatch, tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "auto", "Codex CLI", path=path)

    monkeypatch.setattr(
        idea_worker,
        "build_provider",
        lambda engine: (None, SimpleNamespace(message="node executable not found")),
    )

    assert idea_worker.run(job["id"], jobs_path=path) == "failed"
    assert idea_jobs.get_job(job["id"], path=path)["error"] == "node executable not found"


def test_worker_does_not_run_job_claimed_by_another_worker(monkeypatch, tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", path=path)
    idea_jobs.claim_job(job["id"], path=path)
    build_calls = []

    monkeypatch.setattr(idea_worker, "build_provider", lambda engine: build_calls.append(engine))

    assert idea_worker.run(job["id"], jobs_path=path) == "not_claimed"
    assert build_calls == []
