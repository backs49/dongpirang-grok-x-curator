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
from datetime import datetime, timedelta
from pathlib import Path

from content_queue import queue_lock, save_queue


JOBS_PATH = Path("content_queue/workspace_jobs.json")

# 방향 카드 생성 / 선택한 방향으로 포스트 한 편 작성 / 포스트 최적화.
JOB_KINDS = ("directions", "post", "optimize", "memo")

# job_view.PENDING_STATUSES 와 동일한 집합을 여기서도 유지한다 — 스토어가
# UI 모듈을 import 하지 않도록 값만 그대로 복제한다.
PENDING_STATUSES = ("queued", "running")
TERMINAL_STATUSES = ("completed", "failed")

# 종료된 작업 보관 기간과 최대 개수. 둘 중 하나라도 넘으면 정리한다.
PRUNE_TTL_DAYS = 7
PRUNE_MAX_TERMINAL = 200

# 워커가 죽어 영원히 queued 로 남은 작업이 재제출을 영구히 막지 않도록,
# 중복 판정은 이 창 안의 pending 작업으로만 제한한다.
DEDUP_WINDOW_MINUTES = 15


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


def _parse_timestamp(value) -> datetime | None:
    """updated_at 을 파싱한다. 비어 있거나 형식이 어긋나면 None — 나이를 알 수
    없는 잡을 정리 대상으로 오판하지 않기 위해서다."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _prune(jobs: list) -> list:
    """추가 전 정리. TTL 을 넘긴 terminal 잡을 지우고, 그러고도 terminal 이
    PRUNE_MAX_TERMINAL 을 넘으면 오래된 것부터 초과분을 지운다. pending 잡과
    updated_at 파싱 실패 잡은 나이·개수와 무관하게 항상 남긴다."""
    ttl_cutoff = datetime.now() - timedelta(days=PRUNE_TTL_DAYS)

    # 제거는 레코드 객체 동일성으로 판정한다 — "id" 필드를 쓰면 id 가 빠진 기형
    # 레코드끼리 None 키로 충돌해 pending 잡까지 지워질 수 있다.
    remove = set()
    survivors = []  # (updated_at, job) — TTL 은 통과했지만 개수 상한 대상인 terminal 잡
    for job in jobs:
        if job.get("status") not in TERMINAL_STATUSES:
            continue
        updated_at = _parse_timestamp(job.get("updated_at"))
        if updated_at is None:
            continue
        if updated_at < ttl_cutoff:
            remove.add(id(job))
            continue
        survivors.append((updated_at, job))

    if len(survivors) > PRUNE_MAX_TERMINAL:
        survivors.sort(key=lambda pair: pair[0])
        excess = len(survivors) - PRUNE_MAX_TERMINAL
        remove.update(id(job) for _, job in survivors[:excess])

    return [job for job in jobs if id(job) not in remove]


def _find_duplicate(
    jobs: list, *, kind: str, engine: str, language: str, request_key: str
) -> dict | None:
    """같은 요청이 이미 대기 중이면 그 잡을 돌려준다. DEDUP_WINDOW_MINUTES 를
    넘긴 pending 잡은 워커가 죽었을 수 있으니 제외해 재제출을 막지 않는다."""
    window_cutoff = datetime.now() - timedelta(minutes=DEDUP_WINDOW_MINUTES)
    for job in jobs:
        if job.get("status") not in PENDING_STATUSES:
            continue
        if job.get("kind") != kind or job.get("engine") != engine or job.get("language") != language:
            continue
        if json.dumps(job.get("request"), sort_keys=True, ensure_ascii=False) != request_key:
            continue
        updated_at = _parse_timestamp(job.get("updated_at"))
        if updated_at is None or updated_at < window_cutoff:
            continue
        return job
    return None


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

    같은 kind/engine/language/request 로 이미 대기 중인 잡이 있으면 새로
    만들지 않고 그 잡을 그대로 돌려준다 — 탭 두 개가 같은 요청을 동시에
    보내도 워커는 한 번만 일한다.
    """
    if kind not in JOB_KINDS:
        raise ValueError(f"unknown workspace job kind: {kind!r}")
    if not isinstance(request, dict) or not request:
        raise ValueError("workspace job request must be a non-empty dict")
    try:
        request_key = json.dumps(request, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"workspace job request must be JSON-serializable: {exc}") from exc

    engine = engine or ""
    language = language or ""
    now = _now()
    job = {
        "id": uuid.uuid4().hex,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "kind": kind,
        "request": copy.deepcopy(request),
        "engine": engine,
        "language": language,
    }
    with _transaction(path) as data:
        data["jobs"] = _prune(data["jobs"])
        duplicate = _find_duplicate(
            data["jobs"], kind=kind, engine=engine, language=language, request_key=request_key
        )
        if duplicate is not None:
            return copy.deepcopy(duplicate)
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
