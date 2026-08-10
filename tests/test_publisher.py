"""XPublisher + 발행 워커 로직 테스트 (HTTP 목)."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

import publisher as publisher_mod
from content_queue import add_draft, approve_draft, empty_queue, load_queue, save_queue
from providers.base import ProviderError
from publisher import XPublisher, load_env

# scripts/ 는 패키지가 아니므로 파일 경로로 로드한다.
_spec = importlib.util.spec_from_file_location(
    "publish_worker", Path(__file__).parent.parent / "scripts" / "publish_worker.py"
)
publish_worker = importlib.util.module_from_spec(_spec)
sys.modules["publish_worker"] = publish_worker
_spec.loader.exec_module(publish_worker)


FAKE_ENV = {
    "X_API_KEY": "fake-consumer-key-12345",
    "X_API_KEY_SECRET": "fake-consumer-secret-12345",
    "X_ACCESS_TOKEN": "fake-access-token-12345",
    "X_ACCESS_TOKEN_SECRET": "fake-access-secret-12345",
}

WED_EVENING = datetime(2026, 7, 8, 19, 5)  # 수 19:05 — 19:00 슬롯 유예시간 내


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json


class TestLoadEnv:
    def test_parses_env_file(self, tmp_path, monkeypatch):
        for key in FAKE_ENV:
            monkeypatch.delenv(key, raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# comment\nX_API_KEY=abc\nX_API_KEY_SECRET=\"quoted\"\n", encoding="utf-8"
        )
        env = load_env(env_file)
        assert env["X_API_KEY"] == "abc"
        assert env["X_API_KEY_SECRET"] == "quoted"

    def test_missing_file_gives_empty(self, tmp_path, monkeypatch):
        for key in FAKE_ENV:
            monkeypatch.delenv(key, raising=False)
        assert load_env(tmp_path / "none.env") == {}


class TestXPublisher:
    def test_not_configured_raises(self):
        pub = XPublisher(env={})
        assert not pub.is_configured()
        with pytest.raises(ProviderError, match="not configured"):
            pub.post_text("hello")

    def test_post_text_success(self, monkeypatch):
        captured = {}

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["json"] = kwargs["json"]
            return _FakeResponse({"data": {"id": "1234567890", "text": "hello"}}, 201)

        monkeypatch.setattr(publisher_mod.requests, "post", fake_post)
        result = XPublisher(env=FAKE_ENV).post_text("hello")

        assert result["id"] == "1234567890"
        assert captured["url"].endswith("/2/tweets")
        assert captured["json"] == {"text": "hello"}

    def test_post_text_error_surfaces_detail_without_keys(self, monkeypatch):
        def fake_post(url, **kwargs):
            return _FakeResponse({"detail": "payment required"}, 402)

        monkeypatch.setattr(publisher_mod.requests, "post", fake_post)
        with pytest.raises(ProviderError) as err:
            XPublisher(env=FAKE_ENV).post_text("hello")
        message = str(err.value)
        assert "payment required" in message
        for secret in FAKE_ENV.values():
            assert secret not in message  # 키 값이 에러 메시지에 노출되지 않음

    def test_empty_text_raises(self):
        with pytest.raises(ProviderError, match="empty"):
            XPublisher(env=FAKE_ENV).post_text("   ")


class _FakePublisher:
    def __init__(self, fail=False):
        self.posted = []
        self.fail = fail

    def post_text(self, text):
        if self.fail:
            raise ProviderError("X API error HTTP 402: payment required")
        self.posted.append(text)
        return {"id": f"tw{len(self.posted)}", "text": text}


def _queue_with_approved(tmp_path, *, slot_iso: str):
    data = empty_queue()
    draft = add_draft(data, text="발행할 글", pillar="tip")
    draft["status"] = "approved"
    draft["slot"] = slot_iso
    path = tmp_path / "queue.json"
    save_queue(path, data)
    return path, draft["id"]


def _read_events(tmp_path):
    log_path = tmp_path / "log.jsonl"
    if not log_path.exists():
        return []
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestPublishWorker:
    def _silence_log(self, monkeypatch, tmp_path):
        monkeypatch.setattr(publish_worker, "LOG_PATH", tmp_path / "log.jsonl")

    def test_dry_run_does_not_publish(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        path, draft_id = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=False, queue_path=path)

        assert summary["posted"] == 1  # would-post 로 집계
        data = load_queue(path)
        assert data["drafts"][0]["status"] == "approved"  # 상태 변화 없음

    def test_live_publishes_due_draft(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        fake = _FakePublisher()
        monkeypatch.setattr(publish_worker, "XPublisher", lambda: fake)
        path, draft_id = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=True, queue_path=path)

        assert summary["posted"] == 1
        assert fake.posted == ["발행할 글"]
        data = load_queue(path)
        assert data["drafts"][0]["status"] == "published"
        assert data["drafts"][0]["tweet_id"] == "tw1"

    def test_future_slot_stays_pending(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        path, _ = _queue_with_approved(tmp_path, slot_iso="2026-07-09T08:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=False, queue_path=path)

        assert summary == {"posted": 0, "reassigned": 0, "pending": 1}

    def test_missed_slot_reassigned_not_posted(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        fake = _FakePublisher()
        monkeypatch.setattr(publish_worker, "XPublisher", lambda: fake)
        # 슬롯이 아침 08시였는데 지금은 19:05 — 유예(90분) 초과
        path, _ = _queue_with_approved(tmp_path, slot_iso="2026-07-08T08:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=True, queue_path=path)

        assert summary["reassigned"] == 1
        assert fake.posted == []
        data = load_queue(path)
        draft = data["drafts"][0]
        assert draft["status"] == "approved"
        assert draft["slot"] > "2026-07-08T19:05"  # 미래 슬롯으로 이동

    def test_publish_failure_keeps_draft_approved(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        monkeypatch.setattr(publish_worker, "XPublisher", lambda: _FakePublisher(fail=True))
        path, _ = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=True, queue_path=path)

        assert summary["posted"] == 0
        data = load_queue(path)
        assert data["drafts"][0]["status"] == "approved"  # 다음 실행에서 재시도 가능

    # -- 클레임(트랜잭션1) / 락 밖 발행 / 기록(트랜잭션2) 재구성 ---------------

    def test_live_success_marks_published(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        fake = _FakePublisher()
        path, draft_id = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(
            now=WED_EVENING, live=True, queue_path=path, publisher=fake
        )

        assert summary["posted"] == 1
        assert fake.posted == ["발행할 글"]  # 정확히 1회 호출
        data = load_queue(path)
        draft = data["drafts"][0]
        assert draft["status"] == "published"
        assert draft["tweet_id"] == "tw1"
        assert draft["published_at"]

    def test_live_failure_reverts_to_approved(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        fake = _FakePublisher(fail=True)
        path, draft_id = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(
            now=WED_EVENING, live=True, queue_path=path, publisher=fake
        )

        assert summary["posted"] == 0
        data = load_queue(path)
        draft = data["drafts"][0]
        assert draft["status"] == "approved"  # 슬롯 유지, 다음 실행에서 재시도
        assert draft["slot"] == "2026-07-08T19:00:00"
        events = _read_events(tmp_path)
        assert any(
            e["event"] == "publish_failed" and e["draft_id"] == draft_id
            for e in events
        )

    def test_stale_publishing_marked_error(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        data = empty_queue()
        draft = add_draft(data, text="크래시 잔재", pillar="tip")
        draft["status"] = "publishing"  # 이전 실행이 크래시로 남긴 상태
        draft["slot"] = "2026-07-08T19:00:00"
        path = tmp_path / "queue.json"
        save_queue(path, data)
        fake = _FakePublisher()

        publish_worker.run(now=WED_EVENING, live=True, queue_path=path, publisher=fake)

        assert fake.posted == []  # 재발행하지 않음 — 이중 게시 방지가 우선
        result = load_queue(path)
        assert result["drafts"][0]["status"] == "error"
        events = _read_events(tmp_path)
        assert any(
            e["event"] == "stale_publishing_needs_review"
            and e["draft_id"] == draft["id"]
            for e in events
        )

    def test_dry_run_unchanged(self, tmp_path, monkeypatch):
        self._silence_log(monkeypatch, tmp_path)
        path, draft_id = _queue_with_approved(tmp_path, slot_iso="2026-07-08T19:00:00")

        summary = publish_worker.run(now=WED_EVENING, live=False, queue_path=path)

        assert summary["posted"] == 1  # would-post 로 집계
        data = load_queue(path)
        draft = data["drafts"][0]
        assert draft["status"] == "approved"  # 상태 변화 없음(재배정 제외)
        assert "tweet_id" not in draft
        events = _read_events(tmp_path)
        assert any(
            e["event"] == "dry_run_would_post" and e["draft_id"] == draft_id
            for e in events
        )

    def test_concurrent_run_skips_publishing_draft(self, tmp_path, monkeypatch):
        """트랜잭션1~2 사이(디스크에 status=publishing 이 이미 반영된 시점)에
        다른 워커 실행이 큐를 열어도, 이미 클레임된 초안을 다시 발행하지 않는다."""
        self._silence_log(monkeypatch, tmp_path)
        data = empty_queue()
        draft = add_draft(data, text="이미 클레임됨", pillar="tip")
        draft["status"] = "publishing"  # 다른 실행이 트랜잭션1에서 이미 찜한 상태
        draft["slot"] = "2026-07-08T19:00:00"
        path = tmp_path / "queue.json"
        save_queue(path, data)
        fake = _FakePublisher()

        publish_worker.run(now=WED_EVENING, live=True, queue_path=path, publisher=fake)

        assert fake.posted == []  # 이중 발행 없음

    def test_non_provider_error_does_not_orphan_other_claims(self, tmp_path, monkeypatch):
        """post_text 가 ProviderError 가 아닌 평범한 예외(예: JSON 파싱 실패)를
        던져도 그 클레임 하나만 실패 처리되고, 나머지 클레임은 정상 발행돼야
        한다 — 좁은 except 는 루프 전체를 끊어 이미 성공한 발행까지
        "publishing" 에 방치할 수 있다(다음 실행에서 전부 error 로 처리됨)."""
        self._silence_log(monkeypatch, tmp_path)
        data = empty_queue()
        draft_a = add_draft(data, text="글 A - 실패", pillar="tip")
        draft_a["status"] = "approved"
        draft_a["slot"] = "2026-07-08T19:00:00"
        draft_b = add_draft(data, text="글 B - 성공", pillar="tip")
        draft_b["status"] = "approved"
        draft_b["slot"] = "2026-07-08T19:00:00"
        path = tmp_path / "queue.json"
        save_queue(path, data)

        class _MixedFakePublisher:
            def __init__(self):
                self.posted = []

            def post_text(self, text):
                if text == draft_a["text"]:
                    raise RuntimeError("boom — ProviderError 가 아닌 평범한 예외")
                self.posted.append(text)
                return {"id": f"tw{len(self.posted)}"}

        fake = _MixedFakePublisher()

        summary = publish_worker.run(
            now=WED_EVENING, live=True, queue_path=path, publisher=fake
        )  # 예외를 raise 하지 않고 끝까지 실행돼야 한다

        assert summary["posted"] == 1
        result = load_queue(path)
        by_id = {d["id"]: d for d in result["drafts"]}
        assert by_id[draft_a["id"]]["status"] == "approved"  # 되돌림 — 재시도 가능
        assert by_id[draft_b["id"]]["status"] == "published"
        assert by_id[draft_b["id"]]["tweet_id"] == "tw1"
        events = _read_events(tmp_path)
        assert any(
            e["event"] == "publish_failed" and e["draft_id"] == draft_a["id"]
            for e in events
        )
        assert any(
            e["event"] == "published" and e["draft_id"] == draft_b["id"]
            for e in events
        )
