from __future__ import annotations

from types import SimpleNamespace

import idea_jobs
from scripts import idea_worker


class FakeGrok:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.provider = SimpleNamespace(name="Fake CLI")

    def generate_ideas(self, keywords, length, mode, language="ko"):
        self.calls.append((keywords, length, mode))
        self.language = language
        return self.result


class GroundedFake:
    def __init__(self, result):
        self.result = result
        self.calls = []
        self.provider = SimpleNamespace(name="Fake CLI")

    def generate_grounded_tips(self, keywords, *, category, references, length, mode, language="ko"):
        self.calls.append((keywords, category, references, length, mode))
        self.language = language
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


def test_grounded_worker_uses_grok_cli_and_persists_sources(monkeypatch, tmp_path):
    path = tmp_path / "jobs.json"
    job = idea_jobs.create_job(
        "수면",
        280,
        "hankang",
        "Claude CLI",
        content_type="grounded_tip",
        tip_category="health",
        references="WHO link",
        path=path,
    )
    calls, history = [], []
    fake = GroundedFake({"ideas": [{
        "content": "본문",
        "sources": [{"url": "https://who.int/a"}, {"url": "https://cdc.gov/b"}],
    }]})
    monkeypatch.setattr(
        idea_worker,
        "build_provider",
        lambda engine: (calls.append(engine) or fake, SimpleNamespace(message="ready")),
    )
    monkeypatch.setattr(idea_worker, "append_history", lambda *args, **kwargs: history.append((args, kwargs)))

    assert idea_worker.run(job["id"], jobs_path=path) == "completed"

    assert calls == ["Grok CLI"]
    assert fake.calls == [("수면", "health", "WHO link", 280, "hankang")]
    assert idea_jobs.get_job(job["id"], path=path)["result"] == fake.result
    assert history[0][1]["content_type"] == "grounded_tip"
    assert history[0][1]["tip_category"] == "health"
    assert history[0][1]["references"] == "WHO link"


def test_worker_passes_job_language_to_generation(monkeypatch, tmp_path):
    """워커는 스트림릿 세션 밖이라 UI 언어를 작업에서 읽어 넘겨야 한다."""
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", language="ja", path=path)
    grok = FakeGrok({"ideas": [{"content": "投稿"}]})
    monkeypatch.setattr(idea_worker, "build_provider", lambda engine: (grok, SimpleNamespace(message="ready")))
    monkeypatch.setattr(idea_worker, "append_history", lambda *a, **k: None)

    assert idea_worker.run(job["id"], jobs_path=path) == "completed"
    assert grok.language == "ja"


def test_unknown_or_legacy_job_language_falls_back_to_korean(tmp_path):
    path = tmp_path / "idea_jobs.json"
    job = idea_jobs.create_job("AI", 0, "auto", "Grok CLI", language="xx", path=path)
    assert job["language"] == "ko"
