"""만들기 — 주제 한 줄에서 완성한 포스트 한 편까지.

흐름을 이렇게 쪼갠 이유는 돈과 시간이다. 방향 카드 3장은 조사도 글쓰기도
하지 않아 싸고 빠르다. 완성 글은 비싸다. 그래서 사람이 카드 하나를 고른
뒤에야 완성 글 요청이 한 번 나간다. 사실 기반 팁도 마찬가지다 — 조사는
선택 이후 워커가 한다(카드 단계에서는 아무것도 검색하지 않는다).

브라우저는 요청 결과를 들고 있지 않는다. 작업 ID 만 서명된 사용자
스토리지에 두고, 화면은 저장소에서 상태를 다시 읽어 그린다. 그래서
재접속하거나 페이지가 다시 그려져도 프로바이더 요청이 두 번 나가지
않는다. 자동 재시도는 어디에도 없다.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import app, ui

import workspace_job_runner
import writing_modes
from grounded_tips import CONTENT_TYPE_GROUNDED_TIP, CONTENT_TYPE_IDEAS, TIP_CATEGORIES
from workspace_ui import editor, job_view
from workspace_ui.copy import copy


# 방향 카드가 들고 다니는 전부. grok_client 의 정규화와 같은 네 필드다 —
# 화면과 요청 어디에도 이 밖의 값을 흘려보내지 않는다.
DIRECTION_FIELDS = ("title", "hook", "angle", "core_message")

DEFAULT_MODE = writing_modes.AUTO_MIX
DEFAULT_LANGUAGE = "ko"

# 0 = 자동. 모바일에서 슬라이더를 미는 대신 몇 개만 고르게 한다.
LENGTH_OPTIONS = (0, 200, 280, 500, 800)

# 이 영역이 쓰는 사용자 스토리지. 새어 나가도 무해한 값만 둔다.
STORAGE_DEFAULTS = {
    "create_content_type": CONTENT_TYPE_IDEAS,
    "create_category": TIP_CATEGORIES[0],
    "create_references": "",
    "create_length": 0,
    "create_mode": DEFAULT_MODE,
    "create_direction": None,
    "active_direction_job_id": None,
    "active_post_job_id": None,
    "editor_job_id": None,
    "editor_draft_id": None,
    "editor_text": "",
}


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 브라우저 없이 요청의 모양을 검사할 수 있다
# ─────────────────────────────────────────────────────────────

def filled_button_props(theme_name: str) -> str:
    """채운 버튼의 props. 어두운 테마의 강조색은 밝아서 흰 글씨가 읽히지
    않는다 — 설정 다이얼로그와 같은 규칙으로 대비를 뒤집는다."""
    return f"unelevated text-color={'white' if theme_name == 'light' else 'dark'}"


def normalize_direction(direction: object) -> dict | None:
    """방향 카드에서 네 필드만 남긴다. 하나라도 비면 None.

    grok_client 도 같은 규칙으로 정규화하지만, 화면에서 고른 카드에는
    _lint 같은 부가 정보가 붙어 올 수 있어 요청을 만들기 전에 한 번 더
    턴다. 작업 저장소에 들어가는 값은 작을수록 좋다.
    """
    if not isinstance(direction, dict):
        return None
    selected: dict[str, str] = {}
    for field in DIRECTION_FIELDS:
        value = direction.get(field)
        if not isinstance(value, str) or not value.strip():
            return None
        selected[field] = value.strip()
    return selected


def submit_directions(
    request: dict,
    *,
    submitter: Callable | None = None,
    engine: str = "",
    language: str = DEFAULT_LANGUAGE,
) -> dict | None:
    """방향 카드 작업 하나를 만든다. 주제가 비면 아무것도 보내지 않는다.

    작업 저장소는 비어 있지 않은 요청이면 무엇이든 받는다(의도된 설계다).
    그러니 빈 주제를 걸러 내는 일은 여기 클라이언트 쪽 몫이다.
    """
    keywords = str(request.get("keywords") or "").strip()
    if not keywords:
        return None

    payload = {"keywords": keywords, "mode": request.get("mode") or DEFAULT_MODE}
    submit = submitter or workspace_job_runner.submit_job
    return submit("directions", payload, engine=engine, language=language)


def submit_selected_direction(
    *,
    keywords: str,
    direction: dict,
    length: int = 0,
    mode: str = DEFAULT_MODE,
    language: str = DEFAULT_LANGUAGE,
    content_type: str = CONTENT_TYPE_IDEAS,
    category: str = "",
    references: str = "",
    engine: str = "",
    submitter: Callable | None = None,
) -> dict | None:
    """고른 방향 하나로 완성 글 작업을 만든다 — 정확히 한 번.

    사실 기반 팁일 때만 content_type/category/references 를 함께 보낸다.
    워커는 이 키를 보고 write_grounded_post 로 분기하고, 조사는 그때
    거기서 일어난다.
    """
    topic = str(keywords or "").strip()
    selected = normalize_direction(direction)
    if not topic or selected is None:
        return None

    request = {
        "keywords": topic,
        "direction": selected,
        "length": int(length or 0),
        "mode": mode or DEFAULT_MODE,
    }
    if content_type == CONTENT_TYPE_GROUNDED_TIP:
        request["content_type"] = CONTENT_TYPE_GROUNDED_TIP
        request["category"] = category
        request["references"] = references or ""

    submit = submitter or workspace_job_runner.submit_job
    return submit("post", request, engine=engine, language=language)


# ─────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────

def render_create() -> None:
    """만들기 영역. workspace_ui.app 의 AREA_RENDERERS 가 부른다."""
    store = _init_storage()
    settings = _shell_settings()

    ui.label(copy("nav_create")).classes("workspace-area-title")
    ui.label(copy("create_hint")).classes("workspace-hint")

    area = ui.column().classes("w-full gap-4")

    def repaint() -> None:
        # 입력값은 모두 스토리지에 묶여 있어 다시 그려도 잃을 게 없다.
        area.clear()
        with area:
            _render_area(store, settings, repaint)

    repaint()


def _render_area(store, settings: dict, repaint: Callable[[], None]) -> None:
    direction_job = job_view.load_job(store.get("active_direction_job_id"))
    post_job = job_view.load_job(store.get("active_post_job_id"))

    topic = _render_composer(
        store, settings, repaint, busy=job_view.is_pending(direction_job)
    )

    def keywords() -> str:
        return topic.value or ""

    if store.get("active_direction_job_id"):
        job_view.render_job(
            direction_job,
            on_result=lambda job: _render_directions(
                job, store, settings, repaint,
                keywords=keywords,
                disabled=job_view.is_pending(post_job),
            ),
            on_retry=lambda: _start_directions(store, settings, repaint, keywords()),
            marker="direction-job",
        )

    if store.get("active_post_job_id"):
        job_view.render_job(
            post_job,
            on_result=lambda job: editor.render_editor(
                job, store,
                pillar=editor.editor_pillar(
                    store.get("create_mode"), store.get("create_content_type")
                ),
                on_published=lambda: _finish_post(store, repaint),
            ),
            on_retry=lambda: _select_direction(
                store.get("create_direction"), store, settings, repaint, keywords()
            ),
            marker="post-job",
        )

    # 끝나지 않은 작업만 지켜본다. 상태가 바뀌면 영역을 한 번 다시 그린다.
    job_view.watch_jobs(
        {
            store.get("active_direction_job_id"): (direction_job or {}).get("status"),
            store.get("active_post_job_id"): (post_job or {}).get("status"),
        },
        on_change=repaint,
    )


def _render_composer(store, settings: dict, repaint: Callable[[], None], *, busy: bool):
    """주제 한 줄과 그 아래 옵션. 화면에서 가장 큰 것은 입력과 버튼이다.

    주제 입력 요소를 돌려준다 — 방향 카드와 다시 시도 버튼이 스토리지가
    아니라 지금 화면에 적힌 주제를 읽게 하기 위해서다.
    """
    with ui.column().classes("workspace-card w-full"):
        ui.label(copy("create_topic_label")).classes("text-base font-semibold")

        topic = ui.textarea(placeholder=copy("create_topic_placeholder")) \
            .props("autogrow outlined dense") \
            .classes("w-full text-base") \
            .bind_value(store, "create_input") \
            .mark("create-topic")

        content_type = ui.toggle({
            CONTENT_TYPE_IDEAS: copy("create_type_ideas"),
            CONTENT_TYPE_GROUNDED_TIP: copy("create_type_grounded"),
        }).props("unelevated no-caps dense") \
            .classes("w-full") \
            .bind_value(store, "create_content_type") \
            .mark("create-type")

        # 사실 기반 팁일 때만 보이는 것들. 조사는 방향을 고른 뒤 워커가 한다.
        grounded = ui.column().classes("w-full gap-2")
        grounded.bind_visibility_from(content_type, "value", value=CONTENT_TYPE_GROUNDED_TIP)
        with grounded:
            ui.label(copy("ideas_tip_category_label")).classes("workspace-hint")
            ui.toggle({
                category: copy(f"ideas_tip_category_{category}")
                for category in TIP_CATEGORIES
            }).props("unelevated no-caps dense") \
                .classes("w-full") \
                .bind_value(store, "create_category") \
                .mark("create-category")

            ui.input(placeholder=copy("ideas_references_label")) \
                .props("outlined dense") \
                .classes("w-full") \
                .bind_value(store, "create_references") \
                .mark("create-references")
            ui.label(copy("ideas_references_help")).classes("workspace-hint")
            ui.label(copy("ideas_health_finance_notice")).classes("workspace-notice")

        with ui.expansion(copy("create_options")).classes("w-full").mark("create-options"):
            ui.select(
                {
                    length: copy("create_length_auto") if length == 0
                    else copy("ideas_char_count", n=length)
                    for length in LENGTH_OPTIONS
                },
                label=copy("ideas_length_label"),
            ).props("outlined dense").classes("w-full") \
                .bind_value(store, "create_length").mark("create-length")

            ui.select(
                {key: writing_modes.mode_label(key) for key in writing_modes.mode_options()},
                label=copy("ideas_mode_label"),
            ).props("outlined dense").classes("w-full") \
                .bind_value(store, "create_mode").mark("create-mode")

        submit = ui.button(
            copy("create_directions_cta"),
            on_click=lambda: _start_directions(store, settings, repaint, topic.value or ""),
        ).props(f'{filled_button_props(settings["theme"])} size=lg') \
            .classes("w-full").mark("create-submit")

        # 빈 주제로는 보낼 수 없고, 이미 도는 작업이 있으면 더 보낼 수 없다.
        submit.bind_enabled_from(
            topic, "value",
            backward=lambda value: bool((value or "").strip()) and not busy,
        )

    return topic


def _render_directions(
    job: dict,
    store,
    settings: dict,
    repaint: Callable[[], None],
    *,
    keywords: Callable[[], str],
    disabled: bool,
) -> None:
    """방향 카드 3장. 제목·훅·각도·핵심만 보여 준다."""
    directions = (job.get("result") or {}).get("directions") or []

    ui.label(copy("create_directions_title")).classes("text-base font-semibold")
    ui.label(copy("create_directions_hint")).classes("workspace-hint")

    for index, direction in enumerate(directions):
        with ui.column().classes("workspace-card w-full gap-1") \
                .mark("direction-card", f"direction-card-{index}"):
            ui.label(direction.get("title", "")).classes("text-base font-semibold")
            ui.label(direction.get("hook", "")).classes("text-sm")
            ui.label(f'{copy("create_field_angle")} · {direction.get("angle", "")}') \
                .classes("workspace-hint")
            ui.label(f'{copy("create_field_core")} · {direction.get("core_message", "")}') \
                .classes("workspace-hint")

            select = ui.button(
                copy("create_direction_select"),
                on_click=lambda _event, picked=direction: _select_direction(
                    picked, store, settings, repaint, keywords()
                ),
            ).props(f'{filled_button_props(settings["theme"])} dense') \
                .classes("w-full").mark(f"direction-select-{index}")
            if disabled:
                # 완성 글이 이미 돌고 있다 — 두 번째 요청을 막는다.
                select.disable()


# ─────────────────────────────────────────────────────────────
# 행동
# ─────────────────────────────────────────────────────────────

def _start_directions(store, settings: dict, repaint: Callable[[], None], keywords: str) -> None:
    job = submit_directions(
        {"keywords": keywords, "mode": store.get("create_mode")},
        engine=settings["engine"],
        language=settings["language"],
    )
    if job is None:
        ui.notify(copy("create_topic_required"))
        return
    # 결과가 아니라 ID 만 들고 있는다. 결과의 주인은 작업 저장소다.
    store["active_direction_job_id"] = job["id"]
    repaint()


def _select_direction(
    direction, store, settings: dict, repaint: Callable[[], None], keywords: str
) -> None:
    job = submit_selected_direction(
        keywords=keywords,
        direction=direction,
        length=store.get("create_length") or 0,
        mode=store.get("create_mode") or DEFAULT_MODE,
        language=settings["language"],
        content_type=store.get("create_content_type") or CONTENT_TYPE_IDEAS,
        category=store.get("create_category") or "",
        references=store.get("create_references") or "",
        engine=settings["engine"],
    )
    if job is None:
        ui.notify(copy("create_topic_required"))
        return

    store["create_direction"] = normalize_direction(direction)
    store["active_post_job_id"] = job["id"]
    # 새 글이 오는 중이다 — 이전 초안과의 연결을 끊어야 그 초안이
    # 이 글의 자동저장에 덮어써지지 않는다.
    editor.clear_editor_state(store)
    repaint()


def _finish_post(store, repaint: Callable[[], None]) -> None:
    """발행을 기록한 뒤 에디터를 닫는다.

    작업 ID까지 지워야 화면이 완성 결과를 다시 그리지 않는다 — 다시
    그리면 이미 발행한 글로 새 초안이 생긴다.
    """
    store["active_post_job_id"] = None
    repaint()


def _init_storage():
    store = app.storage.user
    for key, value in STORAGE_DEFAULTS.items():
        store.setdefault(key, value)
    return store


def _shell_settings() -> dict:
    # 셸이 이 모듈을 임포트하므로 최상단에서 거꾸로 임포트하면 순환이
    # 된다. 부를 때는 셸이 이미 로드돼 있다.
    from workspace_ui.app import init_user_settings

    return init_user_settings()
