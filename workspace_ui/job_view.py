"""저장된 작업 하나를 화면에 비추는 얇은 뷰 — 절대 스스로 보내지 않는다.

워크스페이스의 비용 통제는 여기서 갈린다. 브라우저는 작업을 만들지 않고,
만들어진 작업의 ID 만 들고 있다가 저장소를 다시 읽는다. 재접속하든 페이지가
다시 그려지든 같은 ID 를 읽을 뿐이므로 프로바이더 요청이 두 번 나가는 길이
없다. 실패한 작업도 마찬가지다 — 자동 재시도는 없고, 사람이 "다시 시도" 를
누를 때만 새 작업이 생긴다.

만들기(방향/포스트)와 다듬기(최적화)가 같은 모양을 쓰도록, 이 모듈은 작업의
종류를 모른다. 결과를 어떻게 그릴지는 호출자가 on_result 로 넘긴다.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from nicegui import ui

import workspace_jobs
from workspace_ui.copy import copy


# 아직 끝나지 않은 작업을 다시 읽는 간격.
POLL_SECONDS = 1.0

PENDING_STATUSES = ("queued", "running")


def load_job(job_id: str | None, *, read_job: Callable | None = None) -> dict | None:
    """저장된 작업 스냅샷. ID 가 없으면 읽지 않는다.

    workspace_jobs.get_job 은 일부러 락 없이 읽는다 — 작업 파일은 작고
    workspace_jobs 쪽 쓰기가 이미 mkstemp+os.replace 로 원자적이라 반쯤
    쓰인 내용을 볼 일이 없다. 이 읽기는 화면을 그리는 이벤트 루프 위에서
    동기로 도는데(여기와 watch_jobs 의 폴링 타이머 둘 다), 락을 걸면 그
    동안 다른 세션의 쓰기가 끝날 때까지 서버 전체가 멈춘다 — 락을 추가할
    거면 이 동기 읽기 자체를 먼저 다시 설계해야 한다.
    """
    if not job_id:
        return None
    reader = read_job or workspace_jobs.get_job
    return reader(job_id)


def is_pending(job: dict | None) -> bool:
    return (job or {}).get("status") in PENDING_STATUSES


def error_message(error: str) -> str:
    """작업이 남긴 오류 키를 사람이 읽을 문장으로 바꾼다.

    grok_client 가 돌려주는 키(invalid_post 같은)는 그대로 문구 사전에
    있고, 근거 기반 팁 오류는 레거시 앱과 같은 ideas_error_* 문구를 쓴다.
    사전에 없는 값(프로바이더 예외 메시지 등)은 감추지 말고 그대로 붙인다.
    """
    detail = (error or "").strip()
    if not detail:
        return copy("job_failed")

    grounded_key = f"ideas_error_{detail}"
    if (text := copy(grounded_key)) != grounded_key:
        return text
    if (text := copy(detail)) != detail:
        return text
    return copy("job_failed_detail", detail=detail)


def render_job(
    job: dict | None,
    *,
    on_result: Callable[[dict], None],
    on_retry: Callable[[], None] | None = None,
    marker: str = "job",
) -> None:
    """작업 스냅샷 하나를 현재 슬롯에 그린다. 저장소를 다시 읽지 않는다."""
    with ui.column().classes("w-full gap-2").mark(marker):
        status = (job or {}).get("status")

        if job is None:
            ui.label(copy("job_missing")).classes("workspace-hint").mark(f"{marker}-missing")
            return

        if status in PENDING_STATUSES:
            with ui.row().classes("items-center gap-2").mark(f"{marker}-progress"):
                ui.spinner(size="sm")
                ui.label(copy(f"job_{status}")).classes("workspace-hint")
            return

        if status == "completed":
            on_result(job)
            return

        with ui.column().classes("workspace-notice w-full").mark(f"{marker}-error"):
            ui.label(error_message(job.get("error", "")))
            if on_retry is not None:
                ui.button(copy("job_retry"), on_click=lambda: on_retry()) \
                    .props("flat dense").mark(f"{marker}-retry")


def watch_jobs(
    statuses: Mapping[str, str | None],
    *,
    on_change: Callable[[], None],
    read_job: Callable | None = None,
    poll_seconds: float | None = None,
) -> None:
    """아직 끝나지 않은 작업만 지켜보다가 상태가 바뀌면 한 번 알린다.

    statuses 는 이미 읽어 둔 {작업 ID: 상태} 다 — 화면을 그리려고 읽은 값을
    그대로 재사용해서 같은 파일을 두 번 읽지 않는다. 끝난 작업만 있으면
    타이머 자체를 만들지 않는다.
    """
    pending = {job_id: status for job_id, status in statuses.items()
               if job_id and status in PENDING_STATUSES}
    if not pending:
        return

    reader = read_job or workspace_jobs.get_job

    def poll() -> None:
        for job_id, status in pending.items():
            if (reader(job_id) or {}).get("status") != status:
                timer.deactivate()
                on_change()
                return

    timer = ui.timer(poll_seconds if poll_seconds is not None else POLL_SECONDS, poll)
