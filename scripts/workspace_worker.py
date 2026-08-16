#!/usr/bin/env python3
"""워크스페이스 작업(방향 카드 / 선택 포스트 / 최적화)을 세션 밖에서
실행하는 단발성 워커."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import demo_data  # noqa: E402
import workspace_jobs  # noqa: E402
from provider_selection import build_provider  # noqa: E402


def _demo_directions() -> dict:
    """Demo 엔진은 프로바이더를 만들 수 없다(build_provider("Demo") 는 항상
    None 을 돌려준다) — demo_data 의 기존 아이디어 픽스처에서 결정적인
    방향 카드 3장을 파생한다."""
    ideas = demo_data.IDEAS_DEMO["ideas"]
    return {
        "directions": [
            {
                "title": idea["title"],
                "hook": idea["content"].strip().splitlines()[0],
                "angle": idea["mode"],
                "core_message": idea["strategy"].strip().splitlines()[0],
            }
            for idea in ideas
        ]
    }


def _demo_post() -> dict:
    idea = demo_data.IDEAS_DEMO["ideas"][0]
    return {"post": {"title": idea["title"], "content": idea["content"]}}


def _demo_optimize() -> dict:
    return copy.deepcopy(demo_data.OPTIMIZER_DEMO)


_DEMO_RESULTS = {
    "directions": _demo_directions,
    "post": _demo_post,
    "optimize": _demo_optimize,
}


def run(job_id: str, *, jobs_path: Path = workspace_jobs.JOBS_PATH) -> str:
    """작업 하나를 선점해 실행하고, 어떤 종료 경로에서도 상태를 기록한다."""
    job = workspace_jobs.claim_job(job_id, path=jobs_path)
    if job is None:
        return "not_claimed"

    try:
        if job["engine"] == "Demo":
            # Demo 는 실제 프로바이더가 없으므로 build_provider 호출 전에
            # 분기해 고정 결과로 완료한다. Demo 전용 프로바이더 클래스는
            # 만들지 않는다.
            result = _DEMO_RESULTS[job["kind"]]()
            workspace_jobs.complete_job(job_id, result, path=jobs_path)
            return "completed"

        grok, status = build_provider(job["engine"])
        if grok is None:
            # xAI API 키는 브라우저 쿠키에만 있어 detached 워커가 접근할 수
            # 없다 — api_key 없이 build_provider("xAI API") 를 부르면 여기서
            # 이미 안전하게 실패한다(별도 분기 불필요).
            workspace_jobs.fail_job(job_id, status.message, path=jobs_path)
            return "failed"

        request = job["request"]
        if job["kind"] == "directions":
            result = grok.generate_directions(
                request["keywords"], mode=request["mode"], language=job["language"]
            )
        elif job["kind"] == "post" and request.get("content_type") == "grounded_tip":
            # request.get(...) 사용 — 일반 포스트 요청에는 이 키가 아예 없어
            # request["content_type"] 로 읽으면 KeyError 가 fail_job 에
            # 삼켜져 정상 작업까지 실패로 처리된다.
            result = grok.write_grounded_post(
                keywords=request["keywords"],
                direction=request["direction"],
                category=request["category"],
                references=request["references"],
                length=request["length"],
                mode=request["mode"],
                language=job["language"],
            )
        elif job["kind"] == "post":
            result = grok.write_post(
                keywords=request["keywords"],
                direction=request["direction"],
                length=request["length"],
                mode=request["mode"],
                language=job["language"],
            )
        else:
            result = grok.optimize_post(request["text"], language=job["language"])

        if "error" in result:
            workspace_jobs.fail_job(job_id, result["error"], path=jobs_path)
            return "failed"

        workspace_jobs.complete_job(job_id, result, path=jobs_path)
        return "completed"
    except Exception as exc:
        workspace_jobs.fail_job(job_id, str(exc), path=jobs_path)
        return "failed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    run(args.job_id)
