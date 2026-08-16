"""발행 — 기존 큐 하나를 네 필터로 나눠 보여주고, 초안을 슬롯에 예약하고,
히스토리(발행·실패)를 새 편집 가능한 초안으로 되살린다.

이 화면은 새 데이터를 만들지 않는다. content_queue 가 유일한 출처이고, 여기
테스트가 못 박는 것은 세 가지다.

1. PUBLISH_FILTERS 매핑이 정확히 브리핑대로다 — 예약(scheduled)에는 approved
   와 publishing 이, 실패(failed)에는 error 와 rejected 가 함께 들어간다.
2. 실패 필터 안에서도 비대칭이 있다 — error 초안만 다시 예약할 수 있고
   (legacy tabs/tab_publish_queue.py 의 _can_approve 와 같은 규칙), rejected
   초안은 읽기 전용이며 절대 슬롯 큐로 돌아가지 않는다.
3. 히스토리 재사용(reuse_history_item)은 새 초안을 만들 뿐 원본을 절대
   건드리지 않는다 — 원본이 발행됐든 반려됐든 마찬가지다.
"""

from __future__ import annotations

import asyncio
import time

from nicegui import app
from nicegui.testing import user_simulation

from content_queue import (
    load_queue,
    mark_manual_published,
    queue_transaction,
    upsert_workspace_draft,
)
from workspace_ui import editor, publish
from workspace_ui.app import build_workspace
from workspace_ui.copy import copy
from workspace_ui.publish import (
    PUBLISH_FILTERS,
    load_publish_items,
    reuse_history_item,
    schedule_draft,
)


def _seeded_page(**seed):
    """스토리지에 값이 이미 있는 상태에서 페이지를 그린다 = 재접속/재구성."""

    def build() -> None:
        app.storage.user.update(seed)
        build_workspace()

    return build


async def _wait_until(check, timeout: float = 3.0):
    deadline = time.monotonic() + timeout
    while True:
        value = check()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError("조건이 시간 안에 만족되지 않았다")
        await asyncio.sleep(0.02)


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 브라우저 없이 큐 파일만 본다 (브리핑 Step 1, 원문 그대로)
# ─────────────────────────────────────────────────────────────

def test_publish_filters_show_pending_and_manual_history(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(data, draft_id=None, text="초안", pillar="tip", source_job_id="j1", source_kind="post")
        mark_manual_published(data, draft["id"])
    assert len(load_publish_items("draft", queue_path=path)) == 0
    assert len(load_publish_items("published", queue_path=path)) == 1


def test_history_reuse_opens_a_new_draft(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="지난 글", pillar="tip", source_job_id="j1", source_kind="post")
        mark_manual_published(data, old["id"])
    copied = reuse_history_item(old["id"], queue_path=path)
    assert copied["id"] != old["id"]
    assert copied["status"] == "draft"


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 추가로 못 박는 것들
# ─────────────────────────────────────────────────────────────

def test_publish_filters_mapping_is_exactly_the_briefed_shape():
    assert PUBLISH_FILTERS == {
        "draft": {"draft"},
        "scheduled": {"approved", "publishing"},
        "failed": {"error", "rejected"},
        "published": {"published"},
    }


def test_load_publish_items_unknown_filter_returns_empty(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        upsert_workspace_draft(data, draft_id=None, text="초안", pillar="tip")
    assert load_publish_items("nope", queue_path=path) == []


def test_schedule_draft_calls_approve_draft_and_assigns_a_slot(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(data, draft_id=None, text="예약할 글", pillar="tip")

    scheduled = schedule_draft(draft["id"], queue_path=path)

    assert scheduled["status"] == "approved"
    assert scheduled["slot"]
    assert load_publish_items("draft", queue_path=path) == []
    assert len(load_publish_items("scheduled", queue_path=path)) == 1


def test_schedule_draft_of_a_missing_id_is_a_no_op(tmp_path):
    path = tmp_path / "queue.json"
    assert schedule_draft("nope-does-not-exist", queue_path=path) is None


def test_reuse_history_item_of_a_missing_id_is_a_no_op(tmp_path):
    path = tmp_path / "queue.json"
    assert reuse_history_item("nope-does-not-exist", queue_path=path) is None


def test_reuse_history_item_never_mutates_the_source_draft(tmp_path):
    """원본이 반려(rejected)든 발행(published)이든, 재사용은 새 초안만 만들고
    원본 레코드는 어떤 필드도 바뀌지 않는다."""
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        rejected = upsert_workspace_draft(data, draft_id=None, text="반려된 글", pillar="tip")
        rejected["status"] = "rejected"
        rejected["slot"] = None
        before = dict(rejected)

    copied = reuse_history_item(rejected["id"], queue_path=path)

    assert copied["id"] != rejected["id"]
    assert copied["status"] == "draft"
    stored_source = next(d for d in load_queue(path)["drafts"] if d["id"] == rejected["id"])
    assert stored_source == before


# ─────────────────────────────────────────────────────────────
# 화면 — 필터 전환, 예약, 히스토리 열람·재사용 (Pattern A user_simulation)
# ─────────────────────────────────────────────────────────────

def _seed_all_statuses(path):
    """네 필터 각각에 카드가 하나씩 걸리는 큐를 만든다."""
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(
            data, draft_id=None, text="초안 상태 글", pillar="tip",
            source_job_id="j1", source_kind="post",
        )

        approved = upsert_workspace_draft(
            data, draft_id=None, text="예약된 글", pillar="build_in_public",
        )
        approved["status"] = "approved"
        approved["slot"] = "2026-08-20T08:00:00"

        error_draft = upsert_workspace_draft(
            data, draft_id=None, text="검토가 필요한 글", pillar="retrospective",
        )
        error_draft["status"] = "error"

        rejected = upsert_workspace_draft(
            data, draft_id=None, text="반려된 글", pillar="curation",
        )
        rejected["status"] = "rejected"

        api_published = upsert_workspace_draft(
            data, draft_id=None, text="API로 나간 글", pillar="tip",
        )
        api_published["status"] = "published"
        api_published["tweet_id"] = "999888777"
        api_published["published_at"] = "2026-08-15T08:00:00"

        manual_published = upsert_workspace_draft(
            data, draft_id=None, text="수동으로 올린 글", pillar="tip",
        )
        mark_manual_published(data, manual_published["id"])

    return {
        "draft": draft,
        "approved": approved,
        "error": error_draft,
        "rejected": rejected,
        "api_published": api_published,
        "manual_published": manual_published,
    }


async def test_switching_all_four_filters_shows_the_matching_cards(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    seeded = _seed_all_statuses(path)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()

        # 기본은 초안 탭이다.
        await user.should_see(marker=f"publish-card-{seeded['draft']['id']}")
        await user.should_not_see(marker=f"publish-card-{seeded['approved']['id']}")

        user.find(marker="publish-filter-scheduled").click()
        await user.should_see(marker=f"publish-card-{seeded['approved']['id']}")
        await user.should_not_see(marker=f"publish-card-{seeded['draft']['id']}")

        user.find(marker="publish-filter-failed").click()
        await user.should_see(marker=f"publish-card-{seeded['error']['id']}")
        await user.should_see(marker=f"publish-card-{seeded['rejected']['id']}")
        await user.should_not_see(marker=f"publish-card-{seeded['approved']['id']}")

        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{seeded['api_published']['id']}")
        await user.should_see(marker=f"publish-card-{seeded['manual_published']['id']}")
        await user.should_not_see(marker=f"publish-card-{seeded['error']['id']}")

        user.find(marker="publish-filter-draft").click()
        await user.should_see(marker=f"publish-card-{seeded['draft']['id']}")


async def test_approving_a_draft_moves_it_into_the_scheduled_filter(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    seeded = _seed_all_statuses(path)
    draft_id = seeded["draft"]["id"]

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        await user.should_see(marker=f"publish-schedule-{draft_id}")

        user.find(marker=f"publish-schedule-{draft_id}").click()
        await user.should_not_see(marker=f"publish-card-{draft_id}")

        stored = await _wait_until(
            lambda: next((d for d in load_queue(path)["drafts"] if d["id"] == draft_id), None)
        )
        assert stored["status"] == "approved"
        assert stored["slot"]

        user.find(marker="publish-filter-scheduled").click()
        await user.should_see(marker=f"publish-card-{draft_id}")


async def test_failed_filter_only_lets_error_cards_retry(monkeypatch, tmp_path):
    """실패 필터 안의 비대칭: error 카드만 재예약 버튼이 있고, rejected
    카드는 조회만 되며 절대 슬롯 큐로 돌아가지 않는다."""
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    seeded = _seed_all_statuses(path)
    error_id = seeded["error"]["id"]
    rejected_id = seeded["rejected"]["id"]

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-failed").click()

        await user.should_see(marker=f"publish-retry-{error_id}")
        await user.should_see(marker=f"publish-card-{rejected_id}")
        await user.should_not_see(marker=f"publish-retry-{rejected_id}")

        # rejected 카드도 재사용(복제) 버튼은 열람 뒤에 볼 수 있다 — 슬롯
        # 큐로 돌아가는 것과는 다른 행동이다.
        user.find(marker=f"publish-open-{rejected_id}").click()
        await user.should_see(marker=f"publish-reuse-{rejected_id}")
        await user.should_not_see(marker=f"publish-retry-{rejected_id}")

        # error 카드를 재예약해도 rejected 카드는 그대로 실패 탭에 남는다
        # (조용히 사라지지 않는다).
        user.find(marker=f"publish-retry-{error_id}").click()
        await _wait_until(
            lambda: next(
                (d for d in load_queue(path)["drafts"] if d["id"] == error_id), {}
            ).get("status") == "approved"
        )
        await user.should_see(marker=f"publish-card-{rejected_id}")


async def test_opening_a_historical_item_reveals_its_full_text(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    long_text = "긴 글 " * 40
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(data, draft_id=None, text=long_text, pillar="tip")
        mark_manual_published(data, draft["id"])

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{draft['id']}")

        # 펼치기 전에는 전체 본문(마커)이 그려지지 않는다.
        await user.should_not_see(marker=f"publish-text-{draft['id']}")

        user.find(marker=f"publish-open-{draft['id']}").click()

        await user.should_see(marker=f"publish-text-{draft['id']}")
        await user.should_see(marker=f"publish-reuse-{draft['id']}")


async def test_duplicating_a_historical_item_never_mutates_its_source(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="예전에 쓴 글", pillar="tip")
        mark_manual_published(data, old["id"])
        before = dict(old)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{old['id']}")

        user.find(marker=f"publish-open-{old['id']}").click()
        await user.should_see(marker=f"publish-reuse-{old['id']}")

        user.find(marker=f"publish-reuse-{old['id']}").click()

        # 재사용은 공유 에디터를 그 자리에 연다 — 원본이 아니라 새 초안을.
        await user.should_see(marker="editor-text")
        await user.should_see("예전에 쓴 글")

        drafts = await _wait_until(lambda: load_queue(path)["drafts"] or None)
        assert len(drafts) == 2
        source_after = next(d for d in drafts if d["id"] == old["id"])
        assert source_after == before

        copy_draft = next(d for d in drafts if d["id"] != old["id"])
        assert copy_draft["status"] == "draft"
        assert copy_draft["text"] == "예전에 쓴 글"


async def test_reused_draft_publishes_through_the_shared_editor(monkeypatch, tmp_path):
    """재사용으로 연 에디터도 창작·다듬기 에디터와 같은 계약을 지킨다 —
    "게시했음" 을 누르면 발행 큐에 수동 발행으로 기록되고 원본 초안은
    새로 늘지 않는다."""
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="다시 쓸 글", pillar="tip")
        mark_manual_published(data, old["id"])

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{old['id']}")

        user.find(marker=f"publish-open-{old['id']}").click()
        await user.should_see(marker=f"publish-reuse-{old['id']}")
        user.find(marker=f"publish-reuse-{old['id']}").click()
        await user.should_see(marker="editor-published")

        user.find(marker="editor-published").click()

        stored = await _wait_until(
            lambda: next(
                (d for d in load_queue(path)["drafts"]
                 if d["id"] != old["id"] and d["status"] == "published"),
                None,
            )
        )
        assert stored["manual_published"] is True
        assert len(load_queue(path)["drafts"]) == 2

        # 편집기가 닫혔고, 원본 발행 글은 여전히 하나뿐이다.
        await user.should_not_see(marker="editor-text")


async def test_published_card_shows_x_link_only_when_tweet_id_exists(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    seeded = _seed_all_statuses(path)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{seeded['api_published']['id']}")

        user.find(marker=f"publish-open-{seeded['api_published']['id']}").click()
        await user.should_see(marker=f"publish-x-link-{seeded['api_published']['id']}")
        with user.client:
            link = next(iter(
                user.find(marker=f"publish-x-link-{seeded['api_published']['id']}").elements
            ))
        assert link.props["href"] == "https://x.com/i/status/999888777"

        user.find(marker=f"publish-open-{seeded['manual_published']['id']}").click()
        await user.should_see(marker=f"publish-reuse-{seeded['manual_published']['id']}")
        await user.should_not_see(marker=f"publish-x-link-{seeded['manual_published']['id']}")


async def test_reconnect_restores_the_open_editor_without_resubmitting(monkeypatch, tmp_path):
    """재사용으로 초안을 열어 둔 채 재접속해도 같은 초안을 그대로 이어
    편집한다 — 새 복제본을 또 만들지 않는다(만들기·다듬기와 같은 재접속
    규칙)."""
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="원본", pillar="tip")
        mark_manual_published(data, old["id"])
    copied = publish.reuse_history_item(old["id"], queue_path=path)

    page = _seeded_page(
        publish_editor_job_id=publish._reuse_job_id(old["id"]),
        publish_editor_draft_id=copied["id"],
        publish_editor_text=copied["text"],
        publish_reuse_pillar=copied["pillar"],
    )
    async with user_simulation(page) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()

        await user.should_see(marker="editor-text")
        await user.should_see("원본")

        assert len(load_queue(path)["drafts"]) == 2


async def test_reuse_editor_back_button_returns_to_the_list_without_publishing(monkeypatch, tmp_path):
    """재사용 에디터에 잘못 들어와도 "목록으로 돌아가기" 로 그냥 나갈 수
    있다 — 발행을 기록하지 않고, 복제본은 초안으로 큐에 그대로 남는다.
    (리뷰 Finding 2: 이전에는 발행을 기록하거나 빈 본문으로 만드는 것
    말고는 재사용 에디터를 빠져나갈 길이 없었다.)"""
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="원본 글", pillar="tip")
        mark_manual_published(data, old["id"])

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        user.find(marker="publish-filter-published").click()
        await user.should_see(marker=f"publish-card-{old['id']}")

        user.find(marker=f"publish-open-{old['id']}").click()
        await user.should_see(marker=f"publish-reuse-{old['id']}")
        user.find(marker=f"publish-reuse-{old['id']}").click()
        await user.should_see(marker="editor-text")
        await user.should_see(marker="publish-editor-back")

        user.find(marker="publish-editor-back").click()

        # 목록으로 돌아갔다 — 필터 탭이 다시 보이고 에디터는 사라졌다.
        await user.should_see(marker="publish-filters")
        await user.should_not_see(marker="editor-text")

        with user.client:
            assert app.storage.user[publish._EDITOR_KEYS.job_id] is None
            assert app.storage.user[publish._EDITOR_KEYS.draft_id] is None

        # 복제본은 잃지 않았다 — 초안 상태로 큐에 남아 있고, 원본은 여전히
        # (수동) 발행 상태 그대로다.
        drafts = load_queue(path)["drafts"]
        assert len(drafts) == 2
        source_after = next(d for d in drafts if d["id"] == old["id"])
        assert source_after["status"] == "published"
        assert source_after["manual_published"] is True
        copy_draft = next(d for d in drafts if d["id"] != old["id"])
        assert copy_draft["status"] == "draft"
        assert copy_draft["text"] == "원본 글"

        # 목록으로 돌아온 뒤 그 초안을 다시 열 수도 있다(잃지 않았다는
        # 증거) — 초안 필터로 가면 보인다.
        user.find(marker="publish-filter-draft").click()
        await user.should_see(marker=f"publish-card-{copy_draft['id']}")


async def test_stale_reload_never_lets_a_rejected_draft_render_under_the_draft_filters_rules(
    monkeypatch, tmp_path
):
    """빠른 필터 전환 중 먼저 시작한 느린 읽기가 나중에 끝나도, 화면은
    항상 지금 store["publish_filter"] 에 맞는 항목만 그 필터의 규칙으로
    그린다. 특히 반려(rejected) 초안은 어떤 뒤섞임에도 예약 버튼을 받지
    않는다 — content_queue.approve_draft 에는 상태 가드가 없으므로, 이
    불변식이 깨지면 반려 초안이 그대로 슬롯 큐에 들어갈 수 있다.
    (리뷰 Finding 1)"""
    path = tmp_path / "queue.json"
    monkeypatch.setattr(publish, "QUEUE_PATH", path)
    seeded = _seed_all_statuses(path)
    rejected_id = seeded["rejected"]["id"]
    draft_id = seeded["draft"]["id"]

    real_load = publish.load_publish_items
    reached_failed = asyncio.Event()
    release_failed = asyncio.Event()

    async def slow_io_bound(func, *args, **kwargs):
        # run.io_bound 를 흉내 내되, "실패" 필터 읽기만 release_failed 가
        # 풀릴 때까지 붙잡아 둔다 — 나머지(초안 필터 읽기 등)는 그대로
        # 즉시 실행한다.
        if func is real_load and args and args[0] == "failed":
            reached_failed.set()
            await release_failed.wait()
        return func(*args, **kwargs)

    monkeypatch.setattr(publish.run, "io_bound", slow_io_bound)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-publish").click()
        await user.should_see(marker=f"publish-card-{draft_id}")
        await user.should_see(marker=f"publish-schedule-{draft_id}")

        # 실패 탭으로 전환한다 — 이 읽기는 release_failed 가 풀릴 때까지
        # 멈춘 채로 대기한다.
        user.find(marker="publish-filter-failed").click()
        await asyncio.wait_for(reached_failed.wait(), timeout=2.0)

        # 느린 읽기가 아직 끝나지 않았는데, 초안 탭으로 되돌아간다 — 두
        # 번째(빠른) reload() 가 먼저 끝나 초안 필터를 올바르게 그린다.
        user.find(marker="publish-filter-draft").click()
        await user.should_see(marker=f"publish-card-{draft_id}")
        await user.should_see(marker=f"publish-schedule-{draft_id}")

        # 이제서야 느린 "실패" 읽기를 풀어준다. 화면은 이미 "초안" 필터를
        # 보고 있으므로 이 결과는 낡은 것으로 버려져야 한다.
        release_failed.set()
        await asyncio.sleep(0.3)

        # 반려 초안이 초안 탭에 새어 들어오지 않았고, 무엇보다 예약 버튼을
        # 받지 않았다 — approve_draft 는 상태를 가리지 않으므로, 버튼이
        # 있었다면 눌렀을 때 반려 초안이 그대로 슬롯 큐에 들어갔을 것이다.
        await user.should_not_see(marker=f"publish-card-{rejected_id}")
        await user.should_not_see(marker=f"publish-schedule-{rejected_id}")
        await user.should_see(marker=f"publish-card-{draft_id}")
        await user.should_see(marker=f"publish-schedule-{draft_id}")
