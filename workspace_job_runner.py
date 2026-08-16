"""워크스페이스 작업 워커 프로세스 시작 책임을 UI 세션에서 분리한다."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import workspace_jobs


REPO_ROOT = Path(__file__).resolve().parent
WORKER_PATH = REPO_ROOT / "scripts" / "workspace_worker.py"


def submit_job(
    kind: str,
    request: dict,
    *,
    engine: str,
    language: str,
    jobs_path: Path = workspace_jobs.JOBS_PATH,
    popen=subprocess.Popen,
) -> dict:
    """저장 성공 후 독립 워커를 시작한다. 시작 실패도 작업 상태로 돌려준다."""
    job = workspace_jobs.create_job(
        kind, request, engine=engine, language=language, path=jobs_path
    )
    try:
        popen(
            [sys.executable, str(WORKER_PATH), "--job-id", job["id"]],
            cwd=REPO_ROOT,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        return workspace_jobs.fail_job(job["id"], str(exc), path=jobs_path) or job
    return job
