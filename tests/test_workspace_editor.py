"""완성한 포스트를 고치는 에디터 — 자동저장, X 작성 화면, 수동 발행 기록.

에디터의 계약은 두 가지다. (1) 사람이 친 글자는 무슨 일이 있어도 사라지지
않는다. (2) 초안 하나가 두 개로 불어나지 않는다. 자동저장이 무손실이라는
말은 오래된 draft_id 를 만나면 새 초안을 만든다는 뜻이고, 그래서 발행을
기록한 뒤 에디터 상태를 지우지 않으면 뒤늦은 자동저장이 유령 초안을
낳는다 — 아래 테스트가 그 두 경계를 함께 못 박는다.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
import time

from nicegui import app
from nicegui.testing import user_simulation

import content_queue
import workspace_job_runner
import workspace_jobs
from content_queue import load_queue, queue_transaction, upsert_workspace_draft
from utils import generate_tweet_intent_url
from workspace_ui import editor
from workspace_ui.app import build_workspace
from workspace_ui.copy import copy
from workspace_ui.editor import (
    editor_pillar,
    mark_editor_published,
    save_editor_draft,
    x_compose_url,
)


POST_JOB = {
    "id": "post-1",
    "kind": "post",
    "status": "completed",
    "engine": "Demo",
    "language": "ko",
    "request": {"keywords": "배포 실수", "direction": {"title": "A"}, "length": 0, "mode": "builder_note"},
    # 데모 결과에는 _lint 가 없다 — 에디터는 어떤 키도 필수로 요구하지 않는다.
    "result": {"post": {"title": "배포 실수", "content": "첫 문장"}},
}


def _seeded_page(**seed):
    """스토리지에 이미 값이 들어 있는 상태로 페이지를 다시 그린다 =
    재접속/페이지 재구성. 새 요청을 보내지 않고 저장된 것만 복원해야 한다."""

    def build() -> None:
        app.storage.user.update(seed)
        build_workspace()

    return build


def _boom(message: str):
    raise AssertionError(message)


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
# 순수 헬퍼
# ─────────────────────────────────────────────────────────────

def test_editor_autosave_and_manual_publish_keep_history(tmp_path):
    draft = save_editor_draft(None, "첫 문장", "tip", "post-1", queue_path=tmp_path / "queue.json")
    save_editor_draft(draft["id"], "수정한 문장", "tip", "post-1", queue_path=tmp_path / "queue.json")
    mark_editor_published(draft["id"], queue_path=tmp_path / "queue.json")
    saved = load_queue(tmp_path / "queue.json")["drafts"][0]
    assert (saved["text"], saved["manual_published"]) == ("수정한 문장", True)


def test_autosave_records_where_the_text_came_from(tmp_path):
    path = tmp_path / "queue.json"
    draft = save_editor_draft(None, "첫 문장", "tip", "post-1", queue_path=path)

    assert draft["status"] == "draft"
    assert draft["origin"] == "workspace"
    assert (draft["source_job_id"], draft["source_kind"]) == ("post-1", "post")
    # 이어지는 자동저장은 provenance 를 다시 보내지 않아도 값을 잃지 않는다.
    save_editor_draft(draft["id"], "고친 문장", "tip", queue_path=path)
    stored = load_queue(path)["drafts"][0]
    assert (stored["source_job_id"], stored["source_kind"]) == ("post-1", "post")


def test_blank_text_never_creates_a_draft(tmp_path):
    path = tmp_path / "queue.json"
    assert save_editor_draft(None, "   ", "tip", "post-1", queue_path=path) is None
    assert load_queue(path)["drafts"] == []


def test_edit_after_publish_becomes_a_new_draft_instead_of_vanishing(tmp_path):
    path = tmp_path / "queue.json"
    first = save_editor_draft(None, "첫 문장", "tip", "post-1", queue_path=path)
    mark_editor_published(first["id"], queue_path=path)

    late = save_editor_draft(first["id"], "뒤늦게 고친 문장", "tip", "post-1", queue_path=path)

    drafts = load_queue(path)["drafts"]
    assert len(drafts) == 2
    assert late["id"] != first["id"]
    assert drafts[0]["text"] == "첫 문장" and drafts[0]["status"] == "published"
    assert drafts[1]["text"] == "뒤늦게 고친 문장" and drafts[1]["status"] == "draft"


def test_manual_publish_never_touches_an_api_published_draft(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(data, None, "이미 API로 나간 글", "tip", "post-1", "post")
        draft["tweet_id"] = "1234567890"
        draft["status"] = "published"
        draft_id = draft["id"]

    assert mark_editor_published(draft_id, queue_path=path) is None
    stored = load_queue(path)["drafts"][0]
    assert stored["tweet_id"] == "1234567890"
    assert "manual_published" not in stored


def test_manual_publish_of_a_missing_draft_is_a_no_op(tmp_path):
    path = tmp_path / "queue.json"
    assert mark_editor_published("nope", queue_path=path) is None
    assert load_queue(path)["drafts"] == []


def test_x_compose_url_matches_the_existing_intent_link():
    text = "배포 실수로 배운 것 & 다음 회고"
    assert x_compose_url(text) == generate_tweet_intent_url(text)
    assert x_compose_url(text).startswith("https://x.com/intent/post?text=")
    # 공백과 특수문자는 인코딩되어 링크가 잘리지 않는다.
    assert " " not in x_compose_url(text)


def test_editor_pillar_follows_the_mode_and_grounded_tips_are_tips():
    assert editor_pillar("builder_note", "ideas") == "build_in_public"
    assert editor_pillar("hook", "ideas") == "tip"
    assert editor_pillar("auto_mix", "ideas") == "curation"
    # 사실 기반 팁은 어떤 모드로 쓰든 팁이다.
    assert editor_pillar("builder_note", "grounded_tip") == "tip"


# ─────────────────────────────────────────────────────────────
# 화면 — 자동저장과 수동 발행 기록
# ─────────────────────────────────────────────────────────────

async def test_completed_post_is_saved_immediately_and_autosaves_edits(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)
    monkeypatch.setattr(
        workspace_job_runner, "submit_job",
        lambda *a, **k: _boom("에디터를 여는 것만으로 새 요청이 나갔다"),
    )

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-text")

        # 완성 결과는 화면에 뜨는 즉시 초안이 된다 — 저장 버튼을 기다리지 않는다.
        saved = load_queue(path)["drafts"]
        assert len(saved) == 1
        assert saved[0]["text"] == "첫 문장"
        assert saved[0]["status"] == "draft"
        assert saved[0]["source_job_id"] == "post-1"

        user.find(marker="editor-text").type(" 그리고 둘째 문장")
        await _wait_until(lambda: load_queue(path)["drafts"][0]["text"] == "첫 문장 그리고 둘째 문장")
        # 자동저장은 같은 초안을 고칠 뿐 새 초안을 만들지 않는다.
        assert len(load_queue(path)["drafts"]) == 1


async def test_reconnect_keeps_the_text_that_autosave_had_not_written_yet(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    # 파일에는 옛 본문, 스토리지에는 사람이 방금 친 본문 — 자동저장이 돌기
    # 전에 페이지가 다시 그려진 상황이다.
    draft = save_editor_draft(None, "첫 문장", "tip", "post-1", queue_path=path)
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    page = _seeded_page(
        active_post_job_id="post-1",
        editor_job_id="post-1",
        editor_draft_id=draft["id"],
        editor_text="사람이 방금 친 문장",
    )
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see("사람이 방금 친 문장")

        await _wait_until(lambda: load_queue(path)["drafts"][0]["text"] == "사람이 방금 친 문장")
        assert len(load_queue(path)["drafts"]) == 1


async def test_x_composer_link_opens_a_new_tab_without_changing_status(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-x-link")

        with user.client:
            link = next(iter(user.find(marker="editor-x-link").elements))
        assert link.props["target"] == "_blank"
        assert link.props["href"] == x_compose_url("첫 문장")
        # 링크를 그리는 것만으로 상태가 바뀌면 안 된다 — 발행은 별도 행동이다.
        assert load_queue(path)["drafts"][0]["status"] == "draft"


async def test_saving_to_the_queue_leaves_the_draft_ready_for_approval(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-save")

        user.find(marker="editor-text").type(" 마지막 줄")
        user.find(marker="editor-save").click()

        stored = await _wait_until(
            lambda: load_queue(path)["drafts"][0]
            if load_queue(path)["drafts"][0]["text"] == "첫 문장 마지막 줄" else None
        )
        # 발행 큐 저장은 승인/예약을 대신하지 않는다 (Task 8 의 몫).
        assert stored["status"] == "draft"
        assert stored["slot"] is None
        assert "manual_published" not in stored


async def test_queue_contention_never_freezes_the_event_loop(monkeypatch, tmp_path):
    """배치가 큐 락을 잡고 있어도 서버는 계속 돈다.

    큐 락은 flock 을 최대 10초까지 기다리며 time.sleep 으로 busy-wait 한다.
    그 기다림이 이벤트 루프에서 일어나면 그 동안 이 사람뿐 아니라 접속한
    모든 클라이언트와 모든 타이머가 함께 멈춘다.
    """
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-text")

        holding = threading.Event()
        released = threading.Event()

        def hold_the_queue_lock() -> None:
            # launchd 배치(generate_drafts, publish_worker)가 같은 flock 을 잡은 상황.
            with content_queue.queue_lock(path, timeout=5.0):
                holding.set()
                released.wait(5.0)

        holder = threading.Thread(target=hold_the_queue_lock, daemon=True)
        holder.start()
        assert holding.wait(2.0)

        ticks = 0

        async def heartbeat() -> None:
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0.01)

        beat = asyncio.create_task(heartbeat())
        try:
            user.find(marker="editor-text").type(" 둘째 문장")
            user.find(marker="editor-save").click()
            await asyncio.sleep(0.3)

            # 저장은 아직 락을 기다리는 중이지만 루프는 살아 있다.
            assert ticks > 5
            assert load_queue(path)["drafts"][0]["text"] == "첫 문장"
        finally:
            released.set()
            holder.join(5.0)
            beat.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await beat

        await _wait_until(lambda: load_queue(path)["drafts"][0]["text"] == "첫 문장 둘째 문장")


async def test_concurrent_writes_cannot_leave_a_ghost_draft(monkeypatch, tmp_path):
    """자동저장이 쓰는 중에 저장 버튼이 겹쳐도 초안은 하나다.

    저장은 "초안 ID 를 읽고 → 파일에 쓰고 → 받은 ID 를 되쓰는" 세 걸음이고
    그 사이에 await 가 있다. 자동저장 틱과 버튼 클릭은 서로 다른 태스크라,
    직렬화하지 않으면 둘 다 비어 있는 ID(None)를 읽고 각자 새 초안을 만든다.
    """
    path = tmp_path / "queue.json"
    real_save = editor.save_editor_draft
    saves = {"started": 0, "finished": 0}
    painting = {"now": True}

    def slow_save(*args, **kwargs):
        if painting["now"]:
            # 그리는 도중의 첫 저장이 경합으로 실패한 상태 = 초안 ID 가 없다.
            raise TimeoutError("paint lock timeout")
        saves["started"] += 1
        try:
            time.sleep(0.25)  # 워커 스레드 안에서만 느리다
            return real_save(*args, **kwargs)
        finally:
            saves["finished"] += 1

    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(editor, "save_editor_draft", slow_save)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-text")
        assert load_queue(path)["drafts"] == []

        painting["now"] = False
        user.find(marker="editor-text").type(" 가")
        await _wait_until(lambda: saves["started"] >= 1)

        # 자동저장이 아직 파일을 쓰는 중에 사람이 저장을 누른다.
        user.find(marker="editor-text").type("나")
        user.find(marker="editor-save").click()

        await _wait_until(lambda: saves["finished"] >= 2, timeout=5.0)
        await asyncio.sleep(0.4)

        drafts = load_queue(path)["drafts"]
        assert len(drafts) == 1
        assert drafts[0]["text"] == "첫 문장 가나"


async def test_page_rebuild_keeps_edits_when_the_first_save_never_landed(monkeypatch, tmp_path):
    """초안 ID 가 없어도 복원은 복원이다.

    첫 저장이 경합으로 실패하면 editor_draft_id 는 비어 있다. 그 상태에서
    다시 그릴 때 "완성 결과를 처음 본다" 로 착각하면, 사람이 이미 고쳐 둔
    본문을 원래 생성 결과가 덮어써 버린다.
    """
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    page = _seeded_page(
        active_post_job_id="post-1",
        editor_job_id="post-1",
        editor_draft_id=None,
        editor_text="사람이 고친 문장",
    )
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see("사람이 고친 문장")
        # 생성 결과("첫 문장")가 사람의 편집을 밀어내지 않았다.
        await user.should_not_see("첫 문장")

        # 초안이 없던 상태에서도 자동저장이 그 본문으로 초안 하나를 만든다.
        stored = await _wait_until(
            lambda: load_queue(path)["drafts"][0] if load_queue(path)["drafts"] else None
        )
        assert stored["text"] == "사람이 고친 문장"
        assert stored["source_job_id"] == "post-1"
        assert len(load_queue(path)["drafts"]) == 1


async def test_queue_lock_timeout_is_visible_and_autosave_retries(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    contended = {"now": False}
    real_save = editor.save_editor_draft

    def flaky_save(*args, **kwargs):
        if contended["now"]:
            raise TimeoutError(f"queue lock timeout (10.0s): {path}")
        return real_save(*args, **kwargs)

    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(editor, "save_editor_draft", flaky_save)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-text")
        assert load_queue(path)["drafts"][0]["text"] == "첫 문장"

        contended["now"] = True
        user.find(marker="editor-text").type(" 둘째 문장")
        user.find(marker="editor-save").click()

        # 저장이 멈춘 걸 사람이 알아야 한다. 저장했다고 거짓말하지 않는다.
        await user.should_see(copy("queue_busy"))
        await user.should_not_see(copy("editor_saved"))
        assert load_queue(path)["drafts"][0]["text"] == "첫 문장"

        # 기준선이 올라가지 않았으므로 락이 풀리면 다음 틱이 다시 쓴다.
        contended["now"] = False
        await _wait_until(lambda: load_queue(path)["drafts"][0]["text"] == "첫 문장 둘째 문장")
        assert len(load_queue(path)["drafts"]) == 1


async def test_publish_timeout_keeps_the_editor_and_its_draft(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    contended = {"now": False}
    real_mark = editor.mark_editor_published

    def flaky_mark(*args, **kwargs):
        if contended["now"]:
            raise TimeoutError(f"queue lock timeout (10.0s): {path}")
        return real_mark(*args, **kwargs)

    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(editor, "mark_editor_published", flaky_mark)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-published")

        contended["now"] = True
        user.find(marker="editor-published").click()

        await user.should_see(copy("queue_busy"))
        # 기록하지 못했으니 에디터를 닫지 않는다 — 초안 연결도 그대로다.
        await user.should_see(marker="editor-text")
        await user.should_not_see(copy("editor_published"))
        assert load_queue(path)["drafts"][0]["status"] == "draft"

        contended["now"] = False
        user.find(marker="editor-published").click()

        stored = await _wait_until(
            lambda: load_queue(path)["drafts"][0]
            if load_queue(path)["drafts"][0]["status"] == "published" else None
        )
        assert stored["manual_published"] is True
        # 실패한 시도가 유령 초안을 남기지 않았다.
        assert len(load_queue(path)["drafts"]) == 1


async def test_marking_published_clears_the_editor_so_autosave_cannot_duplicate(monkeypatch, tmp_path):
    path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: POST_JOB if job_id == "post-1" else None)

    async with user_simulation(_seeded_page(active_post_job_id="post-1")) as user:
        await user.open("/")
        await user.should_see(marker="editor-published")

        user.find(marker="editor-published").click()

        stored = await _wait_until(
            lambda: load_queue(path)["drafts"][0]
            if load_queue(path)["drafts"][0]["status"] == "published" else None
        )
        assert stored["manual_published"] is True
        assert "tweet_id" not in stored

        # 발행을 기록한 뒤에는 에디터가 닫히고, 남아 있던 자동저장도 유령
        # 초안을 만들지 못한다.
        await user.should_not_see(marker="editor-text")
        await asyncio.sleep(0.2)
        assert len(load_queue(path)["drafts"]) == 1


