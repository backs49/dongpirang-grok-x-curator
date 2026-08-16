"""브라우저 세션과 독립적으로 방향/포스트/최적화 작업을 추적하는 영속 작업 큐.

idea_jobs.py 와 같은 구조(파일 락 + 트랜잭션 + queued→running 단발 클레임)를
따르되, 아이디어 탭이 아니라 NiceGUI 워크스페이스(방향 카드 → 선택 포스트 →
최적화)의 임의 요청을 credentials-free 하게 저장한다.
"""

from __future__ import annotations

import copy
import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from content_queue import queue_lock, save_queue


JOBS_PATH = Path("content_queue/workspace_jobs.json")

# 방향 카드 생성 / 선택한 방향으로 포스트 한 편 작성 / 포스트 최적화.
JOB_KINDS = ("directions", "post", "optimize")


def _empty_store() -> dict:
    return {"jobs": []}


def _load(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        return _empty_store()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_store()
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        return _empty_store()
    return data


@contextmanager
def _transaction(path: Path):
    path = Path(path)
    with queue_lock(path):
        data = _load(path)
        yield data
        save_queue(path, data)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _find(data: dict, job_id: str) -> dict | None:
    return next((job for job in data["jobs"] if job.get("id") == job_id), None)


def create_job(
    kind: str,
    request: dict,
    *,
    engine: str,
    language: str,
    path: Path = JOBS_PATH,
) -> dict:
    """새 작업을 먼저 저장한다. 워커는 이 저장이 성공한 뒤에만 시작한다.

    request 는 반드시 JSON 직렬화 가능한 평범한 데이터여야 한다 — API 키,
    쿠키, 프로바이더 객체를 절대 여기 담지 않는다. 알 수 없는 kind 나
    빈 request 는 아무것도 쓰지 않고 즉시 거부한다.
    """
    if kind not in JOB_KINDS:
        raise ValueError(f"unknown workspace job kind: {kind!r}")
    if not isinstance(request, dict) or not request:
        raise ValueError("workspace job request must be a non-empty dict")
    try:
        json.dumps(request, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"workspace job request must be JSON-serializable: {exc}") from exc

    now = _now()
    job = {
        "id": uuid.uuid4().hex,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "kind": kind,
        "request": copy.deepcopy(request),
        "engine": engine or "",
        "language": language or "",
    }
    with _transaction(path) as data:
        data["jobs"].append(job)
    return copy.deepcopy(job)


def claim_job(job_id: str, *, path: Path = JOBS_PATH) -> dict | None:
    """대기 중인 작업 하나를 실행 중으로 전환한다. 중복 워커는 받을 수 없다."""
    with _transaction(path) as data:
        job = _find(data, job_id)
        if job is None or job.get("status") != "queued":
            return None
        job["status"] = "running"
        job["updated_at"] = _now()
        return copy.deepcopy(job)


def complete_job(job_id: str, result: dict, *, path: Path = JOBS_PATH) -> dict | None:
    """성공 결과를 저장해, 끊긴 브라우저도 나중에 같은 작업을 복원하게 한다."""
    with _transaction(path) as data:
        job = _find(data, job_id)
        if job is None:
            return None
        job["status"] = "completed"
        job["updated_at"] = _now()
        job["result"] = copy.deepcopy(result)
        job.pop("error", None)
        return copy.deepcopy(job)


def fail_job(job_id: str, error: str, *, path: Path = JOBS_PATH) -> dict | None:
    """실패 원인을 작업과 함께 보존해 재접속 후에도 사용자에게 표시한다."""
    with _transaction(path) as data:
        job = _find(data, job_id)
        if job is None:
            return None
        job["status"] = "failed"
        job["updated_at"] = _now()
        job["error"] = (error or "unknown workspace job error").strip()
        job.pop("result", None)
        return copy.deepcopy(job)


def get_job(job_id: str, *, path: Path = JOBS_PATH) -> dict | None:
    """읽기 전용 스냅샷을 돌려준다. 호출자는 저장된 상태를 직접 바꾸지 못한다."""
    data = _load(Path(path))
    job = _find(data, job_id)
    return copy.deepcopy(job) if job is not None else None
