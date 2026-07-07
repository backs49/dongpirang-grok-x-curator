#!/usr/bin/env python3
"""야간 초안 생성 배치 (4b).

launchd 가 매일 밤 23시에 실행한다. 절제형 설계:

1. 초안 재고(draft+approved)가 STOCK_TARGET 개 이상이면 아무것도 하지 않는다.
   억지로 콘텐츠를 늘리는 것보다 승인 큐가 얇게 유지되는 편이 낫다.
2. 소재 인박스에 미사용 소재가 있으면 최대 MAX_MATERIALS_PER_NIGHT 개를
   초안으로 변환한다 (진정성 원칙이 담긴 draft_from_material 프롬프트 사용).
3. 소재가 하나도 없을 때만 팁(tip) 초안 1개를 키워드 기반으로 보충한다.
   키워드는 queue.json 의 settings.tip_keywords 로 바꿀 수 있다.

엔진은 로컬 CLI(Codex → Claude 순서로 가용한 것)라 생성 비용이 없다.
생성된 초안은 전부 'draft' 상태 — 발행되려면 앱에서 사용자의 승인이 필요하다.

사용:
  python scripts/generate_drafts.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_queue import (  # noqa: E402
    QUEUE_PATH,
    add_draft,
    load_queue,
    save_queue,
    unused_materials,
)

MAX_MATERIALS_PER_NIGHT = 3
STOCK_TARGET = 4
DEFAULT_TIP_KEYWORDS = "AI 사이드프로젝트, 솔로 개발자, 빌드 인 퍼블릭"
LOG_PATH = QUEUE_PATH.parent / "draft_log.jsonl"


def log_event(event: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {"at": datetime.now().isoformat(timespec="seconds"), **event}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False))


def _build_cli_grok():
    """가용한 로컬 CLI 엔진으로 GrokClient 를 만든다 (Codex 우선)."""
    from provider_selection import build_provider

    for engine in ("Codex CLI", "Claude CLI"):
        grok, status = build_provider(engine)
        if grok is not None:
            log_event({"event": "engine_selected", "engine": engine})
            return grok
    return None


def run(grok=None, queue_path=QUEUE_PATH) -> dict:
    data = load_queue(queue_path)

    stock = sum(1 for d in data["drafts"] if d["status"] in ("draft", "approved"))
    if stock >= STOCK_TARGET:
        log_event({"event": "skipped_stock_sufficient", "stock": stock})
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    if grok is None:
        grok = _build_cli_grok()
    if grok is None:
        log_event({"event": "no_engine_available"})
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    from_materials = 0
    materials = unused_materials(data)[:MAX_MATERIALS_PER_NIGHT]
    for material in materials:
        result = grok.draft_from_material(material["text"])
        if "error" in result or not result.get("post"):
            log_event({
                "event": "draft_failed",
                "material_id": material["id"],
                "error": result.get("error", "empty post"),
            })
            continue
        draft = add_draft(
            data,
            text=result["post"],
            pillar=result.get("pillar", "build_in_public"),
            image_prompt=result.get("image_prompt", ""),
            material_id=material["id"],
        )
        from_materials += 1
        log_event({
            "event": "draft_created",
            "draft_id": draft["id"],
            "pillar": draft["pillar"],
            "source": "material",
        })

    tip_drafts = 0
    if from_materials == 0 and not unused_materials(data):
        keywords = (data.get("settings") or {}).get("tip_keywords") or DEFAULT_TIP_KEYWORDS
        result = grok.generate_ideas(keywords, length=0)
        ideas = result.get("ideas") or []
        if "error" in result or not ideas:
            log_event({"event": "tip_draft_failed", "error": result.get("error", "no ideas")})
        else:
            idea = ideas[0]
            draft = add_draft(
                data,
                text=idea.get("content", ""),
                pillar="tip",
                image_prompt=idea.get("image_prompt", ""),
            )
            tip_drafts = 1
            log_event({"event": "draft_created", "draft_id": draft["id"], "source": "tip"})

    save_queue(queue_path, data)
    summary = {"from_materials": from_materials, "tip_drafts": tip_drafts, "skipped": False}
    log_event({"event": "run_summary", **summary})
    return summary


if __name__ == "__main__":
    run()
