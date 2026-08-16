"""발행 — 만들기·다듬기가 채운 발행 큐를 필터로 나눠 보여주고, 초안을 다음
슬롯에 예약하고, 지나간 글 하나를 새 편집 가능한 초안으로 되살린다.

이 화면은 새 데이터를 만들지 않는다. content_queue 하나가 유일한 출처이고,
여기서는 그 위에 필터(PUBLISH_FILTERS)와 두 조작(예약·재사용)만 얹는다.
프로바이더를 부르지 않으므로 job_view/workspace_jobs 는 쓰지 않는다 —
만들기·다듬기와 다른 지점이다.

큐를 만지는 모든 자리는 만들기·다듬기·에디터와 같은 규칙을 따른다: 순수
헬퍼(load_publish_items/schedule_draft/reuse_history_item)는 동기 함수라
테스트가 직접 부르고, 화면 쪽 호출은 예외 없이 run.io_bound 로 감싼다 —
읽기든 쓰기든 마찬가지다. 읽기 자체는 flock 을 잡지 않지만(load_queue 는
잠그지 않는다), 그 판단을 화면 코드가 매번 다시 하게 두는 대신 세 헬퍼
전부를 똑같이 다룬다 — Task 6 이 못 박은 "이벤트 루프에서는 큐를 만지지
않는다" 는 규칙을 예외 없이 지키는 편이 나중에 헷갈리지 않는다.

재사용(reuse_history_item)이 만든 새 초안은 공유 에디터(workspace_ui.editor)
로 연다. 에디터의 계약은 "완성된 작업 하나를 연다"(render_editor(job, ...))
는 것뿐이라, job 이 없는 이 경로에서는 진짜 작업 대신 이 화면이 만든
가짜 job id 하나(f"publish-reuse:{원본 초안 id}")를 쓴다. 에디터의 복원
분기(_restore_or_create_draft)는 "store 에 이미 같은 job_id 가 있으면 그
초안을 그대로 잇는다" 는 조건만 본다 — 그래서 이 화면이 세 스토리지 키
(job_id/draft_id/text)를 미리 채워 두면 에디터는 새 초안을 만들지 않고
방금 만든 복제본을 그대로 편집한다. editor.py 는 고치지 않았다: 기존
계약 안에서 이미 표현할 수 있었다. 에디터 세 키는 이 화면만의 접두어
(key_prefix="publish_")를 쓴다 — 만들기(접두어 없음)·다듬기("optimize_")
와 함께 ui.tab_panels 안에서 세 렌더 함수가 동시에 도는 한, 접두어가
겹치면 세 에디터가 같은 초안을 가리키게 된다(editor.editor_storage_keys
문서 참고).

재사용 에디터에는 명시적 탈출구(publish-editor-back)가 있다. 잘못 눌러
들어와도, 발행을 기록하지 않고 목록으로 돌아갈 수 있다 — 복제본은 이미
"draft" 상태로 큐에 들어가 있으므로 나가도 잃는 것이 없다.
"""

from __future__ import annotations

import copy as copy_module
from collections.abc import Awaitable, Callable
from pathlib import Path

from nicegui import app, background_tasks, run, ui

import content_queue
from workspace_ui import editor
from workspace_ui.copy import copy


QUEUE_PATH = content_queue.QUEUE_PATH

# 브리핑이 못 박은 그대로. 예약(scheduled)은 승인 대기(approved)와 발행
# 시도 중(publishing)을 함께 묶고, 실패(failed)는 재시도 가능한 오류(error)
# 와 다시 슬롯으로 돌아가지 않는 반려(rejected)를 함께 묶는다.
PUBLISH_FILTERS: dict[str, set[str]] = {
    "draft": {"draft"},
    "scheduled": {"approved", "publishing"},
    "failed": {"error", "rejected"},
    "published": {"published"},
}

FILTER_ORDER = ("draft", "scheduled", "failed", "published")

# 큐 락을 물고 있는 상태(publish_worker 가 클레임한 초안) — legacy
# tabs/tab_publish_queue.py 의 _is_claim_locked 와 같은 규칙: 읽기 전용으로만
# 보여준다.
_LOCKED_STATUS = "publishing"

PILLAR_LABEL_KEYS = {
    "build_in_public": "publish_pillar_build_in_public",
    "retrospective": "publish_pillar_retrospective",
    "tip": "publish_pillar_tip",
    "curation": "publish_pillar_curation",
}

# 재사용이 만든 초안의 출처 표시. 만들기의 "post", 다듬기의 "optimize" 와
# 나란한 세 번째 값이다 — 발행 큐에서 "과거 글을 다시 쓴 것" 임을 구분한다.
SOURCE_KIND = "reuse"

# 이 화면의 에디터가 쓰는 스토리지 키 접두어. 만들기(접두어 없음)·다듬기
# ("optimize_") 와 완전히 분리된 job_id/draft_id/text 세 키를 만든다.
EDITOR_KEY_PREFIX = "publish_"
_EDITOR_KEYS = editor.editor_storage_keys(EDITOR_KEY_PREFIX)

STORAGE_DEFAULTS = {
    "publish_filter": FILTER_ORDER[0],
    # 히스토리 카드 중 "자세히 보기" 로 펼쳐 둔 것들. {draft_id: True} 모양만
    # 쓴다 — 없는 키는 접힌 것과 같다.
    "publish_open_ids": {},
    "publish_reuse_pillar": "curation",
    _EDITOR_KEYS.job_id: None,
    _EDITOR_KEYS.draft_id: None,
    _EDITOR_KEYS.text: "",
}


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 브라우저 없이 큐 파일만으로 테스트된다
# ─────────────────────────────────────────────────────────────

def load_publish_items(filter_name: str, *, queue_path: Path | None = None) -> list[dict]:
    """필터 하나에 해당하는 초안만 순서대로 돌려준다. 모르는 필터 이름은
    빈 목록이다 — 화면이 잘못된 탭을 그리다 죽는 대신 아무것도 보여주지
    않는 쪽을 고른다."""
    statuses = PUBLISH_FILTERS.get(filter_name)
    if not statuses:
        return []
    path = QUEUE_PATH if queue_path is None else queue_path
    data = content_queue.load_queue(path)
    return content_queue.drafts_for_statuses(data, statuses)


def schedule_draft(draft_id: str, *, queue_path: Path | None = None) -> dict | None:
    """초안을 승인해 다음 빈 슬롯에 넣는다. X 는 절대 부르지 않는다 — 실제
    발행은 scripts/publish_worker.py 배치의 몫이고, 여기서는 승인만 한다
    (기존 approve_draft 를 그대로 부른다).

    draft_id 가 없거나 큐에서 사라졌으면 아무것도 바꾸지 않고 None."""
    path = QUEUE_PATH if queue_path is None else queue_path
    with content_queue.queue_transaction(path) as data:
        draft = content_queue.approve_draft(data, draft_id)
        return copy_module.deepcopy(draft) if draft is not None else None


def reuse_history_item(draft_id: str, *, queue_path: Path | None = None) -> dict | None:
    """히스토리(발행됐거나 반려된) 글 하나를 새 편집 가능한 초안으로
    복제한다. 원본은 절대 건드리지 않는다 — content_queue.duplicate_draft
    의 계약을 그대로 물려받는다."""
    path = QUEUE_PATH if queue_path is None else queue_path
    with content_queue.queue_transaction(path) as data:
        copied = content_queue.duplicate_draft(data, draft_id)
        return copy_module.deepcopy(copied) if copied is not None else None


def preview_text(text: str, limit: int = 80) -> str:
    """히스토리 카드가 접혀 있을 때 보여줄 만큼만 자른다."""
    body = (text or "").strip()
    if len(body) <= limit:
        return body
    return body[:limit].rstrip() + "…"


def format_timestamp(value: str | None) -> str:
    """ISO 타임스탬프를 "YYYY-MM-DD HH:MM" 만 남겨 화면에 짧게 보여준다."""
    if not value:
        return ""
    return value.replace("T", " ")[:16]


def x_status_url(tweet_id: str) -> str:
    """API 로 발행된 글의 검증된 X 링크. tweet_id 가 있을 때만 만든다."""
    return f"https://x.com/i/status/{tweet_id}"


# ─────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────

def render_publish() -> None:
    """발행 영역. workspace_ui.app 의 AREA_RENDERERS 가 부른다."""
    store = _init_storage()

    ui.label(copy("nav_publish")).classes("workspace-area-title")
    ui.label(copy("publish_hint")).classes("workspace-hint")

    area = ui.column().classes("w-full gap-4")
    # token 은 "이 reload() 호출이 아직 가장 최신인가" 를 검사한다 — 빠른
    # 필터 전환으로 두 reload() 가 겹치면 완료 순서가 뒤집힐 수 있어서다
    # (리뷰에서 지적된 경합: 느린 응답이 나중에 도착해 최신 필터 화면을
    # 옛 필터의 항목으로 덮어쓰면, 그 항목이 지금 필터의 규칙으로 그려진다
    # — 예를 들어 반려 초안이 "초안" 탭의 규칙을 입고 예약 버튼을 받는다).
    state: dict = {"items": None, "token": 0}

    def repaint() -> None:
        area.clear()
        with area:
            _render_area(store, state, repaint, reload)

    async def reload() -> None:
        state["token"] += 1
        token = state["token"]
        requested = _normalize_filter(store.get("publish_filter"))

        if state["items"] is not None:
            # 이미 뭔가 그려져 있었다면 로딩 상태로 되돌린다 — 필터를 바꾸거나
            # 예약·재사용 직후에도 옛 목록이 잠깐 남아 있지 않게 한다. 맨 첫
            # 로드는 render_publish() 가 이미 로딩 상태를 그려 뒀으므로 여기서
            # 또 그리지 않는다(중복 페인트를 피한다).
            state["items"] = None
            repaint()

        items = await run.io_bound(load_publish_items, requested, queue_path=QUEUE_PATH)

        if token != state["token"] or requested != _normalize_filter(store.get("publish_filter")):
            # 더 최신 reload() 가 이미 시작됐거나, 그 사이에 필터가 다시
            # 바뀌었다 — 이 결과는 낡았으니 버린다. 지금 필터를 위한 요청은
            # 이미 따로 돌고 있으므로(또는 곧 돌 것이므로) 화면은 결국 맞는
            # 상태로 그려진다.
            return

        state["items"] = items
        repaint()

    repaint()
    if not store.get(_EDITOR_KEYS.job_id):
        # 재접속 시 이미 재사용 에디터가 열려 있으면 _render_area 가 곧장
        # 그 화면으로 빠지고 목록(state["items"])은 전혀 쓰지 않는다 —
        # 그런 경우에 목록을 미리 불러오는 것은 헛일이다.
        background_tasks.create(reload(), name="publish-initial-load")


def _render_area(
    store, state: dict, repaint: Callable[[], None], reload: Callable[[], Awaitable[None]]
) -> None:
    if store.get(_EDITOR_KEYS.job_id):
        _render_reuse_editor(store, repaint, reload)
        return

    _render_filter_tabs(store, reload)

    items = state.get("items")
    if items is None:
        with ui.row().classes("items-center gap-2").mark("publish-loading"):
            ui.spinner(size="sm")
            ui.label(copy("publish_loading")).classes("workspace-hint")
        return

    filter_name = _normalize_filter(store.get("publish_filter"))
    if not items:
        ui.label(copy(f"publish_empty_{filter_name}")) \
            .classes("workspace-hint").mark("publish-empty")
        return

    for draft in items:
        _render_card(draft, filter_name, store, repaint, reload)


def _render_filter_tabs(store, reload: Callable[[], Awaitable[None]]) -> None:
    async def on_change(event) -> None:
        store["publish_filter"] = _normalize_filter(event.value)
        await reload()

    with ui.tabs(value=_normalize_filter(store.get("publish_filter"))) \
            .classes("w-full workspace-tabs").mark("publish-filters") as tabs:
        for name in FILTER_ORDER:
            ui.tab(name, label=copy(f"publish_filter_{name}")).mark(f"publish-filter-{name}")
    tabs.on_value_change(on_change)


def _render_card(
    draft: dict,
    filter_name: str,
    store,
    repaint: Callable[[], None],
    reload: Callable[[], Awaitable[None]],
) -> None:
    draft_id = draft["id"]
    pillar_key = PILLAR_LABEL_KEYS.get(draft.get("pillar"), "publish_pillar_curation")

    with ui.column().classes("workspace-card w-full gap-1") \
            .mark("publish-card", f"publish-card-{draft_id}"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(copy(pillar_key)).classes("text-sm font-semibold")
            note = _status_note(draft, filter_name)
            if note:
                ui.label(note).classes("workspace-hint")

        if filter_name == "scheduled" and draft.get("slot"):
            ui.label(f'{copy("publish_slot_label")} · {format_timestamp(draft["slot"])}') \
                .classes("workspace-hint")
        if filter_name == "published" and draft.get("published_at"):
            ui.label(
                f'{copy("publish_published_at_label")} · {format_timestamp(draft["published_at"])}'
            ).classes("workspace-hint")

        if filter_name in ("failed", "published"):
            _render_history_body(draft, filter_name, store, repaint)
        else:
            ui.label(draft.get("text", "")).classes("text-sm whitespace-pre-wrap") \
                .mark(f"publish-text-{draft_id}")
            timestamp = draft.get("updated_at") or draft.get("created_at")
            if timestamp:
                ui.label(f'{copy("publish_created_at_label")} · {format_timestamp(timestamp)}') \
                    .classes("workspace-hint")

        # status 를 filter_name 과 함께 다시 확인한다(방어적 이중 검사) —
        # 정상적으로는 load_publish_items 가 이미 필터에 맞는 상태만
        # 돌려주지만, 예약 버튼은 반려 초안이 슬롯 큐로 돌아가면 안 되는
        # 안전 불변식과 직결되므로 여기서도 한 번 더 못 박는다.
        if filter_name == "draft" and draft.get("status") == "draft":
            ui.button(
                copy("publish_schedule_cta"),
                on_click=lambda: _schedule(draft_id, reload),
            ).props("unelevated dense").classes("w-full").mark(f"publish-schedule-{draft_id}")
        elif filter_name == "failed" and draft.get("status") == "error":
            # legacy tabs/tab_publish_queue.py 의 _can_approve 와 같은 비대칭:
            # error 만 재예약할 수 있고 rejected 는 절대 슬롯 큐로 돌아가지
            # 않는다.
            ui.button(
                copy("publish_retry_cta"),
                on_click=lambda: _schedule(draft_id, reload),
            ).props("unelevated dense").classes("w-full").mark(f"publish-retry-{draft_id}")


def _render_history_body(draft: dict, filter_name: str, store, repaint: Callable[[], None]) -> None:
    """실패·발행 카드의 몸통. 접혀 있으면 미리보기만, 펼치면 전체 본문과
    (발행된 글이면) X 링크, 그리고 재사용 버튼까지 보여준다."""
    draft_id = draft["id"]
    open_ids = store.get("publish_open_ids") or {}
    is_open = bool(open_ids.get(draft_id))

    ui.label(preview_text(draft.get("text", ""))).classes("text-sm whitespace-pre-wrap")

    ui.button(
        copy("publish_hide_details") if is_open else copy("publish_view_details"),
        on_click=lambda: _toggle_open(draft_id, store, repaint),
    ).props("flat dense").mark(f"publish-open-{draft_id}")

    if not is_open:
        return

    with ui.column().classes("w-full gap-2").mark(f"publish-detail-{draft_id}"):
        ui.label(draft.get("text", "")).classes("text-sm whitespace-pre-wrap") \
            .mark(f"publish-text-{draft_id}")

        tweet_id = draft.get("tweet_id")
        if filter_name == "published" and tweet_id:
            ui.link(copy("publish_view_on_x"), x_status_url(tweet_id), new_tab=True) \
                .classes("text-sm").mark(f"publish-x-link-{draft_id}")

        ui.button(
            copy("publish_reuse_cta"),
            on_click=lambda: _reuse(draft_id, store, repaint),
        ).props("outline dense").classes("w-full").mark(f"publish-reuse-{draft_id}")


def _render_reuse_editor(
    store, repaint: Callable[[], None], reload: Callable[[], Awaitable[None]]
) -> None:
    # 되돌아갈 길이 있어야 한다 — 잘못 눌러 재사용 에디터에 들어와도, 빈
    # 본문으로는 발행이 막히고(editor_empty) on_published 는 실제로 발행을
    # 기록해야만 불린다. 목록으로 돌아가는 명시적 탈출구를 둔다.
    ui.button(
        copy("publish_editor_back"),
        on_click=lambda: _cancel_reuse_editor(store, repaint, reload),
    ).props("flat dense").mark("publish-editor-back")

    job = {"id": store[_EDITOR_KEYS.job_id]}
    pillar = store.get("publish_reuse_pillar") or "curation"
    editor.render_editor(
        job, store,
        pillar=pillar,
        on_published=lambda: _close_reuse_editor(store, repaint, reload),
        queue_path=QUEUE_PATH,
        source_kind=SOURCE_KIND,
        key_prefix=EDITOR_KEY_PREFIX,
    )


# ─────────────────────────────────────────────────────────────
# 행동
# ─────────────────────────────────────────────────────────────

async def _schedule(draft_id: str, reload: Callable[[], Awaitable[None]]) -> None:
    try:
        result = await run.io_bound(schedule_draft, draft_id, queue_path=QUEUE_PATH)
    except TimeoutError:
        ui.notify(copy("queue_busy"))
        return
    if result is not None:
        ui.notify(copy("publish_scheduled_notice"))
    await reload()


async def _reuse(draft_id: str, store, repaint: Callable[[], None]) -> None:
    try:
        copied = await run.io_bound(reuse_history_item, draft_id, queue_path=QUEUE_PATH)
    except TimeoutError:
        ui.notify(copy("queue_busy"))
        return
    if copied is None:
        return

    keys = _EDITOR_KEYS
    # source_job_id 자리에 원본(재사용 대상) 초안의 id 를 남긴다 — 진짜
    # job 은 없지만, "이 초안이 어떤 과거 글에서 복제됐는가" 는 유용한
    # 흔적이라 그냥 버리지 않는다(content_queue.py 의 필드 문서에 이
    # 합성 값을 명시해 뒀다).
    store[keys.job_id] = _reuse_job_id(draft_id)
    store[keys.draft_id] = copied["id"]
    store[keys.text] = copied.get("text") or ""
    store["publish_reuse_pillar"] = copied.get("pillar") or "curation"
    ui.notify(copy("publish_reuse_done"))
    repaint()


def _close_reuse_editor(
    store, repaint: Callable[[], None], reload: Callable[[], Awaitable[None]]
) -> None:
    editor.clear_editor_state(store, key_prefix=EDITOR_KEY_PREFIX)
    repaint()
    # 발행을 기록한 뒤 필터 카드로 돌아간다 — 지금 보고 있던 필터가
    # "발행됨" 이었다면 방금 기록한 글이 바로 보여야 한다.
    background_tasks.create(reload(), name="publish-reload-after-publish")


def _cancel_reuse_editor(
    store, repaint: Callable[[], None], reload: Callable[[], Awaitable[None]]
) -> None:
    """재사용 에디터에서 그냥 나간다 — 발행을 기록하지 않는다.

    복제본은 이미 큐에 초안 상태로 들어가 있으니 잃는 것이 없다: 목록으로
    돌아가면 초안 필터에서 그대로 보이고, 나중에 다시 열어 이어 고칠 수
    있다."""
    editor.clear_editor_state(store, key_prefix=EDITOR_KEY_PREFIX)
    repaint()
    background_tasks.create(reload(), name="publish-reload-after-cancel")


def _toggle_open(draft_id: str, store, repaint: Callable[[], None]) -> None:
    open_ids = dict(store.get("publish_open_ids") or {})
    open_ids[draft_id] = not open_ids.get(draft_id, False)
    store["publish_open_ids"] = open_ids
    repaint()


def _reuse_job_id(source_draft_id: str) -> str:
    """복제 대상(원본) 초안 id 로 만드는 가짜 job id. 진짜 작업이 아니므로
    workspace_jobs 가 만드는 id 와 절대 겹치지 않을 접두어를 쓴다 — 그리고
    복제본이 아니라 원본을 가리켜, 자동저장이 source_job_id 로 이 값을
    남길 때 "어디서 복제됐는지" 를 알 수 있게 한다."""
    return f"publish-reuse:{source_draft_id}"


def _status_note(draft: dict, filter_name: str) -> str | None:
    status = draft.get("status")
    if filter_name == "scheduled":
        return copy(
            "publish_status_publishing" if status == _LOCKED_STATUS
            else "publish_status_approved"
        )
    if filter_name == "failed":
        return copy("publish_status_error" if status == "error" else "publish_status_rejected")
    if filter_name == "published":
        return copy("publish_status_manual" if draft.get("manual_published") else "publish_status_api")
    return None


def _normalize_filter(value: object) -> str:
    return value if value in PUBLISH_FILTERS else FILTER_ORDER[0]  # type: ignore[return-value]


def _init_storage():
    store = app.storage.user
    for key, value in STORAGE_DEFAULTS.items():
        store.setdefault(key, value)
    return store
