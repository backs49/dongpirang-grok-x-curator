"""만들기 영역 — 주제 한 줄 → 방향 3장 → 고른 하나 → 포스트 한 편.

이 영역이 존재하는 이유는 비용이다. 방향 카드는 싸고 완성 글은 비싸다.
그래서 여기 테스트는 "무엇이 보이는가" 만큼이나 "요청이 몇 번 나갔는가"를
못 박는다. 특히 재접속·페이지 재구성은 저장된 작업 ID 를 다시 읽을 뿐,
어떤 경우에도 프로바이더를 다시 부르지 않아야 한다.
"""

from __future__ import annotations

import asyncio
import time

from nicegui import app
from nicegui.testing import user_simulation

import workspace_job_runner
import workspace_jobs
from content_queue import load_queue
from workspace_ui import editor, job_view
from workspace_ui.app import build_workspace
from workspace_ui.copy import copy
from workspace_ui.create import submit_directions, submit_selected_direction


DIRECTION_A = {"title": "A", "hook": "h", "angle": "a", "core_message": "m"}
DIRECTIONS = [
    {
        "title": f"방향 {n}",
        "hook": f"훅 {n}",
        "angle": f"각도 {n}",
        "core_message": f"핵심 {n}",
    }
    for n in (1, 2, 3)
]


def _job(job_id: str, kind: str, status: str, **extra) -> dict:
    return {
        "id": job_id,
        "kind": kind,
        "status": status,
        "engine": "Demo",
        "language": "ko",
        "request": {},
        **extra,
    }


DIRECTIONS_DONE = _job("dir-1", "directions", "completed", result={"directions": DIRECTIONS})
POST_DONE = _job(
    "post-1", "post", "completed",
    result={"post": {"title": "제목", "content": "완성한 본문"}},
)


def _seeded_page(**seed):
    """스토리지에 값이 이미 있는 상태에서 페이지를 그린다 = 재접속/재구성."""

    def build() -> None:
        app.storage.user.update(seed)
        build_workspace()

    return build


def _recording_submitter(calls: list, job_id: str = "new-job"):
    def submit(kind, request, *, engine="", language="", **kwargs):
        calls.append({"kind": kind, "request": request, "engine": engine, "language": language})
        return _job(job_id, kind, "queued")

    return submit


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
# 순수 헬퍼 — 브라우저 없이 요청의 모양만 본다
# ─────────────────────────────────────────────────────────────

def test_create_request_contains_no_full_post_until_direction_is_selected():
    captured = []
    submit_directions(
        {"keywords": "배포 실수", "mode": "builder_note"},
        submitter=lambda kind, request, **kwargs: captured.append((kind, request)) or {"id": "d1"},
    )
    assert captured == [("directions", {"keywords": "배포 실수", "mode": "builder_note"})]


def test_selecting_a_direction_submits_one_post_job():
    captured = []
    submit_selected_direction(
        keywords="배포 실수", direction={"title": "A", "hook": "h", "angle": "a", "core_message": "m"},
        length=280, mode="builder_note", language="ko", content_type="ideas",
        submitter=lambda kind, request, **kwargs: captured.append((kind, request)) or {"id": "p1"},
    )
    assert captured[0][0] == "post"
    assert captured[0][1]["direction"]["title"] == "A"


def test_blank_topic_never_reaches_the_job_store():
    captured = []
    submitter = _recording_submitter(captured)

    assert submit_directions({"keywords": "   ", "mode": "hook"}, submitter=submitter) is None
    assert submit_directions({"mode": "hook"}, submitter=submitter) is None
    assert captured == []


def test_directions_request_carries_the_engine_and_language_snapshot():
    captured = []
    submit_directions(
        {"keywords": "  배포 실수  ", "mode": "hook"},
        submitter=_recording_submitter(captured),
        engine="Codex CLI",
        language="en",
    )
    assert captured[0]["engine"] == "Codex CLI"
    assert captured[0]["language"] == "en"
    # 앞뒤 공백은 요청에 담지 않는다.
    assert captured[0]["request"]["keywords"] == "배포 실수"


def test_post_request_copies_only_the_four_direction_fields():
    captured = []
    submit_selected_direction(
        keywords="배포 실수",
        direction={**DIRECTION_A, "_lint": {"s1": ["ㅋ"]}, "extra": "버려질 값"},
        length=0, mode="builder_note", language="ko", content_type="ideas",
        submitter=_recording_submitter(captured),
    )
    assert captured[0]["request"]["direction"] == DIRECTION_A
    assert captured[0]["request"] == {
        "keywords": "배포 실수",
        "direction": DIRECTION_A,
        "length": 0,
        "mode": "builder_note",
    }


def test_grounded_tip_selection_rides_along_with_category_and_references():
    captured = []
    submit_selected_direction(
        keywords="전세 사기",
        direction=DIRECTION_A,
        length=400, mode="serious", language="ko",
        content_type="grounded_tip", category="finance", references="https://example.gov/notice",
        submitter=_recording_submitter(captured),
    )
    request = captured[0]["request"]
    # 워커는 content_type 을 보고 write_grounded_post 로 분기한다.
    assert request["content_type"] == "grounded_tip"
    assert request["category"] == "finance"
    assert request["references"] == "https://example.gov/notice"


def test_incomplete_direction_is_never_submitted():
    captured = []
    submitter = _recording_submitter(captured)

    assert submit_selected_direction(
        keywords="배포 실수", direction={"title": "A", "hook": "", "angle": "a", "core_message": "m"},
        length=0, mode="hook", language="ko", content_type="ideas", submitter=submitter,
    ) is None
    assert submit_selected_direction(
        keywords="", direction=DIRECTION_A,
        length=0, mode="hook", language="ko", content_type="ideas", submitter=submitter,
    ) is None
    assert captured == []


def test_job_errors_read_as_sentences_without_hiding_the_unknown_ones():
    # grok_client 가 남기는 키는 문구가 있고,
    assert "방향 카드" in job_view.error_message("invalid_directions")
    assert "본문" in job_view.error_message("invalid_post")
    # 근거 기반 팁 오류는 레거시 앱과 같은 문장을 쓰고,
    assert "Grok CLI" in job_view.error_message("grounded_tips_require_grok_cli")
    # 사전에 없는 원인은 감추지 않고 그대로 붙인다(중괄호가 있어도 깨지지 않는다).
    assert "cli not found {x}" in job_view.error_message("boom: cli not found {x}")
    assert job_view.error_message("") == copy("job_failed")


# ─────────────────────────────────────────────────────────────
# 화면 — 한 줄 프롬프트에서 에디터까지
# ─────────────────────────────────────────────────────────────

async def test_create_opens_with_one_line_prompt_and_refuses_an_empty_topic(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        await user.should_see(marker="create-topic")
        await user.should_see(marker="create-submit")
        await user.should_see("방향 3개 보기")

        with user.client:
            button = next(iter(user.find(marker="create-submit").elements))
        assert button.enabled is False

        user.find(marker="create-topic").type("   ")
        user.find(marker="create-submit").click()
        assert calls == []


async def test_one_topic_line_submits_exactly_one_directions_job(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "dir-9"))
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: _job(job_id, "directions", "queued"),
    )

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="create-topic").type("배포 실수로 배운 것")

        with user.client:
            button = next(iter(user.find(marker="create-submit").elements))
        assert button.enabled is True

        user.find(marker="create-submit").click()
        await user.should_see(marker="direction-job")

        assert len(calls) == 1
        assert calls[0]["kind"] == "directions"
        assert calls[0]["request"]["keywords"] == "배포 실수로 배운 것"
        # 완성 글 요청은 아직 나가지 않았다 — 방향 카드가 먼저다.
        assert "direction" not in calls[0]["request"]


async def test_stored_directions_job_restores_three_cards_without_resubmitting(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: DIRECTIONS_DONE if job_id == "dir-1" else None,
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-card-2")
        await user.should_see("방향 1")
        await user.should_see("훅 3")

        with user.client:
            cards = user.find(marker="direction-card").elements
        assert len(cards) == 3
        await user.should_not_see(marker="direction-card-3")
        # 저장된 결과를 다시 그렸을 뿐, 프로바이더는 한 번도 부르지 않았다.
        assert calls == []


async def test_selecting_a_card_submits_one_post_job_and_opens_the_editor(monkeypatch, tmp_path):
    calls = []
    jobs = {"dir-1": DIRECTIONS_DONE, "post-1": POST_DONE}
    monkeypatch.setattr(editor, "QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr(
        workspace_job_runner, "submit_job", _recording_submitter(calls, "post-1")
    )
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: jobs.get(job_id))

    page = _seeded_page(
        create_input="배포 실수", active_direction_job_id="dir-1", create_mode="builder_note"
    )
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-select-1")

        user.find(marker="direction-select-1").click()

        await user.should_see(marker="editor-text")
        await user.should_see("X 작성 화면 열기")
        await user.should_see(marker="editor-save")
        await user.should_see(marker="editor-published")

        assert len(calls) == 1
        assert calls[0]["kind"] == "post"
        assert calls[0]["request"]["direction"] == DIRECTIONS[1]
        assert calls[0]["request"]["mode"] == "builder_note"
        # 완성 결과는 즉시 초안이 된다.
        assert load_queue(tmp_path / "queue.json")["drafts"][0]["text"] == "완성한 본문"


async def test_grounded_tip_selection_carries_the_facts_options(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(editor, "QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "post-2"))
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: DIRECTIONS_DONE if job_id == "dir-1" else _job(job_id, "post", "running"),
    )

    page = _seeded_page(
        create_input="전세 사기 예방",
        active_direction_job_id="dir-1",
        create_content_type="grounded_tip",
        create_category="finance",
        create_references="https://example.gov/notice",
    )
    async with user_simulation(page) as user:
        await user.open("/")
        # 사실 기반 팁을 고르면 분야 칩과 참고 자료 입력이 함께 보인다.
        await user.should_see(marker="create-category")
        await user.should_see(marker="create-references")

        user.find(marker="direction-select-0").click()
        await user.should_see(marker="post-job")

        request = calls[0]["request"]
        assert request["content_type"] == "grounded_tip"
        assert request["category"] == "finance"
        assert request["references"] == "https://example.gov/notice"


async def test_regular_ideas_never_send_grounded_keys(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(editor, "QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "post-3"))
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: DIRECTIONS_DONE if job_id == "dir-1" else _job(job_id, "post", "running"),
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_not_see(marker="create-category")

        user.find(marker="direction-select-0").click()
        await user.should_see(marker="post-job")

        assert set(calls[0]["request"]) == {"keywords", "direction", "length", "mode"}


async def test_failed_job_waits_for_an_explicit_retry(monkeypatch):
    calls = []
    failed = _job("dir-1", "directions", "failed", error="invalid_directions")
    jobs = {"dir-1": failed}
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "dir-2"))
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: jobs.get(job_id))

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-job-error")
        # 실패한 작업을 화면이 다시 보내지 않는다.
        assert calls == []

        jobs["dir-2"] = _job("dir-2", "directions", "queued")
        user.find(marker="direction-job-retry").click()

        await _wait_until(lambda: len(calls) == 1)
        assert calls[0]["kind"] == "directions"
        assert calls[0]["request"]["keywords"] == "배포 실수"


async def test_running_job_keeps_the_primary_action_disabled(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))
    monkeypatch.setattr(
        workspace_jobs, "get_job", lambda job_id, **kw: _job(job_id, "directions", "running")
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-job-progress")

        with user.client:
            button = next(iter(user.find(marker="create-submit").elements))
        assert button.enabled is False

        user.find(marker="create-submit").click()
        assert calls == []
