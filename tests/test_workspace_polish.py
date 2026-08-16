"""다듬기 영역 — 이미 쓴 포스트 원문 → 다듬기 작업 하나 → 공유 에디터.

만들기와 같은 원칙을 지킨다: 재접속·페이지 재구성은 저장된 작업 ID 를 다시
읽을 뿐 프로바이더를 두 번 부르지 않는다. 여기 테스트가 특히 못 박는 것은
두 가지다 — (1) 다듬기의 작업 ID(active_optimize_job_id)는 만들기의 것과
완전히 독립적이어서 하단 탭을 오가도 서로의 작업을 지우지 않는다. (2) 다듬기
결과에서 나온 초안은 source_kind="optimize" 로 남아, 같은 화면을 공유하는
만들기의 "post" 초안과 발행 큐에서 구분된다.
"""

from __future__ import annotations

import asyncio
import time

from nicegui import app
from nicegui.testing import user_simulation

import workspace_job_runner
import workspace_jobs
from content_queue import load_queue
from workspace_ui import create, editor, polish
from workspace_ui.app import build_workspace
from workspace_ui.copy import copy
from workspace_ui.polish import submit_optimization


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


OPTIMIZE_DONE = _job(
    "opt-1", "optimize", "completed",
    result={
        "score": 80,
        "reasons": ["구체적인 숫자가 있다"],
        "suggestions": ["1줄 요약을 추가한다"],
        "optimized_post": "다듬은 문장",
    },
)


def _seeded_page(**seed):
    """스토리지에 값이 이미 있는 상태에서 페이지를 그린다 = 재접속/재구성."""

    def build() -> None:
        app.storage.user.update(seed)
        build_workspace()

    return build


def _recording_submitter(calls: list, job_id: str = "new-opt-job"):
    def submit(kind, request, *, engine="", language="", **kwargs):
        calls.append({"kind": kind, "request": request, "engine": engine, "language": language})
        return _job(job_id, kind, "queued")

    return submit


def _boom(*args, **kwargs):
    raise AssertionError("이 상황에서는 새 작업이 나가면 안 된다")


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
# 순수 헬퍼 — 브라우저 없이 요청의 모양만 본다 (브리핑 Step 1)
# ─────────────────────────────────────────────────────────────

def test_polish_submits_one_durable_optimize_job():
    calls = []
    job = submit_optimization(
        "원문 포스트", language="ko", engine="Claude CLI",
        submitter=lambda kind, request, **kwargs: calls.append((kind, request)) or {"id": "o1"},
    )
    assert job["id"] == "o1"
    assert calls == [("optimize", {"text": "원문 포스트"})]


def test_blank_post_is_not_submitted():
    def must_not_submit(*args, **kwargs):
        raise AssertionError("blank input must not create a job")

    assert submit_optimization("   ", language="ko", engine="Grok CLI", submitter=must_not_submit) is None


def test_optimize_request_strips_surrounding_whitespace():
    calls = []
    submit_optimization(
        "  줄바꿈 있는 원문  \n", language="en", engine="Codex CLI",
        submitter=lambda kind, request, **kwargs: calls.append(request) or {"id": "o2"},
    )
    assert calls == [{"text": "줄바꿈 있는 원문"}]


def test_optimized_text_reads_the_worker_result_key():
    assert polish.optimized_text(OPTIMIZE_DONE) == "다듬은 문장"
    assert polish.optimized_text(None) == ""
    assert polish.optimized_text({"result": {}}) == ""


def test_active_optimize_job_id_is_independent_of_create_keys():
    # 브리핑의 명시적 요구: 하단 탭을 오가도 서로의 작업이 지워지지 않도록
    # 만들기와 다듬기는 서로 다른 작업 ID 스토리지 키를 쓴다.
    assert "active_optimize_job_id" not in create.STORAGE_DEFAULTS
    assert "active_post_job_id" not in polish.STORAGE_DEFAULTS
    assert "active_direction_job_id" not in polish.STORAGE_DEFAULTS
    assert polish.STORAGE_DEFAULTS["active_optimize_job_id"] is None


# ─────────────────────────────────────────────────────────────
# 화면 — 원문 붙여넣기부터 공유 에디터까지
# ─────────────────────────────────────────────────────────────

async def test_polish_opens_with_a_blank_input_and_refuses_blank_text(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()
        await user.should_see(marker="polish-input")
        await user.should_see(marker="polish-submit")

        with user.client:
            button = next(iter(user.find(marker="polish-submit").elements))
        assert button.enabled is False

        user.find(marker="polish-input").type("   ")
        user.find(marker="polish-submit").click()
        assert calls == []


async def test_submitting_valid_text_shows_exactly_one_queued_status(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "opt-9"))
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: _job(job_id, "optimize", "running"),
    )

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()

        user.find(marker="polish-input").type("원문 포스트")
        with user.client:
            button = next(iter(user.find(marker="polish-submit").elements))
        assert button.enabled is True

        user.find(marker="polish-submit").click()
        await user.should_see(marker="optimize-job-progress")

        assert len(calls) == 1
        assert calls[0]["kind"] == "optimize"
        assert calls[0]["request"] == {"text": "원문 포스트"}

        # 아직 도는 작업이 있으면 제출 버튼은 다시 눌러도 반응하지 않는다.
        user.find(marker="polish-submit").click()
        assert len(calls) == 1


async def test_optimize_submission_timeout_shows_queue_busy_and_stores_no_job(monkeypatch):
    """다듬기 제출도 만들기와 같은 큐 락(10초)을 잡는다 — 락을 못 잡으면
    같은 queue_busy 알림이 뜨고 active_optimize_job_id 는 비어 있어야
    한다(유령 상태로 재시도를 오염시키지 않기 위해서)."""
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("queue lock timeout (10.0s): workspace_jobs.json")

    monkeypatch.setattr(workspace_job_runner, "submit_job", raise_timeout)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()
        user.find(marker="polish-input").type("원문 포스트")
        user.find(marker="polish-submit").click()

        await user.should_see(copy("queue_busy"))
        with user.client:
            assert app.storage.user.get("active_optimize_job_id") is None


async def test_completed_job_restores_without_resubmitting_and_shows_the_optimized_post(monkeypatch):
    monkeypatch.setattr(workspace_job_runner, "submit_job", _boom)
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: OPTIMIZE_DONE if job_id == "opt-1" else None,
    )

    page = _seeded_page(active_optimize_job_id="opt-1")
    async with user_simulation(page) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()

        await user.should_see(marker="optimize-result")
        await user.should_see("다듬은 문장")
        await user.should_see(marker="optimize-open-editor")
        # 에디터는 아직 열지 않았다 — 버튼을 눌러야 열린다.
        await user.should_not_see(marker="editor-text")


async def test_opening_the_editor_creates_its_own_draft_tagged_as_optimize(monkeypatch, tmp_path):
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(workspace_job_runner, "submit_job", _boom)
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: OPTIMIZE_DONE if job_id == "opt-1" else None,
    )

    page = _seeded_page(active_optimize_job_id="opt-1")
    async with user_simulation(page) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()
        await user.should_see(marker="optimize-open-editor")

        user.find(marker="optimize-open-editor").click()

        await user.should_see(marker="editor-text")
        await user.should_see("다듬은 문장")
        await user.should_see(marker="editor-save")
        await user.should_see(marker="editor-published")

        drafts = load_queue(queue_path)["drafts"]
        assert len(drafts) == 1
        assert drafts[0]["text"] == "다듬은 문장"
        assert drafts[0]["source_job_id"] == "opt-1"
        assert drafts[0]["source_kind"] == "optimize"


async def test_optimize_and_create_editors_keep_independent_drafts_through_later_autosave(
    monkeypatch, tmp_path
):
    """만들기 탭이 자동으로 여는 에디터와 다듬기 탭이 여는 에디터가 같은 화면
    안에 함께 살아 있어도, 서로 다른 스토리지 키를 쓰므로 각자의 초안을
    절대 밟지 않는다.

    이 테스트는 리뷰에서 재현된 사고를 그대로 되짚는다: 두 에디터가
    editor_job_id/editor_draft_id/editor_text 를 공유하던 시절에는, 다듬기
    에디터를 나중에 열면 그 공유 키가 다듬기 작업으로 넘어가 버렸다. 그
    상태에서 만들기 쪽 본문이 바뀌어 만들기의 자동저장 타이머가 돌면(둘 다
    ui.tab_panels 가 페이지를 열 때 이미 만들어 둔 채로 계속 돈다), 만들기의
    pillar 와 source_kind="post" 로 다듬기 초안 파일을 덮어써 버렸다. 첫
    렌더 직후 상태만 보던 예전 검증은 이 사고를 놓쳤다 — 그래서 여기서는
    다듬기 에디터를 연 "뒤에" 만들기 쪽 본문을 고치고 자동저장이 돌 때까지
    기다린 다음, 두 초안이 각자의 값을 그대로 지키는지까지 확인한다.
    """
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", queue_path)
    monkeypatch.setattr(editor, "AUTOSAVE_SECONDS", 0.05)
    monkeypatch.setattr(workspace_job_runner, "submit_job", _boom)
    jobs = {
        "post-1": _job("post-1", "post", "completed", result={"post": {"content": "포스트 초안"}}),
        "opt-1": OPTIMIZE_DONE,
    }
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: jobs.get(job_id))

    page = _seeded_page(
        active_post_job_id="post-1", active_optimize_job_id="opt-1", create_mode="builder_note"
    )
    async with user_simulation(page) as user:
        await user.open("/")
        # 만들기 탭은 완성 글이 있으면 곧바로 에디터를 연다(Task 6 동작).
        await user.should_see(marker="editor-text")
        assert load_queue(queue_path)["drafts"][0]["source_kind"] == "post"

        user.find(marker="nav-polish").click()
        await user.should_see(marker="optimize-open-editor")
        user.find(marker="optimize-open-editor").click()
        await user.should_see("다듬은 문장")

        drafts = load_queue(queue_path)["drafts"]
        assert len(drafts) == 2
        by_kind = {d["source_kind"]: d for d in drafts}
        assert by_kind["post"]["text"] == "포스트 초안"
        assert by_kind["optimize"]["text"] == "다듬은 문장"
        assert by_kind["optimize"]["source_job_id"] == "opt-1"

        # 만들기 탭으로 돌아가 본문을 고친다. 실제 조작은 만들기 텍스트
        # 영역에 타이핑하는 것이지만, 만들기의 자동저장은 스토리지 값만
        # 읽으므로 여기서는 그 값을 직접 바꿔 같은 효과를 낸다 — 두 에디터가
        # 화면에 동시에 살아 있는 상태에서 "만들기 쪽 값이 바뀌었을 때"를
        # 정확히 겨눈 확인이다.
        user.find(marker="nav-create").click()
        with user.client:
            app.storage.user["editor_text"] = "포스트 초안을 고쳤다"

        def _create_draft_text() -> str | None:
            by_kind = {d["source_kind"]: d for d in load_queue(queue_path)["drafts"]}
            return by_kind.get("post", {}).get("text")

        await _wait_until(lambda: _create_draft_text() == "포스트 초안을 고쳤다")

        drafts_after = {d["source_kind"]: d for d in load_queue(queue_path)["drafts"]}
        assert len(load_queue(queue_path)["drafts"]) == 2
        assert drafts_after["post"]["text"] == "포스트 초안을 고쳤다"
        assert drafts_after["post"]["source_job_id"] == "post-1"
        assert drafts_after["post"]["source_kind"] == "post"
        # 다듬기 초안은 전혀 손대지 않았다 — 본문도, 출처도, 기둥이 남긴
        # 흔적도 그대로다.
        assert drafts_after["optimize"]["text"] == "다듬은 문장"
        assert drafts_after["optimize"]["source_kind"] == "optimize"
        assert drafts_after["optimize"]["source_job_id"] == "opt-1"


async def test_failed_optimize_job_waits_for_an_explicit_retry(monkeypatch):
    calls = []
    jobs = {"opt-1": _job("opt-1", "optimize", "failed", error="job_failed")}
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "opt-2"))
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: jobs.get(job_id))

    page = _seeded_page(polish_input="원문 포스트", active_optimize_job_id="opt-1")
    async with user_simulation(page) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()
        await user.should_see(marker="optimize-job-error")
        assert calls == []

        jobs["opt-2"] = _job("opt-2", "optimize", "queued")
        user.find(marker="optimize-job-retry").click()

        await _wait_until(lambda: len(calls) == 1)
        assert calls[0]["kind"] == "optimize"
        assert calls[0]["request"] == {"text": "원문 포스트"}


async def test_new_submission_closes_the_open_editor_without_touching_the_old_draft(monkeypatch, tmp_path):
    """다듬기 결과의 에디터를 이미 연 상태에서 새 원문을 다시 보내면, 화면은
    새 작업의 진행 상태로 넘어가고 옛 초안은 발행 큐에 그대로 남는다 —
    뒤늦은 자동저장이 옛 초안을 새 결과로 덮어쓰지 않는다는 뜻이다."""
    queue_path = tmp_path / "queue.json"
    monkeypatch.setattr(editor, "QUEUE_PATH", queue_path)
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "opt-2"))
    jobs = {
        "opt-1": OPTIMIZE_DONE,
        "opt-2": _job("opt-2", "optimize", "queued"),
    }
    monkeypatch.setattr(workspace_jobs, "get_job", lambda job_id, **kw: jobs.get(job_id))

    page = _seeded_page(active_optimize_job_id="opt-1")
    async with user_simulation(page) as user:
        await user.open("/")
        user.find(marker="nav-polish").click()
        await user.should_see(marker="optimize-open-editor")
        user.find(marker="optimize-open-editor").click()
        await user.should_see(marker="editor-text")

        drafts = load_queue(queue_path)["drafts"]
        assert len(drafts) == 1 and drafts[0]["text"] == "다듬은 문장"

        user.find(marker="polish-input").type("새 원문")
        user.find(marker="polish-submit").click()

        await user.should_see(marker="optimize-job-progress")
        await user.should_not_see(marker="editor-text")

        assert calls[0]["request"] == {"text": "새 원문"}
        # 새 작업을 보내는 것만으로 옛 초안이 바뀌거나 사라지지 않는다.
        drafts = load_queue(queue_path)["drafts"]
        assert len(drafts) == 1 and drafts[0]["text"] == "다듬은 문장"
