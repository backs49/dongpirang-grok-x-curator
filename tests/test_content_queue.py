"""발행 큐 저장소 + 발행 슬롯 계산 테스트."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from content_queue import (
    add_draft,
    add_material,
    approve_draft,
    empty_queue,
    load_queue,
    next_slots,
    remove_draft,
    remove_material,
    save_queue,
    unused_materials,
    update_draft_text,
)

# 2026-07-08 은 수요일
WED_NOON = datetime(2026, 7, 8, 12, 0)


class TestNextSlots:
    def test_weekday_evening_and_next_morning(self):
        slots = next_slots(WED_NOON, 3)
        assert slots[0] == datetime(2026, 7, 8, 19, 0)   # 수 저녁
        assert slots[1] == datetime(2026, 7, 9, 8, 0)    # 목 아침
        assert slots[2] == datetime(2026, 7, 9, 19, 0)   # 목 저녁

    def test_saturday_single_slot_and_sunday_skipped(self):
        friday_evening = datetime(2026, 7, 10, 20, 0)  # 금 20시 (금 슬롯 종료 후)
        slots = next_slots(friday_evening, 3)
        assert slots[0] == datetime(2026, 7, 11, 10, 0)  # 토 오전
        assert slots[1] == datetime(2026, 7, 13, 8, 0)   # 일요일 건너뛰고 월 아침
        assert slots[2] == datetime(2026, 7, 13, 19, 0)

    def test_same_day_morning_included(self):
        early = datetime(2026, 7, 8, 6, 0)
        slots = next_slots(early, 2)
        assert slots[0] == datetime(2026, 7, 8, 8, 0)
        assert slots[1] == datetime(2026, 7, 8, 19, 0)


class TestQueueStorage:
    def test_load_missing_file_returns_empty(self, tmp_path):
        data = load_queue(tmp_path / "queue.json")
        assert data == empty_queue()

    def test_save_and_load_roundtrip(self, tmp_path):
        path = tmp_path / "queue.json"
        data = empty_queue()
        add_material(data, "오늘 버그 3시간 잡았는데 원인은 오타")
        save_queue(path, data)

        loaded = load_queue(path)
        assert len(loaded["materials"]) == 1
        assert loaded["materials"][0]["text"].startswith("오늘 버그")

    def test_load_corrupt_file_returns_empty(self, tmp_path):
        path = tmp_path / "queue.json"
        path.write_text("{broken json", encoding="utf-8")
        assert load_queue(path) == empty_queue()

    def test_save_uses_unique_tmp_and_leaves_no_stray_files(self, tmp_path):
        """동시 저장자가 고정된 tmp 이름을 공유하지 않고, 저장 후에는
        임시 파일이 디렉터리에 남지 않아야 한다."""
        path = tmp_path / "queue.json"

        data1 = empty_queue()
        add_material(data1, "첫 번째 저장")
        save_queue(path, data1)

        data2 = load_queue(path)
        add_material(data2, "두 번째 저장")
        save_queue(path, data2)

        loaded = load_queue(path)
        assert len(loaded["materials"]) == 2

        stray_tmp_files = [p for p in tmp_path.glob("*") if p != path]
        assert stray_tmp_files == []


class TestMaterials:
    def test_add_and_remove(self):
        data = empty_queue()
        material = add_material(data, "소재 하나")
        assert unused_materials(data) == [material]

        remove_material(data, material["id"])
        assert unused_materials(data) == []

    def test_blank_material_ignored(self):
        data = empty_queue()
        assert add_material(data, "   ") is None
        assert data["materials"] == []


class TestDrafts:
    def test_add_draft_defaults(self):
        data = empty_queue()
        draft = add_draft(data, text="포스트 본문", pillar="tip")
        assert draft["status"] == "draft"
        assert draft["slot"] is None
        assert data["drafts"] == [draft]

    def test_add_draft_marks_material_used(self):
        data = empty_queue()
        material = add_material(data, "소재")
        add_draft(data, text="글", pillar="build_in_public", material_id=material["id"])
        assert unused_materials(data) == []

    def test_approve_assigns_earliest_free_slot(self):
        data = empty_queue()
        d1 = add_draft(data, text="글1", pillar="tip")
        d2 = add_draft(data, text="글2", pillar="tip")

        approve_draft(data, d1["id"], now=WED_NOON)
        approve_draft(data, d2["id"], now=WED_NOON)

        assert d1["status"] == "approved"
        assert d1["slot"] == "2026-07-08T19:00:00"
        # 두 번째 승인은 다음 빈 슬롯
        assert d2["slot"] == "2026-07-09T08:00:00"

    def test_update_text_and_remove(self):
        data = empty_queue()
        draft = add_draft(data, text="원래 글", pillar="tip")
        update_draft_text(data, draft["id"], "고친 글")
        assert data["drafts"][0]["text"] == "고친 글"

        remove_draft(data, draft["id"])
        assert data["drafts"] == []


class _FakeProvider:
    supports_curator = False

    def __init__(self):
        self.last_call = None

    def generate_json(self, system_prompt, user_prompt, **kwargs):
        self.last_call = (system_prompt, user_prompt)
        return {"post": "완성 포스트", "pillar": "tip", "image_prompt": "desk, no text"}


def test_draft_from_material_sends_material():
    from grok_client import GrokClient

    provider = _FakeProvider()
    grok = GrokClient(provider=provider)
    result = grok.draft_from_material("버그 3시간, 원인은 오타")

    assert result["post"] == "완성 포스트"
    system_prompt, user_prompt = provider.last_call
    assert "진정성" in system_prompt
    assert "버그 3시간" in user_prompt
    # 자연스러운 글쓰기 지침(AI 냄새 제거)이 포함되어야 한다
    assert "AI 냄새 제거 규칙" in system_prompt
    assert "17년차" in system_prompt
    assert "이모지는 기본적으로 쓰지 않는다" in system_prompt


class TestQueueLock:
    def test_transaction_saves_on_success(self, tmp_path):
        from content_queue import add_draft, load_queue, queue_transaction

        qp = tmp_path / "queue.json"
        with queue_transaction(qp) as data:
            add_draft(data, text="본문", pillar="tip")
        assert len(load_queue(qp)["drafts"]) == 1

    def test_transaction_skips_save_on_exception(self, tmp_path):
        from content_queue import add_draft, load_queue, queue_transaction

        qp = tmp_path / "queue.json"
        with pytest.raises(RuntimeError):
            with queue_transaction(qp) as data:
                add_draft(data, text="본문", pillar="tip")
                raise RuntimeError("boom")
        assert load_queue(qp)["drafts"] == []

    def test_lock_blocks_second_holder(self, tmp_path):
        import fcntl

        from content_queue import queue_lock

        qp = tmp_path / "queue.json"
        with queue_lock(qp):
            lock_file = qp.with_suffix(".lock")
            with open(lock_file, "w") as second:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_lock_timeout_raises(self, tmp_path, monkeypatch):
        from content_queue import queue_lock

        qp = tmp_path / "queue.json"
        with queue_lock(qp):
            with pytest.raises(TimeoutError):
                with queue_lock(qp, timeout=0.3):
                    pass


def test_pq_i18n_keys_cover_all_languages():
    from i18n import _T, LANGUAGES

    keys = [k for k in _T if k.startswith("pq_")] + ["tab_publish_queue"]
    assert len(keys) > 15
    for key in keys:
        assert set(_T[key]) >= set(LANGUAGES), f"missing translations for {key}"
