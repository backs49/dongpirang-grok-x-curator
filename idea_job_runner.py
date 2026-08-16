"""아이디어 워커 프로세스 시작 책임을 Streamlit UI에서 분리한다."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import idea_jobs


REPO_ROOT = Path(__file__).resolve().parent
WORKER_PATH = REPO_ROOT / "scripts" / "idea_worker.py"


def submit_job(
    keywords: str,
    length: int,
    mode: str,
    engine: str,
    *,
    jobs_path: Path = idea_jobs.JOBS_PATH,
    popen=subprocess.Popen,
) -> dict:
    """저장 성공 후 독립 워커를 시작한다. 시작 실패도 작업 상태로 돌려준다."""
    job = idea_jobs.create_job(keywords, length, mode, engine, path=jobs_path)
    try:
        popen(
            [sys.executable, str(WORKER_PATH), "--job-id", job["id"]],
            cwd=REPO_ROOT,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        return idea_jobs.fail_job(job["id"], str(exc), path=jobs_path) or job
    return job
