"""야간 초안 생성 배치 (4b) 로직 테스트."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from content_queue import add_draft, add_material, empty_queue, load_queue, save_queue

_spec = importlib.util.spec_from_file_location(
    "generate_drafts", Path(__file__).parent.parent / "scripts" / "generate_drafts.py"
)
generate_drafts = importlib.util.module_from_spec(_spec)
sys.modules["generate_drafts"] = generate_drafts
_spec.loader.exec_module(generate_drafts)

_REAL_LOG_PATH = generate_drafts.LOG_PATH


@pytest.fixture(autouse=True)
def _isolated_log(tmp_path, monkeypatch):
    """log_event 가 실제 content_queue/draft_log.jsonl 에 쓰지 않게 한다.

    LOG_PATH 는 임포트 시점의 QUEUE_PATH 에서 만들어져서 run(queue_path=...) 로
    큐만 임시 경로로 돌려도 로그는 운영 파일에 붙었다. 그 로그가 운영 상태를
    보는 정본인데 2026-11-20 기준 2,609줄 중 약 2,300줄이 테스트 흔적이었다.
    """
    monkeypatch.setattr(generate_drafts, "LOG_PATH", tmp_path / "draft_log.jsonl")


class _FakeGrok:
    def __init__(self):
        self.material_calls = []
        self.idea_calls = []
        self.reply_calls = []

    def draft_from_material(self, text):
        self.material_calls.append(text)
        return {
            "post": f"[초안] {text}",
            "pillar": "build_in_public",
            "image_prompt": "desk, no text",
        }

    def draft_from_reply(self, text, parent=""):
        self.reply_calls.append((text, parent))
        if "스킵" in text:
            return {"skip": True, "reason": "원글 없이 뜻이 안 통함"}
        return {"post": f"[답글글] {text}", "pillar": "curation", "image_prompt": ""}

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


def _no_seeds(after_id, now):
    return [], None


def _run(tmp_path, data, grok=None, notify=None, now=None, seed_source=None):
    path = tmp_path / "queue.json"
    save_queue(path, data)
    grok = grok or _FakeGrok()
    # notify 를 항상 주입해 테스트가 실제 텔레그램을 건드리지 않게 한다.
    notify = notify if notify is not None else _FakeNotify()
    # 씨앗 소스도 항상 주입해 X API 를 건드리지 않게 한다.
    summary = generate_drafts.run(
        grok=grok, queue_path=path, notify=notify, now=now,
        seed_source=seed_source or _no_seeds,
    )
    return summary, load_queue(path), grok


class TestLogIsolation:
    def test_events_go_to_the_temp_log_not_the_live_one(self, tmp_path):
        _run(tmp_path, empty_queue())

        assert generate_drafts.LOG_PATH != _REAL_LOG_PATH
        assert generate_drafts.LOG_PATH.parent == tmp_path
        assert "run_summary" in generate_drafts.LOG_PATH.read_text(encoding="utf-8")


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

    def test_full_stock_blocks_materials_and_tips(self, tmp_path):
        data = empty_queue()
        for i in range(generate_drafts.STOCK_TARGET):
            add_draft(data, text=f"재고 {i}", pillar="tip")
        add_material(data, "소재")  # 소재가 있어도 재고 충분하면 변환하지 않는다

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 0 and summary["tip_drafts"] == 0
        assert not grok.material_calls and not grok.idea_calls
        assert len(saved["drafts"]) == generate_drafts.STOCK_TARGET
        # 소재는 소모되지 않고 남는다
        assert not saved["materials"][0]["used"]

    def test_full_stock_without_materials_adds_no_tip(self, tmp_path):
        # 답글 씨앗은 재고가 차도 돌지만(TestReplySeeds), 씨앗이 없는 밤에
        # 팁 보충까지 따라 돌면 재고 목표가 무의미해진다.
        data = empty_queue()
        for i in range(generate_drafts.STOCK_TARGET):
            add_draft(data, text=f"재고 {i}", pillar="tip")

        summary, saved, grok = _run(tmp_path, data)

        assert summary["tip_drafts"] == 0
        assert not grok.idea_calls
        assert len(saved["drafts"]) == generate_drafts.STOCK_TARGET

    def test_error_status_counts_toward_stock(self, tmp_path):
        # error 상태(발행 결과 불명 등)를 재고에서 빼면 해소되지 않은 에러가
        # 쌓인 채로 새 초안이 계속 생성돼 문제를 가린다.
        data = empty_queue()
        draft = add_draft(data, text="에러 상태", pillar="tip")
        draft["status"] = "error"
        for i in range(generate_drafts.STOCK_TARGET - 1):
            add_draft(data, text=f"재고 {i}", pillar="tip")

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 0 and summary["tip_drafts"] == 0
        assert not grok.material_calls and not grok.idea_calls
        assert len(saved["drafts"]) == generate_drafts.STOCK_TARGET

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
        assert summary["from_materials"] == 0 and summary["tip_drafts"] == 0
        assert len(saved["drafts"]) == generate_drafts.STOCK_TARGET
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

    def test_reminder_link_comes_from_workspace_url_file(self, tmp_path, monkeypatch):
        """링크 출처는 워치독이 실제로 쓰는 파일이어야 한다.

        워치독이 Serve 로 넘어가며 funnel.url 쓰기를 멈췄다. 소비자가 옛 경로를
        계속 읽으면 디스크에 남은 낡은 파일 덕에 한동안 맞는 것처럼 보이다가,
        호스트명이 바뀌거나 logs/ 를 비우는 순간 링크가 조용히 사라진다.
        """
        url_file = tmp_path / "workspace.url"
        url_file.write_text("https://node.tail0000.ts.net:10000\n", encoding="utf-8")
        monkeypatch.setattr(generate_drafts, "WORKSPACE_URL_PATH", url_file)

        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 1)
        notify = _FakeNotify()

        _run(tmp_path, data, notify=notify, now=NOW)

        assert notify.messages[0].endswith("https://node.tail0000.ts.net:10000")

    def test_reminder_link_is_omitted_when_url_file_is_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            generate_drafts, "WORKSPACE_URL_PATH", tmp_path / "nope" / "workspace.url"
        )

        data = empty_queue()
        _waiting_draft(data, days_ago=generate_drafts.STALE_DRAFT_DAYS + 1)
        notify = _FakeNotify()

        _run(tmp_path, data, notify=notify, now=NOW)

        assert len(notify.messages) == 1
        assert "https://" not in notify.messages[0]

    def test_url_path_matches_what_the_watchdog_writes(self):
        watchdog = (
            Path(__file__).parent.parent / "scripts" / "tunnel_watch.sh"
        ).read_text(encoding="utf-8")
        assert generate_drafts.WORKSPACE_URL_PATH.name == "workspace.url"
        assert generate_drafts.WORKSPACE_URL_PATH.parent.name == "logs"
        assert 'WORKSPACE_URL_FILE="$LOG_DIR/workspace.url"' in watchdog
        assert not hasattr(generate_drafts, "FUNNEL_URL_PATH")

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


def _seed(rid, text, parent="원글 본문"):
    return {"reply_id": rid, "parent_id": "p" + rid, "text": text, "parent_text": parent}


class TestReplySeeds:
    def test_reply_seed_becomes_draft_via_reply_prompt(self, tmp_path):
        source = lambda after, now: ([_seed("101", "그록 한도가 통합되면 줄어드는건지 모르겠네요")], "105")

        summary, saved, grok = _run(tmp_path, empty_queue(), seed_source=source)

        assert summary["reply_seeds_added"] == 1
        assert summary["from_materials"] == 1
        assert grok.reply_calls == [("그록 한도가 통합되면 줄어드는건지 모르겠네요", "원글 본문")]
        assert grok.material_calls == [] and grok.idea_calls == []
        assert saved["drafts"][0]["text"].startswith("[답글글]")
        assert saved["drafts"][0]["status"] == "draft"
        assert saved["materials"][0]["origin"] == "reply"
        assert saved["reply_seeds"]["last_seen_id"] == "105"

    def test_watermark_passed_and_duplicates_not_readded(self, tmp_path):
        data = empty_queue()
        data["reply_seeds"] = {"last_seen_id": "100"}
        add_material(data, "이미 넣은 답글", extra={"origin": "reply", "reply_id": "101"})
        data["materials"][0]["used"] = True
        seen_after = []

        def source(after, now):
            seen_after.append(after)
            return [_seed("101", "이미 넣은 답글")], "101"

        summary, saved, _ = _run(tmp_path, data, seed_source=source)

        assert seen_after == ["100"]
        assert summary["reply_seeds_added"] == 0
        assert len(saved["materials"]) == 1

    def test_skipped_seed_is_marked_used_without_draft(self, tmp_path):
        source = lambda after, now: ([_seed("101", "스킵될 답글")], "101")

        summary, saved, _ = _run(tmp_path, empty_queue(), seed_source=source)

        assert summary["reply_seeds_skipped"] == 1
        assert saved["drafts"] == []
        assert saved["materials"][0]["used"] is True
        assert saved["materials"][0]["skipped"] == "원글 없이 뜻이 안 통함"

    def test_seed_source_failure_does_not_stop_batch(self, tmp_path):
        def boom(after, now):
            raise RuntimeError("x api down")

        summary, saved, grok = _run(tmp_path, empty_queue(), seed_source=boom)

        assert summary["reply_seeds_added"] == 0
        assert summary["tip_drafts"] == 1  # 기존 팁 흐름은 그대로



def _full_tip_stock(data):
    for i in range(generate_drafts.STOCK_TARGET):
        add_draft(data, text=f"팁 초안 {i}", pillar="tip")


def _full_reply_stock(data):
    for i in range(generate_drafts.REPLY_STOCK_TARGET):
        material = add_material(
            data, f"대기 중인 답글 {i}", extra={"origin": "reply", "reply_id": f"w{i}"}
        )
        add_draft(data, text=f"답글 초안 {i}", pillar="curation", material_id=material["id"])


class TestReplySeedGate:
    """답글 씨앗은 전체 재고가 아니라 답글 초안 대기 수로 따로 막는다.

    2026-11-04~19 에는 승인 안 된 팁 초안 4건이 재고 목표를 채워 답글 씨앗이
    16일 동안 한 번도 돌지 못했다. 보충용인 팁이 본래 소재인 답글을 막은 셈이다.
    """

    def test_tip_stock_does_not_block_reply_seeds(self, tmp_path):
        data = empty_queue()
        _full_tip_stock(data)
        source = lambda after, now: ([_seed("101", "재고가 차도 올라와야 하는 답글")], "101")

        summary, saved, grok = _run(tmp_path, data, seed_source=source)

        assert summary["skipped"] is False
        assert summary["reply_seeds_added"] == 1 and summary["from_materials"] == 1
        assert len(grok.reply_calls) == 1
        assert not grok.material_calls and not grok.idea_calls
        assert len(saved["drafts"]) == generate_drafts.STOCK_TARGET + 1
        assert saved["drafts"][-1]["text"].startswith("[답글글]")

    def test_full_stock_converts_only_the_reply_material(self, tmp_path):
        data = empty_queue()
        _full_tip_stock(data)
        add_material(data, "직접 넣은 소재")
        source = lambda after, now: ([_seed("101", "답글 소재")], "101")

        summary, saved, grok = _run(tmp_path, data, seed_source=source)

        assert summary["from_materials"] == 1
        assert not grok.material_calls
        plain = next(m for m in saved["materials"] if m.get("origin") != "reply")
        assert plain["used"] is False

    def test_no_seeding_when_reply_stock_full(self, tmp_path):
        data = empty_queue()
        _full_reply_stock(data)
        called = []

        _run(tmp_path, data, seed_source=lambda a, n: called.append(1) or ([], None))

        assert called == []

    def test_reply_stock_full_leaves_materials_and_tips_to_the_stock_gate(self, tmp_path):
        assert generate_drafts.REPLY_STOCK_TARGET < generate_drafts.STOCK_TARGET
        data = empty_queue()
        _full_reply_stock(data)
        add_material(data, "직접 넣은 소재")

        summary, saved, grok = _run(tmp_path, data)

        assert grok.material_calls == ["직접 넣은 소재"]
        assert summary["from_materials"] == 1

    def test_leftover_reply_material_does_not_block_tip(self, tmp_path):
        # 변환에 실패해 남은 답글 소재가, 답글 재고가 찬 동안 팁 보충까지 막으면 안 된다.
        data = empty_queue()
        _full_reply_stock(data)
        add_material(data, "남은 답글", extra={"origin": "reply", "reply_id": "left"})

        summary, saved, grok = _run(tmp_path, data)

        assert not grok.reply_calls
        assert summary["tip_drafts"] == 1

    def test_skips_entirely_when_both_stocks_full(self, tmp_path):
        data = empty_queue()
        _full_reply_stock(data)
        for i in range(generate_drafts.STOCK_TARGET - generate_drafts.REPLY_STOCK_TARGET):
            add_draft(data, text=f"팁 초안 {i}", pillar="tip")
        add_material(data, "직접 넣은 소재")
        called = []

        summary, saved, grok = _run(
            tmp_path, data, seed_source=lambda a, n: called.append(1) or ([], None)
        )

        assert summary == {"from_materials": 0, "tip_drafts": 0, "skipped": True}
        assert called == []
        assert not grok.material_calls and not grok.reply_calls and not grok.idea_calls
