"""완성한 포스트를 고치는 에디터 — 자동저장, X 작성 화면, 수동 발행 기록.

여기서 지키는 계약은 두 개다.

1. 사람이 친 글자는 사라지지 않는다. 자동저장은 발행 큐 초안 하나를
   계속 갱신하고, 그 초안이 이미 승인/발행되어 더는 편집할 수 없으면
   content_queue 가 새 초안을 만들어 편집분을 보존한다.
2. 초안 하나가 두 개로 불어나지 않는다. 위 무손실 규칙이 있기 때문에,
   발행을 기록한 뒤에는 에디터가 들고 있던 draft_id 를 반드시 버려야
   한다. 그러지 않으면 뒤늦게 도는 자동저장이 유령 초안을 만든다.

읽기와 쓰기는 한 queue_transaction 안에서 끝낸다 — 앱과 배치 스크립트가
같은 queue.json 을 만지기 때문에, 읽고 나서 따로 쓰면 그 사이의 변경을
조용히 되돌린다.
"""

from __future__ import annotations

import copy as copy_module
from collections.abc import Awaitable, Callable
from pathlib import Path

from nicegui import run, ui

import content_queue
import writing_modes
from grounded_tips import CONTENT_TYPE_GROUNDED_TIP
from utils import generate_tweet_intent_url
from workspace_ui.copy import copy


QUEUE_PATH = content_queue.QUEUE_PATH

# 자동저장 간격. 키 입력마다 파일을 만지지 않으려고 한 번에 모아 쓴다.
AUTOSAVE_SECONDS = 2.0

# 큐 파일 락을 기다리는 시간. launchd 배치(generate_drafts, publish_worker)가
# 같은 flock 을 잡으므로 경합은 정상 상황이고, 기다림은 반드시 워커 스레드
# (run.io_bound)에서 일어나야 한다 — 이벤트 루프에서 기다리면 서버 전체가
# 그동안 멈춘다.
QUEUE_LOCK_TIMEOUT = 10.0

# 화면을 그리는 도중의 첫 저장만은 이벤트 루프 위에서 돈다(렌더러가 동기
# 함수다). 그래서 여기만 짧게 기다리고 포기한다 — 실패해도 본문은
# 스토리지에 있고, 2초 뒤 자동저장이 워커 스레드에서 다시 쓴다.
PAINT_LOCK_TIMEOUT = 0.5

# 워크스페이스 에디터가 만드는 초안의 출처 표시.
SOURCE_KIND = "post"


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 브라우저 없이 테스트된다
# ─────────────────────────────────────────────────────────────

def save_editor_draft(
    draft_id: str | None,
    text: str,
    pillar: str,
    source_job_id: str | None = None,
    *,
    source_kind: str = SOURCE_KIND,
    queue_path: Path | None = None,
    timeout: float = QUEUE_LOCK_TIMEOUT,
) -> dict | None:
    """에디터 본문을 발행 큐 초안으로 저장하고 저장된 초안을 돌려준다.

    None 은 "본문이 비어 있다" 는 뜻뿐이다. draft_id 가 낡았거나 그 초안이
    더는 편집 불가 상태면 옛 레코드를 건드리지 않고 새 초안이 생긴다 —
    호출자는 돌려받은 id 를 다음 저장에 써야 한다.

    락을 잡지 못하면 TimeoutError 가 그대로 올라온다. 조용히 삼키면 사람이
    친 글자가 사라진 줄도 모르게 되므로, 호출자가 알려 주고 다시 시도한다.
    """
    path = QUEUE_PATH if queue_path is None else queue_path
    with content_queue.queue_transaction(path, timeout=timeout) as data:
        draft = content_queue.upsert_workspace_draft(
            data, draft_id, text, pillar, source_job_id, source_kind
        )
        # 트랜잭션이 끝나면 data 는 버려진다 — 복사본을 돌려줘 호출자가
        # 저장되지 않을 변경을 하지 않게 한다.
        return copy_module.deepcopy(draft) if draft is not None else None


def mark_editor_published(
    draft_id: str, *, queue_path: Path | None = None, timeout: float = QUEUE_LOCK_TIMEOUT
) -> dict | None:
    """API 없이 사람이 직접 올린 글을 발행 완료로 기록한다.

    이미 API 로 발행된 글(tweet_id 있음)이나 없는 초안이면 아무것도 하지
    않고 None 을 돌려준다. 락을 못 잡으면 TimeoutError 를 그대로 올린다.
    """
    path = QUEUE_PATH if queue_path is None else queue_path
    with content_queue.queue_transaction(path, timeout=timeout) as data:
        draft = content_queue.mark_manual_published(data, draft_id)
        return copy_module.deepcopy(draft) if draft is not None else None


def x_compose_url(text: str) -> str:
    """X 작성 화면 링크. 레거시 앱의 intent 링크와 같은 모양을 쓴다."""
    return generate_tweet_intent_url(text or "")


def editor_pillar(mode: str, content_type: str) -> str:
    """초안에 붙일 콘텐츠 기둥.

    사실 기반 팁은 어떤 문체로 쓰든 팁이다. 나머지는 글쓰기 모드 카드가
    이미 정해 둔 기둥을 그대로 쓴다(모르는 모드는 curation).
    """
    if content_type == CONTENT_TYPE_GROUNDED_TIP:
        return "tip"
    return writing_modes.pillar_for_mode(mode)


# ─────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────

def render_editor(
    job: dict,
    store,
    *,
    pillar: str,
    on_published: Callable[[], None],
    queue_path: Path | None = None,
) -> None:
    """완성한 포스트 한 편을 고치는 화면을 현재 슬롯에 그린다.

    store 는 서명된 NiceGUI 사용자 스토리지다. 여기에는 본문과 초안 ID 만
    둔다 — 자격 증명은 어떤 경우에도 들어가지 않는다.
    """
    text, on_disk = _restore_or_create_draft(job, store, pillar=pillar, queue_path=queue_path)
    # 마지막으로 파일에 쓴 본문. 바뀌지 않았으면 자동저장이 파일을 만지지 않는다.
    # 복원한 경우에는 파일에 무엇이 있는지 모르므로(자동저장 전에 페이지가
    # 다시 그려졌을 수 있다) None 으로 두어 첫 저장을 반드시 한 번 한다.
    flushed = {"text": on_disk}

    # 락 경합을 한 번 알렸으면 풀릴 때까지 조용히 다시 시도한다 — 2초마다
    # 같은 알림을 쌓지 않기 위해서다.
    warned = {"busy": False}

    async def flush() -> dict | None:
        """바뀐 본문만 파일에 쓴다. 파일 작업은 워커 스레드에서 한다.

        락을 못 잡으면 TimeoutError 를 그대로 올린다. 기준선(flushed)은
        저장이 실제로 끝난 뒤에만 올라가므로, 실패하면 다음 틱이 같은
        본문을 다시 쓴다.
        """
        current = store.get("editor_text") or ""
        if current == flushed["text"]:
            return None
        draft = await run.io_bound(
            save_editor_draft,
            store.get("editor_draft_id"),
            current,
            pillar,
            store.get("editor_job_id"),
            queue_path=queue_path,
        )
        if draft is not None:
            store["editor_draft_id"] = draft["id"]
        flushed["text"] = current
        return draft

    async def autosave() -> None:
        try:
            await flush()
            warned["busy"] = False
        except TimeoutError:
            # 자동저장이 멈춘 걸 사람이 몰라서는 안 된다.
            if not warned["busy"]:
                warned["busy"] = True
                ui.notify(copy("queue_busy"))

    with ui.column().classes("workspace-card w-full").mark("editor"):
        ui.label(copy("editor_title")).classes("text-base font-semibold")

        body = ui.textarea(value=text) \
            .props("autogrow outlined dense") \
            .classes("w-full") \
            .bind_value(store, "editor_text") \
            .mark("editor-text")

        with ui.row().classes("w-full items-center justify-between"):
            count = ui.label(copy("ideas_char_count", n=len(text))) \
                .classes("workspace-hint").mark("editor-count")
            x_link = ui.link(copy("editor_open_x"), x_compose_url(text), new_tab=True) \
                .classes("text-sm").mark("editor-x-link")

        def on_body_change(event) -> None:
            value = event.value or ""
            count.set_text(copy("ideas_char_count", n=len(value)))
            # 링크는 지금 화면의 본문을 그대로 들고 가야 한다. 상태는
            # 건드리지 않는다 — 링크를 여는 것과 발행은 다른 일이다.
            x_link.props(f"href={x_compose_url(value)}")

        body.on_value_change(on_body_change)

        ui.label(copy("editor_hint")).classes("workspace-hint")

        # 어두운 테마의 강조색은 밝아서 흰 글씨가 읽히지 않는다 — 셸의
        # 설정 다이얼로그와 같은 규칙으로 채운 버튼의 대비를 뒤집는다.
        text_color = "white" if store.get("theme") == "light" else "dark"
        with ui.row().classes("w-full items-center gap-2"):
            ui.button(copy("editor_save"), on_click=lambda: _save_now(flush, store)) \
                .props("outline dense").classes("grow").mark("editor-save")
            ui.button(
                copy("editor_mark_published"),
                on_click=lambda: _mark_published(flush, store, queue_path, on_published),
            ).props(f"unelevated dense text-color={text_color}").classes("grow") \
                .mark("editor-published")

        ui.timer(AUTOSAVE_SECONDS, autosave)


def clear_editor_state(store) -> None:
    """에디터가 들고 있던 초안 연결을 끊는다.

    발행을 기록한 뒤에는 반드시 불러야 한다. 남겨 두면 뒤늦은 자동저장이
    편집 불가 초안을 만나 새 초안을 만들어 버린다.
    """
    store["editor_job_id"] = None
    store["editor_draft_id"] = None
    store["editor_text"] = ""


def _restore_or_create_draft(
    job, store, *, pillar: str, queue_path: Path | None
) -> tuple[str, str | None]:
    """완성 결과를 처음 봤으면 즉시 초안으로 저장하고, 아니면 복원한다.

    (화면에 띄울 본문, 파일에 들어 있다고 아는 본문) 을 돌려준다. 복원
    경로에서는 뒤쪽이 None 이다 — 스토리지의 본문이 파일보다 새것일 수
    있으므로 자동저장이 한 번은 반드시 쓰게 만든다.
    """
    job_id = job.get("id")
    if store.get("editor_job_id") == job_id:
        # 이 작업의 본문은 이미 스토리지에 있다. 파일에서 다시 읽지 않는다 —
        # 스토리지 쪽이 더 새것일 수 있다(첫 저장이 실패했거나 자동저장 전에
        # 다시 그려졌을 수 있다).
        return store.get("editor_text") or "", None

    post = (job.get("result") or {}).get("post") or {}
    text = post.get("content") or ""
    try:
        draft = save_editor_draft(
            None, text, pillar, job_id, queue_path=queue_path, timeout=PAINT_LOCK_TIMEOUT
        )
        on_disk = text
    except TimeoutError:
        # 그리는 도중이라 오래 기다릴 수 없다. 본문은 스토리지에 남기고
        # 자동저장(워커 스레드)에 넘긴다.
        ui.notify(copy("queue_busy"))
        draft, on_disk = None, None

    store["editor_job_id"] = job_id
    store["editor_draft_id"] = draft["id"] if draft is not None else None
    store["editor_text"] = text
    return text, on_disk


async def _save_now(flush: Callable[[], Awaitable[dict | None]], store) -> None:
    if not (store.get("editor_text") or "").strip():
        ui.notify(copy("editor_empty"))
        return
    try:
        await flush()
    except TimeoutError:
        ui.notify(copy("queue_busy"))
        return
    ui.notify(copy("editor_saved"))


async def _mark_published(
    flush: Callable[[], Awaitable[dict | None]],
    store,
    queue_path: Path | None,
    on_published: Callable[[], None],
) -> None:
    """게시했음 — 사람이 직접 X 에 올린 글을 발행 기록으로 남긴다."""
    if not (store.get("editor_text") or "").strip():
        ui.notify(copy("editor_empty"))
        return

    try:
        # 먼저 지금 본문을 저장한다. 저장이 새 초안을 만들었다면 그 새 초안을
        # 발행으로 기록해야 화면의 본문과 기록이 어긋나지 않는다.
        draft = await flush()
        draft_id = (draft or {}).get("id") or store.get("editor_draft_id")
        published = await run.io_bound(
            mark_editor_published, draft_id, queue_path=queue_path
        ) if draft_id else None
    except TimeoutError:
        # 기록하지 못했으면 에디터를 그대로 둔다. 여기서 상태를 지우면
        # 발행되지도 않은 글의 초안 연결만 끊긴다.
        ui.notify(copy("queue_busy"))
        return

    ui.notify(copy("editor_published") if published else copy("editor_publish_failed"))
    clear_editor_state(store)
    on_published()
