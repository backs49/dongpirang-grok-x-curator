"""야간 초안 생성 배치 (4b) 로직 테스트."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path

from content_queue import add_draft, add_material, empty_queue, load_queue, save_queue

_spec = importlib.util.spec_from_file_location(
    "generate_drafts", Path(__file__).parent.parent / "scripts" / "generate_drafts.py"
)
generate_drafts = importlib.util.module_from_spec(_spec)
sys.modules["generate_drafts"] = generate_drafts
_spec.loader.exec_module(generate_drafts)


class _FakeGrok:
    def __init__(self):
        self.material_calls = []
        self.idea_calls = []

    def draft_from_material(self, text):
        self.material_calls.append(text)
        return {
            "post": f"[초안] {text}",
            "pillar": "build_in_public",
            "image_prompt": "desk, no text",
        }

    def generate_ideas(self, keywords, length=0):
        self.idea_calls.append(keywords)
        return {
            "ideas": [
                {"title": "팁", "content": "팁 포스트 본문", "image_prompt": "tips, no text"},
            ]
        }


class _FakeNotify:
    """텔레그램 발송기 대역. 실제 발송을 막고 호출 내용을 기록한다."""

    def __init__(self, ok: bool = True):
        self.ok = ok
        self.messages: list[str] = []

    def __call__(self, text: str) -> bool:
        self.messages.append(text)
        return self.ok


def _run(tmp_path, data, grok=None, notify=None, now=None):
    path = tmp_path / "queue.json"
    save_queue(path, data)
    grok = grok or _FakeGrok()
    # notify 를 항상 주입해 테스트가 실제 텔레그램을 건드리지 않게 한다.
    notify = notify if notify is not None else _FakeNotify()
    summary = generate_drafts.run(grok=grok, queue_path=path, notify=notify, now=now)
    return summary, load_queue(path), grok


class TestGenerateDrafts:
    def test_materials_become_drafts(self, tmp_path):
        data = empty_queue()
        add_material(data, "소재 A")
        add_material(data, "소재 B")

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 2
        assert len(saved["drafts"]) == 2
        assert all(d["status"] == "draft" for d in saved["drafts"])
        # 소재는 사용 처리됨
        assert all(m["used"] for m in saved["materials"])

    def test_materials_capped_per_night(self, tmp_path):
        data = empty_queue()
        for i in range(5):
            add_material(data, f"소재 {i}")

        summary, saved, _ = _run(tmp_path, data)

        assert summary["from_materials"] == generate_drafts.MAX_MATERIALS_PER_NIGHT
        unused = [m for m in saved["materials"] if not m["used"]]
        assert len(unused) == 5 - generate_drafts.MAX_MATERIALS_PER_NIGHT

    def test_tip_fallback_when_no_materials_and_low_stock(self, tmp_path):
        data = empty_queue()

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 0
        assert summary["tip_drafts"] == 1
        assert saved["drafts"][0]["pillar"] == "tip"
        assert grok.idea_calls  # generate_ideas 사용

    def test_skips_entirely_when_stock_sufficient(self, tmp_path):
        data = empty_queue()
        for i in range(generate_drafts.STOCK_TARGET):
            add_draft(data, text=f"재고 {i}", pillar="tip")
        add_material(data, "소재")  # 소재가 있어도 재고 충분하면 스킵

        summary, saved, grok = _run(tmp_path, data)

        assert summary == {"from_materials": 0, "tip_drafts": 0, "skipped": True}
        assert not grok.material_calls
        # 소재는 소모되지 않고 남는다
        assert not saved["materials"][0]["used"]

    def test_error_status_counts_toward_stock(self, tmp_path):
        # error 상태(발행 결과 불명 등)를 재고에서 빼면 해소되지 않은 에러가
        # 쌓인 채로 새 초안이 계속 생성돼 문제를 가린다.
        data = empty_queue()
        draft = add_draft(data, text="에러 상태", pillar="tip")
        draft["status"] = "error"
        for i in range(generate_drafts.STOCK_TARGET - 1):
            add_draft(data, text=f"재고 {i}", pillar="tip")

        summary, saved, grok = _run(tmp_path, data)

        assert summary == {"from_materials": 0, "tip_drafts": 0, "skipped": True}
        assert not grok.material_calls

    def test_generation_error_leaves_material_unused(self, tmp_path):
        class _ErrorGrok(_FakeGrok):
            def draft_from_material(self, text):
                return {"error": "engine down"}

        data = empty_queue()
        add_material(data, "소재 A")

        summary, saved, _ = _run(tmp_path, data, grok=_ErrorGrok())

        assert summary["from_materials"] == 0
        assert saved["drafts"] == []
        assert not saved["materials"][0]["used"]

    def test_custom_tip_keywords_from_settings(self, tmp_path):
        data = empty_queue()
        data["settings"] = {"tip_keywords": "고양이 만화, 통영 여행"}

        _, _, grok = _run(tmp_path, data)

        assert grok.idea_calls == ["고양이 만화, 통영 여행"]


NOW = datetime(2026, 8, 10, 23, 0, 0)


def _waiting_draft(data, *, days_ago, status="draft", now=NOW):
    """created_at 을 과거로 돌린 초안을 하나 넣는다."""
    draft = add_draft(data, text=f"{days_ago}일 전 초안", pillar="tip")
    draft["created_at"] = (now - timedelta(days=days_ago)).isoformat(timespec="seconds")
    draft["status"] = status
    return draft


class TestStaleDraftReminder:
    """승인 대기 초안이 방치되면 관리자에게 리마인드한다.

    2026-07-08 이후 33일간 발행이 0건이었던 원인은 코드 버그가 아니라
    승인 게이트였다. 초안 4건이 draft 상태로 쌓여 재고 목표에 도달하자
    생성기는 매일 밤 '재고 충분'만 찍고 멈췄고, 발행 워커는 approved 가
    없어 99회를 헛돌았다. 아무도 알려주지 않아서 한 달을 몰랐다.
    """

    def test_reminds_when_drafts_wait_past_threshold(self, tmp_path):
        data = empty_queue()
        for _ in range(generate_drafts.STOCK_TARGET):
            _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 1)
        notify = _FakeNotify()

        summary, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        # 재고가 충분해 생성은 건너뛰지만, 리마인드는 나가야 한다.
        assert summary["skipped"] is True
        assert len(notify.messages) == 1
        message = notify.messages[0]
        assert str(generate_drafts.STOCK_TARGET) in message
        # 발송 시각이 큐에 기록돼야 다음 밤에 중복 발송하지 않는다.
        assert saved["reminders"]["stale_drafts_at"]

    def test_silent_when_drafts_are_fresh(self, tmp_path):
        data = empty_queue()
        for _ in range(generate_drafts.STOCK_TARGET):
            _waiting_draft(data, days_ago=0)
        notify = _FakeNotify()

        _, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert notify.messages == []
        assert "reminders" not in saved

    def test_silent_when_nothing_is_waiting(self, tmp_path):
        # 승인 대기가 0건인 상태(초안을 전부 삭제한 직후)에서는 알릴 게 없다.
        data = empty_queue()
        notify = _FakeNotify()

        _, _, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert notify.messages == []

    def test_approved_drafts_do_not_trigger_reminder(self, tmp_path):
        # approved 는 워커가 슬롯에 자동 발행한다 — 사람이 막고 있는 게 아니다.
        data = empty_queue()
        for _ in range(generate_drafts.STOCK_TARGET):
            _waiting_draft(
                data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 5, status="approved"
            )
        notify = _FakeNotify()

        _, _, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert notify.messages == []

    def test_throttled_inside_reminder_interval(self, tmp_path):
        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 10)
        recent = NOW - timedelta(days=generate_drafts.REMINDER_INTERVAL_DAYS - 1)
        data["reminders"] = {"stale_drafts_at": recent.isoformat(timespec="seconds")}
        notify = _FakeNotify()

        _, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert notify.messages == []
        # 기존 발송 시각은 그대로 남는다.
        assert saved["reminders"]["stale_drafts_at"] == recent.isoformat(timespec="seconds")

    def test_reminds_again_after_interval(self, tmp_path):
        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 10)
        old = NOW - timedelta(days=generate_drafts.REMINDER_INTERVAL_DAYS)
        data["reminders"] = {"stale_drafts_at": old.isoformat(timespec="seconds")}
        notify = _FakeNotify()

        _, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert len(notify.messages) == 1
        assert saved["reminders"]["stale_drafts_at"] == NOW.isoformat(timespec="seconds")

    def test_failed_send_is_not_stamped(self, tmp_path):
        # 발송이 실패했는데 시각을 찍으면 다음 밤까지 조용해진다 — 그게 이 버그였다.
        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 1)
        notify = _FakeNotify(ok=False)

        _, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert len(notify.messages) == 1
        assert not (saved.get("reminders") or {}).get("stale_drafts_at")

    def test_reminder_survives_the_generating_path(self, tmp_path):
        # 재고가 부족해 생성이 함께 도는 밤에도 리마인드는 나가고 보존된다.
        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 1)
        add_material(data, "새 소재")
        notify = _FakeNotify()

        summary, saved, _ = _run(tmp_path, data, notify=notify, now=NOW)

        assert summary["skipped"] is False
        assert summary["from_materials"] == 1
        assert len(notify.messages) == 1
        assert saved["reminders"]["stale_drafts_at"] == NOW.isoformat(timespec="seconds")
