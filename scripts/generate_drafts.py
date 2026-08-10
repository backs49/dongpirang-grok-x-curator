#!/usr/bin/env python3
"""야간 초안 생성 배치 (4b).

launchd 가 매일 밤 23시에 실행한다. 절제형 설계:

0. 승인 대기 초안이 STALE_DRAFT_DAYS 일 넘게 방치돼 있으면 관리자에게
   리마인드한다 (생성 여부와 무관하게 매일 밤 확인).
1. 초안 재고(draft+approved+publishing+error)가 STOCK_TARGET 개 이상이면
   아무것도 하지 않는다. error 를 빼면 해소되지 않은 에러가 쌓인 채로
   계속 새 초안을 찍어내 문제를 가린다 — 억지로 콘텐츠를 늘리는 것보다
   승인 큐가 얇게 유지되는 편이 낫다.
2. 소재 인박스에 미사용 소재가 있으면 최대 MAX_MATERIALS_PER_NIGHT 개를
   초안으로 변환한다 (진정성 원칙이 담긴 draft_from_material 프롬프트 사용).
3. 소재가 하나도 없을 때만 팁(tip) 초안 1개를 키워드 기반으로 보충한다.
   키워드는 queue.json 의 settings.tip_keywords 로 바꿀 수 있다.

0번이 있는 이유: 승인은 사람이 해야 하는데(진정성 원칙, 풀오토 금지) 안 해도
아무 일이 일어나지 않는 구조였다. 2026-07-08 이후 초안 4건이 draft 상태로
쌓여 재고 목표를 채우자 이 배치는 매일 '재고 충분'만 찍고, 발행 워커는
approved 가 없어 헛돌았다. 33일간 발행 0건인 걸 아무도 알려주지 않았다.

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

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
# notify_admin 은 scripts/ 안에 있고 패키지가 아니라서 직접 경로를 넣어준다.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from content_queue import (  # noqa: E402
    QUEUE_PATH,
    add_draft,
    load_queue,
    queue_transaction,
    unused_materials,
)

MAX_MATERIALS_PER_NIGHT = 3
STOCK_TARGET = 4
DEFAULT_TIP_KEYWORDS = "AI 사이드프로젝트, 솔로 개발자, 빌드 인 퍼블릭"
LOG_PATH = QUEUE_PATH.parent / "draft_log.jsonl"

# 승인 대기 며칠째부터 리마인드할지. 평일 슬롯이 하루 2개라 3일이면
# 이미 5~6슬롯을 날린 셈이다.
STALE_DRAFT_DAYS = 3
# 같은 정체 상황을 며칠마다 다시 알릴지 (매일 보내면 알림 피로로 무시된다).
REMINDER_INTERVAL_DAYS = 3
# tunnel_watch.sh 가 기록하는 고정 접속 URL. 알림에서 바로 앱으로 가려고 읽는다.
FUNNEL_URL_PATH = REPO_ROOT / "logs" / "funnel.url"


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


def _parse_dt(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _app_url() -> str:
    """고정 접속 URL. 없으면 빈 문자열 (알림에서 그 줄만 빠진다)."""
    try:
        return FUNNEL_URL_PATH.read_text(encoding="utf-8").strip().splitlines()[0]
    except (OSError, IndexError):
        return ""


def _default_notify(text: str) -> bool:
    """관리자 1인 텔레그램 발송기. 수신자는 .env 의 TELEGRAM_CHAT_ID 뿐이다."""
    from notify_admin import send_to_admin

    return send_to_admin(text)


def _reminder_message(waiting: int, days: int) -> str:
    lines = [
        f"🐾 승인 대기 초안이 {waiting}건, 가장 오래된 것이 {days}일째 멈춰 있습니다.",
        "승인된 초안이 없으면 발행 워커는 올릴 게 없습니다 — 그 사이 발행은 0건입니다.",
        "발행 큐 탭에서 승인하거나 지워 주세요.",
    ]
    url = _app_url()
    if url:
        lines.append(url)
    return "\n".join(lines)


def _remind_stale_drafts(
    data: dict, *, now: datetime, notify, queue_path: Path = QUEUE_PATH
) -> bool:
    """승인 대기 초안이 방치돼 있으면 관리자에게 리마인드한다.

    반환값은 큐에 발송 시각을 새로 찍었는지 여부. `data` 는 판단(정체
    여부·중복 발송 스로틀)에만 쓰는 읽기 전용 스냅샷이고, 실제 발송 시각
    기록은 별도의 짧은 트랜잭션으로 재로드-수정-저장한다 — 판단과 쓰기
    사이에 다른 프로세스가 큐를 바꿔도 그 변경을 덮어쓰지 않는다.

    approved 는 세지 않는다. 슬롯이 오면 워커가 알아서 발행하니 사람이
    막고 있는 게 아니다. 오직 draft 상태만 사람의 승인을 기다린다.
    """
    waiting = [d for d in data["drafts"] if d.get("status") == "draft"]
    created = [t for t in (_parse_dt(d.get("created_at")) for d in waiting) if t]
    if not created:
        return False

    days = (now - min(created)).days
    if days < STALE_DRAFT_DAYS:
        return False

    last_sent = _parse_dt((data.get("reminders") or {}).get("stale_drafts_at"))
    if last_sent and (now - last_sent).days < REMINDER_INTERVAL_DAYS:
        log_event({
            "event": "stale_reminder_throttled",
            "waiting": len(waiting),
            "days": days,
        })
        return False

    if not notify(_reminder_message(len(waiting), days)):
        log_event({
            "event": "stale_reminder_failed",
            "waiting": len(waiting),
            "days": days,
        })
        return False

    with queue_transaction(queue_path) as tx_data:
        tx_data.setdefault("reminders", {})["stale_drafts_at"] = now.isoformat(
            timespec="seconds"
        )
    log_event({"event": "stale_reminder_sent", "waiting": len(waiting), "days": days})
    return True


def run(grok=None, queue_path=QUEUE_PATH, notify=None, now=None) -> dict:
    # 읽기 전용 스냅샷 — 리마인더 판단과 재고 계산에만 쓴다. 실제 저장은
    # 아래에서 각각 짧은 트랜잭션으로 재로드-수정한다 (LLM 호출 중 락을
    # 쥐고 있지 않기 위해서다).
    data = load_queue(queue_path)
    now = now or datetime.now()
    notify = notify if notify is not None else _default_notify

    # 생성 여부와 무관하게 매일 확인한다. 재고가 꽉 차서 스킵하는 밤이야말로
    # 승인이 멈춰 있을 확률이 가장 높은 밤이다. 발송 시각 기록은
    # _remind_stale_drafts 안에서 자체 트랜잭션으로 처리된다.
    _remind_stale_drafts(data, now=now, notify=notify, queue_path=queue_path)

    stock = sum(
        1 for d in data["drafts"] if d["status"] in ("draft", "approved", "publishing", "error")
    )
    if stock >= STOCK_TARGET:
        log_event({"event": "skipped_stock_sufficient", "stock": stock})
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    if grok is None:
        grok = _build_cli_grok()
    if grok is None:
        log_event({"event": "no_engine_available"})
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    # LLM 호출 구간 — 락을 쥐지 않는다. 결과만 모아뒀다가 호출이 모두
    # 끝난 뒤 한 트랜잭션 안에서 add_draft 를 실행한다.
    from_materials = 0
    materials_snapshot = unused_materials(data)
    materials = materials_snapshot[:MAX_MATERIALS_PER_NIGHT]
    material_drafts = []
    for material in materials:
        result = grok.draft_from_material(material["text"])
        if "error" in result or not result.get("post"):
            log_event({
                "event": "draft_failed",
                "material_id": material["id"],
                "error": result.get("error", "empty post"),
            })
            continue
        material_drafts.append({
            "text": result["post"],
            "pillar": result.get("pillar", "build_in_public"),
            "image_prompt": result.get("image_prompt", ""),
            "material_id": material["id"],
        })
        from_materials += 1

    tip_draft_kwargs = None
    tip_drafts = 0
    if from_materials == 0 and not materials_snapshot:
        keywords = (data.get("settings") or {}).get("tip_keywords") or DEFAULT_TIP_KEYWORDS
        result = grok.generate_ideas(keywords, length=0)
        ideas = result.get("ideas") or []
        if "error" in result or not ideas:
            log_event({"event": "tip_draft_failed", "error": result.get("error", "no ideas")})
        else:
            idea = ideas[0]
            tip_draft_kwargs = {
                "text": idea.get("content", ""),
                "pillar": "tip",
                "image_prompt": idea.get("image_prompt", ""),
            }
            tip_drafts = 1

    # LLM 호출이 모두 끝난 뒤에만 락을 쥔다 — 짧은 트랜잭션 하나로 확정한다.
    if material_drafts or tip_draft_kwargs is not None:
        with queue_transaction(queue_path) as tx_data:
            for kwargs in material_drafts:
                draft = add_draft(tx_data, **kwargs)
                log_event({
                    "event": "draft_created",
                    "draft_id": draft["id"],
                    "pillar": draft["pillar"],
                    "source": "material",
                })
            if tip_draft_kwargs is not None:
                draft = add_draft(tx_data, **tip_draft_kwargs)
                log_event({"event": "draft_created", "draft_id": draft["id"], "source": "tip"})

    summary = {"from_materials": from_materials, "tip_drafts": tip_drafts, "skipped": False}
    log_event({"event": "run_summary", **summary})
    return summary


if __name__ == "__main__":
    run()
