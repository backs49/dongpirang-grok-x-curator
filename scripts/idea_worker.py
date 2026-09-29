#!/usr/bin/env python3
"""아이디어 생성 작업을 Streamlit 세션 밖에서 실행하는 단발성 워커."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import idea_jobs  # noqa: E402
from grounded_tips import CONTENT_TYPE_GROUNDED_TIP  # noqa: E402
from ideas_history import append_history  # noqa: E402
from provider_selection import build_provider  # noqa: E402
from xalgo_prompts import PROMPT_VERSION  # noqa: E402


def run(job_id: str, *, jobs_path: Path = idea_jobs.JOBS_PATH) -> str:
    """작업 하나를 선점해 실행하고, 어떤 종료 경로에서도 상태를 기록한다."""
    job = idea_jobs.claim_job(job_id, path=jobs_path)
    if job is None:
        return "not_claimed"

    try:
        if job.get("content_type") == CONTENT_TYPE_GROUNDED_TIP:
            grok, status = build_provider("Grok CLI")
        else:
            grok, status = build_provider(job["engine"])
        if grok is None:
            idea_jobs.fail_job(job_id, status.message, path=jobs_path)
            return "failed"

        if job.get("content_type") == CONTENT_TYPE_GROUNDED_TIP:
            result = grok.generate_grounded_tips(
                job["keywords"],
                category=job.get("tip_category", ""),
                references=job.get("references", ""),
                length=job["length"],
                mode=job["mode"],
                language=job.get("language", "ko"),
            )
        else:
            result = grok.generate_ideas(
                job["keywords"],
                length=job["length"],
                mode=job["mode"],
                language=job.get("language", "ko"),
            )
        if "error" in result:
            idea_jobs.fail_job(job_id, result["error"], path=jobs_path)
            return "failed"

        idea_jobs.complete_job(job_id, result, path=jobs_path)
        try:
            append_history(
                job["keywords"],
                job["length"],
                result,
                mode=job["mode"],
                engine=getattr(getattr(grok, "provider", None), "name", job["engine"]),
                prompt_version=PROMPT_VERSION,
                content_type=job.get("content_type", "ideas"),
                tip_category=job.get("tip_category", ""),
                references=job.get("references", ""),
            )
        except Exception:
            # 이력 파일 실패는 성공한 생성 결과를 실패로 바꾸지 않는다.
            pass
        return "completed"
    except Exception as exc:
        idea_jobs.fail_job(job_id, str(exc), path=jobs_path)
        return "failed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    run(args.job_id)
