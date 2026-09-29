"""브라우저 세션과 독립적으로 아이디어 생성을 추적하는 영속 작업 큐."""

from __future__ import annotations

import copy
import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from content_queue import queue_lock, save_queue
from grounded_tips import CONTENT_TYPE_GROUNDED_TIP, CONTENT_TYPE_IDEAS, TIP_CATEGORIES
from i18n import normalize_language


JOBS_PATH = Path("content_queue/idea_jobs.json")


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
    # 이전 버전의 작업도 재접속 UI와 워커가 정상 아이디어 요청으로 읽는다.
    for job in data["jobs"]:
        if isinstance(job, dict):
            job.setdefault("content_type", CONTENT_TYPE_IDEAS)
            job.setdefault("tip_category", "")
            job.setdefault("references", "")
            job.setdefault("language", "ko")
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
    keywords: str,
    length: int,
    mode: str,
    engine: str,
    *,
    content_type: str = CONTENT_TYPE_IDEAS,
    tip_category: str = "",
    references: str = "",
    language: str = "ko",
    path: Path = JOBS_PATH,
) -> dict:
    """새 작업을 먼저 저장한다. 워커는 이 저장이 성공한 뒤에만 시작한다."""
    safe_content_type = (
        content_type
        if isinstance(content_type, str)
        and content_type in {CONTENT_TYPE_IDEAS, CONTENT_TYPE_GROUNDED_TIP}
        else CONTENT_TYPE_IDEAS
    )
    safe_tip_category = (
        tip_category.strip()
        if safe_content_type == CONTENT_TYPE_GROUNDED_TIP
        and isinstance(tip_category, str)
        and tip_category.strip() in TIP_CATEGORIES
        else ""
    )
    safe_references = references.strip() if isinstance(references, str) else ""
    now = _now()
    job = {
        "id": uuid.uuid4().hex,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "keywords": (keywords or "").strip(),
        "length": int(length),
        "mode": mode or "",
        "engine": engine or "",
        "content_type": safe_content_type,
        "tip_category": safe_tip_category,
        "references": safe_references,
        # 워커는 스트림릿 세션 밖이라 UI 언어를 모른다. 작업에 박아 넘긴다.
        "language": normalize_language(language),
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
        job["error"] = (error or "unknown idea generation error").strip()
        job.pop("result", None)
        return copy.deepcopy(job)


def get_job(job_id: str, *, path: Path = JOBS_PATH) -> dict | None:
    """읽기 전용 스냅샷을 돌려준다. 호출자는 저장된 상태를 직접 바꾸지 못한다."""
    data = _load(Path(path))
    job = _find(data, job_id)
    return copy.deepcopy(job) if job is not None else None
