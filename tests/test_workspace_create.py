"""만들기 영역 — 주제 한 줄 → 방향 3장 → 고른 하나 → 포스트 한 편.

이 영역이 존재하는 이유는 비용이다. 방향 카드는 싸고 완성 글은 비싸다.
그래서 여기 테스트는 "무엇이 보이는가" 만큼이나 "요청이 몇 번 나갔는가"를
못 박는다. 특히 재접속·페이지 재구성은 저장된 작업 ID 를 다시 읽을 뿐,
어떤 경우에도 프로바이더를 다시 부르지 않아야 한다.
"""

from __future__ import annotations

import asyncio
import threading
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
        # 근거 기반 팁을 고르면 분야 칩과 참고 자료 입력이 함께 보인다.
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


async def test_direction_submission_timeout_shows_queue_busy_and_stores_no_job(monkeypatch):
    """submit_job 이 큐 락(10초)을 못 잡으면 TimeoutError 가 올라온다 —
    화면은 그걸 queue_busy 알림으로 보여주고, 실패한 제출이므로 작업
    ID 도 남기지 않는다(재시도가 새 작업이 아니라 유령 상태를 이어받지
    않게 하기 위해서)."""
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("queue lock timeout (10.0s): workspace_jobs.json")

    monkeypatch.setattr(workspace_job_runner, "submit_job", raise_timeout)

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="create-topic").type("배포 실수")
        user.find(marker="create-submit").click()

        await user.should_see(copy("queue_busy"))
        with user.client:
            assert app.storage.user.get("active_direction_job_id") is None


async def test_post_submission_timeout_shows_queue_busy_and_stores_no_job(monkeypatch):
    """방향을 고른 뒤의 완성 글 제출도 같은 큐 락을 잡는다 — 락을 못 잡으면
    같은 queue_busy 알림이 뜨고 active_post_job_id 는 비어 있어야 한다."""
    def raise_timeout(*args, **kwargs):
        raise TimeoutError("queue lock timeout (10.0s): workspace_jobs.json")

    monkeypatch.setattr(workspace_job_runner, "submit_job", raise_timeout)
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: DIRECTIONS_DONE if job_id == "dir-1" else None,
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-select-0")

        user.find(marker="direction-select-0").click()

        await user.should_see(copy("queue_busy"))
        with user.client:
            assert app.storage.user.get("active_post_job_id") is None


async def test_malformed_direction_notifies_invalid_direction_not_topic_required(monkeypatch):
    """submit_selected_direction 이 None 을 돌려주는 이유는 두 가지다 —
    주제가 비었거나 방향 카드가 망가졌거나. 주제는 채워져 있는데 카드의
    한 필드가 비어 normalize_direction 이 걸러낸 경우에는 create_topic_required
    가 아니라 invalid_direction 을 보여줘야 사람이 무엇을 고칠지 안다."""
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))
    broken = _job(
        "dir-1", "directions", "completed",
        result={"directions": [{"title": "A", "hook": "", "angle": "a", "core_message": "m"}]},
    )
    monkeypatch.setattr(
        workspace_jobs, "get_job", lambda job_id, **kw: broken if job_id == "dir-1" else None
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-select-0")

        user.find(marker="direction-select-0").click()

        await user.should_see(copy("invalid_direction"))
        await user.should_not_see(copy("create_topic_required"))
        # 방향이 온전하지 않으므로 완성 글 요청은 나가지 않는다.
        assert calls == []


async def test_double_click_on_directions_submit_sends_exactly_one_job(monkeypatch):
    """버튼을 두 번 연달아 눌러도 방향 카드 요청은 한 번만 나가야 한다.

    run.io_bound 는 실행을 워커 스레드로 옮기지만, NiceGUI 는 async 클릭
    핸들러를 독립된 fire-and-forget 태스크로 스케줄한다 — 그래서 첫 제출이
    아직 큐 락을 쥐고 도는 동안 두 번째 클릭이 만드는 태스크가 시작될 수
    있다. _start_directions 의 submitting["directions"] 가드가 없으면
    프로바이더 작업이 두 번 나가고 하나는 어느 화면에도 걸리지 않는
    유령으로 남는다 — 이 테스트는 그 가드가 실제로 두 번째 제출을 막는지
    확인한다(가드를 지우면 실패해야 한다)."""
    calls = []
    release = threading.Event()

    def slow_submit(kind, request, *, engine="", language="", **kwargs):
        calls.append({"kind": kind, "request": request})
        assert release.wait(timeout=2), "release 이벤트가 제때 오지 않았다"
        return _job("dir-slow", kind, "queued")

    monkeypatch.setattr(workspace_job_runner, "submit_job", slow_submit)
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: _job(job_id, "directions", "queued") if job_id == "dir-slow" else None,
    )

    async with user_simulation(build_workspace) as user:
        await user.open("/")
        user.find(marker="create-topic").type("배포 실수")

        # 두 번 연달아 클릭한다 — 둘 다 아직 실행되지 않은 백그라운드
        # 태스크로만 예약된다(테스트가 뭔가를 await 하기 전까지는 코루틴
        # 바디가 시작조차 하지 않는다).
        user.find(marker="create-submit").click()
        user.find(marker="create-submit").click()

        await _wait_until(lambda: len(calls) >= 1)
        # 가드가 없다면 두 번째 클릭이 만든 태스크도 이 시점까지 워커
        # 스레드에 진입해 calls 에 자기 몫을 남겼을 것이다 — 스레드 풀은
        # 워커가 여럿이라 둘 다 release 를 기다리기 전에 append 부터 한다.
        # 그러니 여기서 잠깐 더 기다려도 안전하게 판정할 수 있다.
        await asyncio.sleep(0.1)
        assert len(calls) == 1

        release.set()
        await user.should_see(marker="direction-job")

        assert len(calls) == 1
        with user.client:
            assert app.storage.user.get("active_direction_job_id") == "dir-slow"


async def test_double_click_on_direction_select_sends_exactly_one_post_job(monkeypatch):
    """방향 카드를 골라 완성 글을 요청할 때도 같은 경쟁이 있다 — 이 테스트는
    _select_direction 의 submitting["post"] 가드를 겨눈다."""
    calls = []
    release = threading.Event()

    def slow_submit(kind, request, *, engine="", language="", **kwargs):
        calls.append({"kind": kind, "request": request})
        assert release.wait(timeout=2), "release 이벤트가 제때 오지 않았다"
        return _job("post-slow", kind, "queued")

    monkeypatch.setattr(workspace_job_runner, "submit_job", slow_submit)
    monkeypatch.setattr(
        workspace_jobs, "get_job",
        lambda job_id, **kw: DIRECTIONS_DONE if job_id == "dir-1" else None,
    )

    page = _seeded_page(create_input="배포 실수", active_direction_job_id="dir-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="direction-select-0")

        user.find(marker="direction-select-0").click()
        user.find(marker="direction-select-0").click()

        await _wait_until(lambda: len(calls) >= 1)
        await asyncio.sleep(0.1)
        assert len(calls) == 1

        release.set()
        await user.should_see(marker="post-job")

        assert len(calls) == 1
        with user.client:
            assert app.storage.user.get("active_post_job_id") == "post-slow"


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


def test_memo_submits_one_memo_job_and_skips_blank():
    from workspace_ui.create import submit_memo

    captured = []
    submitter = lambda kind, request, **kwargs: captured.append((kind, request, kwargs)) or {"id": "m1"}
    assert submit_memo("   ", submitter=submitter) is None
    submit_memo(" 호주전 이김 ", length=80, engine="Grok CLI", language="ko", submitter=submitter)
    assert captured == [("memo", {"memo": "호주전 이김", "length": 80}, {"engine": "Grok CLI", "language": "ko"})]


def test_memo_variant_becomes_an_editor_job_with_its_own_id():
    from workspace_ui.create import memo_variant_job

    job = {"id": "m1", "result": {"posts": [{"content": "첫째"}, {"content": "둘째"}]}}
    chosen = memo_variant_job(job, 1)
    assert chosen["id"] == "m1-1"
    assert chosen["result"]["post"]["content"] == "둘째"
    assert memo_variant_job(job, 5) is None
    assert memo_variant_job(job, None) is None


MEMO_DONE = _job(
    "memo-1", "memo", "completed",
    result={"posts": [{"content": "잠이 안 오네요!!"}, {"content": "17년 만에 8강이라니"}]},
)


async def test_memo_mode_submits_one_memo_job(monkeypatch):
    calls = []
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls, "memo-1"))
    page = _seeded_page(create_content_type="memo")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="create-memo-submit")
        await user.should_see("내 말투로 5개 쓰기")
        user.find(marker="create-topic").type("호주전 이겨서 잠이 안 옴")
        user.find(marker="create-memo-submit").click()
        await _wait_until(lambda: calls)
        assert calls[0]["kind"] == "memo"
        assert calls[0]["request"]["memo"] == "호주전 이겨서 잠이 안 옴"
        assert len(calls) == 1


async def test_picking_a_memo_draft_opens_the_editor(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(editor, "QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr(workspace_job_runner, "submit_job", _recording_submitter(calls))
    monkeypatch.setattr(
        workspace_jobs, "get_job", lambda job_id, **kw: MEMO_DONE if job_id == "memo-1" else None
    )
    page = _seeded_page(create_content_type="memo", active_memo_job_id="memo-1")
    async with user_simulation(page) as user:
        await user.open("/")
        await user.should_see(marker="memo-card-1")
        await user.should_see("17년 만에 8강이라니")

        user.find(marker="memo-select-1").click()
        await user.should_see(marker="editor-text")
        # 결과를 다시 그리고 고르는 동안 프로바이더 요청은 한 번도 나가지 않는다.
        assert calls == []
        assert load_queue(tmp_path / "queue.json")["drafts"][0]["text"] == "17년 만에 8강이라니"
