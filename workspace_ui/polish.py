"""다듬기 — 이미 써 둔 포스트 한 편을 x-algorithm 기준으로 다시 쓴다.

만들기와 짝을 이루는 화면이지만 값싼 중간 단계(방향 카드)가 없다. 원문을
붙여넣으면 다듬기 작업 하나가 바로 나간다. 그래서 재접속·재구성이 두 번째
요청을 만들지 않게 지키는 규칙은 만들기와 똑같다 — 브라우저는 작업 ID 만
들고, 결과는 저장소에서 다시 읽는다.

다듬기의 작업 ID 는 만들기의 것과 다른 스토리지 키(active_optimize_job_id)
에 둔다. 하단 탭은 세 영역을 동시에 그리므로(보이는 탭만 CSS 로 가릴 뿐,
파이썬 렌더 함수는 페이지를 열 때 셋 다 실행된다) 같은 키를 썼다면 만들기
탭에서 새 글을 시작하는 순간 다듬기가 들고 있던 작업 ID 가 지워질 수
있었다. 독립된 키를 쓰면 두 작업이 동시에 돌아도 서로를 건드리지 않는다.

다듬기 작업 결과에는 점수·이유·제안까지 딸려 오지만, 화면은 그중 다듬은
본문(optimized_post)만 보여준다. 그 본문을 곧바로 에디터에 밀어넣지 않고
먼저 결과만 보여준 뒤 "에디터에서 계속 고치기" 버튼을 눌러야 에디터가
열리게 한 것은 의도된 차이다 — 만들기는 카드를 고른 순간 바로 써야 할
글이 하나뿐이지만, 다듬기는 결과를 먼저 읽고 계속할지 결정할 여지를 준다.

에디터 스토리지 키는 만들기와 완전히 분리한다(key_prefix="optimize_").
만들기는 완성 글이 나오면 곧바로 자기 에디터를 열고, 다듬기는 버튼을
눌러야 연다 — 그런데 ui.tab_panels 는 보이는 탭만 CSS 로 가릴 뿐 세 영역의
렌더 함수를 페이지를 열 때마다 모두 실행하므로, 두 에디터가 같은 스토리지
키(editor_job_id 등)를 썼다면 둘 다 같은 초안을 가리키게 되고, 어느 쪽
텍스트 영역에 타이핑해도 그 값이 두 텍스트 영역 모두에 밀려 들어가며
자동저장은 상대방의 초안 파일에 잘못된 기둥·출처로 덮어써 버린다. 그래서
다듬기는 처음부터 이 화면만의 세 키를 쓴다.
"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import app, run, ui

import workspace_job_runner
from grounded_tips import CONTENT_TYPE_IDEAS
from workspace_ui import editor, job_view
from workspace_ui.copy import copy
from workspace_ui.create import DEFAULT_MODE, filled_button_props


DEFAULT_LANGUAGE = "ko"

# 다듬기 초안의 출처 표시. 에디터의 기본값("post")과 구분해 발행 큐에서
# 이 초안이 어디서 왔는지 알 수 있게 한다.
SOURCE_KIND = "optimize"

# 다듬기 결과가 만드는 초안의 기둥. 방향/모드 선택이 없는 화면이라
# 만들기의 기본값(자동 믹스 + 일반 아이디어)과 같은 규칙을 그대로 써서
# "curation" 이 된다 — create.py 가 고른 것과 같은 관례다.
PILLAR = editor.editor_pillar(DEFAULT_MODE, CONTENT_TYPE_IDEAS)

# 이 화면의 에디터가 쓰는 스토리지 키 접두어. 만들기의 에디터(접두어 없음)
# 와 완전히 분리된 job_id/draft_id/text 세 키를 만든다 — editor.py 의
# editor_storage_keys 문서에 그 이유가 적혀 있다.
EDITOR_KEY_PREFIX = "optimize_"
_EDITOR_KEYS = editor.editor_storage_keys(EDITOR_KEY_PREFIX)

# 이 영역이 쓰는 사용자 스토리지. active_optimize_job_id 는 만들기의
# active_direction_job_id/active_post_job_id 와 독립적이다 — 하단 탭을
# 오가도 서로의 작업을 지우지 않기 위해서다. 에디터 세 키도 만들기와
# 분리된 이름(optimize_editor_*)을 쓴다 — 단일 소스(_EDITOR_KEYS)에서
# 가져와 editor.render_editor 에 넘기는 key_prefix 와 절대 어긋나지 않는다.
STORAGE_DEFAULTS = {
    "active_optimize_job_id": None,
    "optimize_editor_open": False,
    _EDITOR_KEYS.job_id: None,
    _EDITOR_KEYS.draft_id: None,
    _EDITOR_KEYS.text: "",
}


# ─────────────────────────────────────────────────────────────
# 순수 헬퍼 — 브라우저 없이 요청의 모양을 검사할 수 있다
# ─────────────────────────────────────────────────────────────

def submit_optimization(
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    engine: str = "",
    submitter: Callable | None = None,
) -> dict | None:
    """다듬기 작업 하나를 만든다. 원문이 비면 아무것도 보내지 않는다.

    작업 저장소는 비어 있지 않은 요청이면 무엇이든 받으므로, 빈 원문을
    거르는 일은 여기 클라이언트 쪽 몫이다(만들기의 submit_directions 와
    같은 규칙).
    """
    body = str(text or "").strip()
    if not body:
        return None

    submit = submitter or workspace_job_runner.submit_job
    return submit("optimize", {"text": body}, engine=engine, language=language)


def optimized_text(job: dict | None) -> str:
    """작업 결과에서 다듬은 글만 뽑는다. 데모/실 프로바이더 결과 모두
    optimized_post 키를 쓴다(OPTIMIZER_DEMO 와 grok_client 가 같은 모양)."""
    return ((job or {}).get("result") or {}).get("optimized_post") or ""


def polish_score(job: dict | None) -> int | None:
    """작업 결과에서 표시 가능한 점수만 뽑는다.

    옛 잡·실험 모드 결과는 score 가 아예 없거나 형이 다를 수 있으므로
    int 가 아니면 조용히 None 을 돌려준다. bool 은 int 의 서브클래스라
    isinstance(True, int) 가 참이 되므로 따로 걸러낸다.
    """
    score = ((job or {}).get("result") or {}).get("score")
    if isinstance(score, bool) or not isinstance(score, int):
        return None
    return score


def polish_reasons(job: dict | None) -> list[str]:
    """작업 결과에서 표시 가능한 분석 이유만 뽑는다.

    reasons 가 없거나 리스트가 아니면 빈 리스트를 돌려주고, 항목 중
    문자열이 아니거나 빈 문자열인 것은 걸러낸다 — 어느 쪽도 예외를 내지
    않는다.
    """
    reasons = ((job or {}).get("result") or {}).get("reasons")
    if not isinstance(reasons, list):
        return []
    return [reason for reason in reasons if isinstance(reason, str) and reason.strip()]


# ─────────────────────────────────────────────────────────────
# 화면
# ─────────────────────────────────────────────────────────────

def render_polish() -> None:
    """다듬기 영역. workspace_ui.app 의 AREA_RENDERERS 가 부른다."""
    store = _init_storage()
    settings = _shell_settings()

    ui.label(copy("nav_polish")).classes("workspace-area-title")
    ui.label(copy("polish_hint")).classes("workspace-hint")

    area = ui.column().classes("w-full gap-4")

    def repaint() -> None:
        area.clear()
        with area:
            _render_area(store, settings, repaint)

    repaint()


def _render_area(store, settings: dict, repaint: Callable[[], None]) -> None:
    optimize_job = job_view.load_job(store.get("active_optimize_job_id"))

    # 이 렌더 패스 동안만 사는 "제출 중" 표시. create._render_area 와 같은
    # 이유로 store 가 아니라 지역 dict 를 쓴다 — _start_optimize 참고.
    submitting = {"optimize": False}

    text_input = _render_composer(
        store, settings, repaint, submitting, busy=job_view.is_pending(optimize_job)
    )

    if store.get("active_optimize_job_id"):
        job_view.render_job(
            optimize_job,
            on_result=lambda job: _render_result(job, store, settings, repaint),
            on_retry=lambda: _start_optimize(
                store, settings, repaint, submitting, text_input.value or ""
            ),
            marker="optimize-job",
        )

    # 끝나지 않은 작업만 지켜본다. 상태가 바뀌면 영역을 한 번 다시 그린다.
    job_view.watch_jobs(
        {store.get("active_optimize_job_id"): (optimize_job or {}).get("status")},
        on_change=repaint,
    )


def _render_composer(
    store, settings: dict, repaint: Callable[[], None], submitting: dict, *, busy: bool
):
    """원문 붙여넣기 한 칸과 다듬기 시작 버튼."""
    with ui.column().classes("workspace-card w-full"):
        ui.label(copy("polish_input_label")).classes("text-base font-semibold")

        text_input = ui.textarea(placeholder=copy("polish_input_placeholder")) \
            .props("autogrow outlined dense") \
            .classes("w-full text-base") \
            .bind_value(store, "polish_input") \
            .mark("polish-input")

        submit = ui.button(
            copy("polish_submit_cta"),
            on_click=lambda: _start_optimize(
                store, settings, repaint, submitting, text_input.value or ""
            ),
        ).props(f'{filled_button_props(settings["theme"])} size=lg') \
            .classes("w-full").mark("polish-submit")

        # 빈 원문으로는 보낼 수 없고, 이미 도는 작업이 있으면 더 보낼 수 없다.
        submit.bind_enabled_from(
            text_input, "value",
            backward=lambda value: bool((value or "").strip()) and not busy,
        )

    return text_input


def _render_result(job: dict, store, settings: dict, repaint: Callable[[], None]) -> None:
    """완성한 분석을 보여주고, 계속 고칠지는 사람이 버튼으로 정한다.

    점수·이유는 있을 때만 보여준다 — 옛 잡·실험 모드 결과는 둘 다 없을 수
    있다(polish_score/polish_reasons 가 그 형 검사를 맡는다). suggestions
    는 모바일 화면을 아끼려고 이번 범위에서 뺐다.
    """
    optimized = optimized_text(job)
    score = polish_score(job)
    reasons = polish_reasons(job)

    with ui.column().classes("workspace-card w-full gap-2").mark("optimize-result"):
        ui.label(copy("polish_result_title")).classes("text-base font-semibold")

        if score is not None:
            ui.label(f'{copy("opt_score")}: {score}/100') \
                .classes("text-sm font-semibold").mark("optimize-score")

        if reasons:
            with ui.column().classes("gap-1").mark("optimize-reasons"):
                ui.label(copy("opt_reasons")).classes("text-sm font-semibold")
                for reason in reasons:
                    ui.label(f"· {reason}").classes("text-sm")

        ui.label(optimized).classes("text-sm whitespace-pre-wrap").mark("optimize-preview")

        # 이미 이 작업으로 에디터를 연 적이 있으면(재접속 포함) 버튼을 다시
        # 누르게 하지 않고 곧장 에디터를 그린다. 이 플래그는 새 다듬기
        # 요청을 보내거나(_start_optimize) 발행을 기록할 때(_finish_optimize)
        # 매번 False 로 되돌아가므로, 지금 작업이 맞는지 따로 대조할
        # 필요가 없다 — 활성 작업이 바뀌는 순간 함께 닫힌다.
        if store.get("optimize_editor_open"):
            _render_editor_for(job, store, repaint)
        else:
            ui.button(
                copy("polish_open_editor"),
                on_click=lambda: _open_editor(job, store, repaint),
            ).props(f'{filled_button_props(settings["theme"])} dense') \
                .classes("w-full").mark("optimize-open-editor")


def _render_editor_for(job: dict, store, repaint: Callable[[], None]) -> None:
    editor_job = {"id": job.get("id"), "result": {"post": {"content": optimized_text(job)}}}
    editor.render_editor(
        editor_job, store,
        pillar=PILLAR,
        on_published=lambda: _finish_optimize(store, repaint),
        source_kind=SOURCE_KIND,
        key_prefix=EDITOR_KEY_PREFIX,
    )


# ─────────────────────────────────────────────────────────────
# 행동
# ─────────────────────────────────────────────────────────────

async def _start_optimize(
    store, settings: dict, repaint: Callable[[], None], submitting: dict, text: str
) -> None:
    """다듬기 작업을 큐에 올린다.

    submit_optimization 도 만들기의 submit_directions/submit_selected_direction
    과 같은 flock 기반 큐 락(최대 10초)을 잡고 워커를 띄운다 — 클릭
    핸들러에서 그대로 부르면 이벤트 루프가 멈춘다. editor.py 의 자동저장과
    같은 이유로 run.io_bound 워커 스레드에서 돌리고, 락을 못 잡으면 같은
    queue_busy 문구로 알린다.

    submitting["optimize"] 는 create.py 의 _start_directions 와 같은 이유로
    첫 await 전에 동기로 검사·설정한다 — 두 번 연속 클릭이 아직 끝나지
    않은 io_bound 호출 위로 두 번째 태스크를 얹어 프로바이더 작업을 두 번
    보내지 못하게 막는다.
    """
    if submitting["optimize"]:
        return
    submitting["optimize"] = True
    try:
        try:
            job = await run.io_bound(
                submit_optimization, text, engine=settings["engine"], language=settings["language"]
            )
        except TimeoutError:
            ui.notify(copy("queue_busy"))
            return
        if job is None:
            ui.notify(copy("polish_input_required"))
            return
        # 결과가 아니라 ID 만 들고 있는다. 결과의 주인은 작업 저장소다.
        store["active_optimize_job_id"] = job["id"]
        store["optimize_editor_open"] = False
        # 새 다듬기 요청이 오는 중이다 — 이 화면의 에디터가 이전 초안과의
        # 연결을 그대로 들고 있으면, 이번 결과를 열었을 때 옛 본문 위에
        # 자동저장이 덮어써질 수 있다. 이 화면 전용 키만 지운다.
        editor.clear_editor_state(store, key_prefix=EDITOR_KEY_PREFIX)
        repaint()
    finally:
        submitting["optimize"] = False


def _open_editor(job: dict, store, repaint: Callable[[], None]) -> None:
    store["optimize_editor_open"] = True
    repaint()


def _finish_optimize(store, repaint: Callable[[], None]) -> None:
    """발행 기록 후 다듬기 결과와 에디터를 함께 닫는다.

    작업 ID 까지 지워야 화면이 완성 결과를 다시 그리지 않는다 — 다시
    그리면 이미 발행한 글로 새 초안이 생긴다(만들기의 _finish_post 와
    같은 규칙).
    """
    store["active_optimize_job_id"] = None
    store["optimize_editor_open"] = False
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
