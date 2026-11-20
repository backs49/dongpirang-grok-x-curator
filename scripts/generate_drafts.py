#!/usr/bin/env python3
"""야간 초안 생성 배치 (4b).

launchd 가 매일 밤 23시에 실행한다. 절제형 설계:

0. 승인 대기 초안이 STALE_DRAFT_DAYS 일 넘게 방치돼 있으면 관리자에게
   리마인드한다 (생성 여부와 무관하게 매일 밤 확인).
1. 초안 재고(draft+approved+publishing+error)가 STOCK_TARGET 개 이상이면
   직접 넣은 소재 변환과 팁 보충(3·4번)을 하지 않는다. error 를 빼면 해소되지
   않은 에러가 쌓인 채로 계속 새 초안을 찍어내 문제를 가린다 — 억지로
   콘텐츠를 늘리는 것보다 승인 큐가 얇게 유지되는 편이 낫다.
2. 답글 씨앗(reply_seeds.py)은 전체 재고와 별개로, 답글에서 나온 초안의 대기
   수가 REPLY_STOCK_TARGET 개 미만이면 돈다. 최근 답글 중 생각이 담긴 것을 최대
   2개 골라 소재로 넣고 draft_from_reply 로 혼자 서는 글로 옮긴다. 모델이 혼자
   설 수 없다고 하면(skip) 초안 없이 사용 처리만 한다.
3. 소재 인박스에 미사용 소재가 있으면 최대 MAX_MATERIALS_PER_NIGHT 개를
   초안으로 변환한다 (진정성 원칙이 담긴 draft_from_material 프롬프트 사용).
4. 변환할 소재가 하나도 없을 때만 팁(tip) 초안 1개를 키워드 기반으로 보충한다.
   키워드는 queue.json 의 settings.tip_keywords 로 바꿀 수 있다.

2번을 1번에서 떼어낸 이유: 2026-11-04~19 에 승인 안 된 팁 초안 4건이 재고
목표를 채워 답글 씨앗이 16일 동안 한 번도 돌지 못했다. 팁은 소재가 없을 때의
보충이고 답글은 계정 주인이 실제로 쓴 생각인데, 보충이 본래 소재를 막고 있었다.
1번과 2번이 둘 다 찼을 때만 배치 전체를 건너뛴다.

0번이 있는 이유: 승인은 사람이 해야 하는데(진정성 원칙, 풀오토 금지) 안 해도
아무 일이 일어나지 않는 구조였다. 2026-07-08 이후 초안 4건이 draft 상태로
쌓여 재고 목표를 채우자 이 배치는 매일 '재고 충분'만 찍고, 발행 워커는
approved 가 없어 헛돌았다. 33일간 발행 0건인 걸 아무도 알려주지 않았다.

엔진은 로컬 CLI(Claude → Codex 순서로 가용한 것)라 생성 비용이 없다.
Claude 가 먼저인 이유: 메모·답글 글쓰기 실측에서 Claude 가 더 나았고(2026-09-30),
2026-10-30 시험에서 Codex 는 답글 6건 전부 300초 타임아웃이었다.
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
    add_material,
    load_queue,
    queue_transaction,
    skip_material,
    unused_materials,
)

MAX_MATERIALS_PER_NIGHT = 3
STOCK_TARGET = 4
# 답글에서 나온 초안이 이만큼 승인을 기다리면 새 씨앗을 넣지 않는다. 씨앗은
# 하룻밤에 최대 2개라 이 값은 하룻밤 분량이다 — 승인이 멈춘 동안 식은 답글이
# 계속 쌓이지 않게 하는 상한이고, 전체 재고(STOCK_TARGET)와는 따로 센다.
REPLY_STOCK_TARGET = 2
# 재고로 세는 상태. approved·publishing 은 슬롯을 기다리는 중이고, error 는
# 사람이 X 에서 확인해 재승인해야 풀린다.
STOCK_STATUSES = ("draft", "approved", "publishing", "error")
DEFAULT_TIP_KEYWORDS = "AI 사이드프로젝트, 솔로 개발자, 빌드 인 퍼블릭"
LOG_PATH = QUEUE_PATH.parent / "draft_log.jsonl"

# 승인 대기 며칠째부터 리마인드할지. 평일 슬롯이 하루 2개라 3일이면
# 이미 5~6슬롯을 날린 셈이다.
STALE_DRAFT_DAYS = 3
# 같은 정체 상황을 며칠마다 다시 알릴지 (매일 보내면 알림 피로로 무시된다).
REMINDER_INTERVAL_DAYS = 3
# tunnel_watch.sh 가 기록하는 고정 접속 URL. 알림에서 바로 앱으로 가려고 읽는다.
# 워치독이 Funnel(공개) 대신 Tailscale Serve(사설)로 바뀌면서 파일명도
# funnel.url -> workspace.url 로 옮겼다. 승인은 워크스페이스에서 하므로
# 레거시(logs/legacy.url) 가 아니라 워크스페이스 주소를 건다.
WORKSPACE_URL_PATH = REPO_ROOT / "logs" / "workspace.url"


def log_event(event: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {"at": datetime.now().isoformat(timespec="seconds"), **event}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False))


def _build_cli_grok():
    """가용한 로컬 CLI 엔진으로 GrokClient 를 만든다 (Claude 우선)."""
    from provider_selection import build_provider

    for engine in ("Claude CLI", "Codex CLI"):
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
        return WORKSPACE_URL_PATH.read_text(encoding="utf-8").strip().splitlines()[0]
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


def _default_seed_source(after_id: str | None, now: datetime) -> tuple[list[dict], str | None]:
    """아카이브를 최신으로 당겨 답글 씨앗을 고르고 원글 본문을 붙인다.

    반환: (씨앗 목록, 이번에 본 가장 최근 글 id). X API 가 실패해도 배치는
    계속된다 — 갱신 실패면 07:20 에 받은 아카이브로, 원글 조회 실패면 원글
    없이(모델이 skip 할 가능성이 커질 뿐) 진행한다.
    """
    import archive_refresh
    import publisher
    import reply_seeds

    env = publisher.load_env()
    try:
        archive_refresh.refresh(env=env)
    except Exception as e:  # noqa: BLE001 — 네트워크·API 오류 전부 비치명적
        log_event({"event": "reply_seed_refresh_failed", "error": str(e)[:200]})
    rows = reply_seeds.load_rows()
    seeds = reply_seeds.pick_seeds(rows, after_id=after_id, now=now)
    parent_ids = [s["parent_id"] for s in seeds if s.get("parent_id")]
    parents: dict[str, str] = {}
    if parent_ids:
        try:
            parents = archive_refresh.fetch_texts(env, parent_ids)
        except Exception as e:  # noqa: BLE001
            log_event({"event": "reply_seed_parent_failed", "error": str(e)[:200]})
    for seed in seeds:
        seed["parent_text"] = parents.get(seed.get("parent_id") or "", "")
    return seeds, reply_seeds.newest_id(rows)


def _add_reply_seeds(seed_source, *, now: datetime, queue_path: Path) -> int:
    """답글 씨앗을 소재 인박스에 넣는다. 같은 답글은 두 번 넣지 않는다."""
    data = load_queue(queue_path)
    after_id = (data.get("reply_seeds") or {}).get("last_seen_id")
    try:
        seeds, newest = seed_source(after_id, now)
    except Exception as e:  # noqa: BLE001 — 씨앗이 없어도 기존 소재·팁 흐름은 돈다
        log_event({"event": "reply_seed_failed", "error": str(e)[:200]})
        return 0
    added = 0
    with queue_transaction(queue_path) as tx_data:
        seen = {m.get("reply_id") for m in tx_data["materials"] if m.get("reply_id")}
        for seed in seeds:
            if seed["reply_id"] in seen:
                continue
            material = add_material(
                tx_data,
                seed["text"],
                extra={
                    "origin": "reply",
                    "reply_id": seed["reply_id"],
                    "parent_text": seed.get("parent_text", ""),
                },
            )
            if material:
                added += 1
                log_event({"event": "reply_seed_added", "material_id": material["id"],
                           "reply_id": seed["reply_id"]})
        if newest:
            tx_data.setdefault("reply_seeds", {})["last_seen_id"] = newest
    return added


def _is_reply(material: dict) -> bool:
    return material.get("origin") == "reply"


def _reply_stock(data: dict) -> int:
    """답글 씨앗에서 나와 아직 재고로 남아 있는 초안 수."""
    reply_material_ids = {m["id"] for m in data["materials"] if _is_reply(m)}
    return sum(
        1
        for d in data["drafts"]
        if d["status"] in STOCK_STATUSES and d.get("material_id") in reply_material_ids
    )


def run(grok=None, queue_path=QUEUE_PATH, notify=None, now=None, seed_source=None) -> dict:
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

    # 문이 둘이다. stock_open 은 직접 넣은 소재와 팁 보충을, reply_open 은 답글
    # 씨앗을 연다. 팁 초안이 재고를 채워도 답글 씨앗은 막지 않는다.
    stock = sum(1 for d in data["drafts"] if d["status"] in STOCK_STATUSES)
    reply_stock = _reply_stock(data)
    stock_open = stock < STOCK_TARGET
    reply_open = reply_stock < REPLY_STOCK_TARGET
    if not stock_open:
        # 답글 씨앗만 도는 밤에도 남긴다 — 이 이벤트가 매일 밤 이어지면 승인이
        # 멈춰 있다는 뜻이다.
        log_event({
            "event": "skipped_stock_sufficient",
            "stock": stock,
            "reply_stock": reply_stock,
            "reply_seeds": "open" if reply_open else "full",
        })
    if not stock_open and not reply_open:
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    if grok is None:
        grok = _build_cli_grok()
    if grok is None:
        log_event({"event": "no_engine_available"})
        return {"from_materials": 0, "tip_drafts": 0, "skipped": True}

    # 답글 재고가 빌 때만 씨앗을 넣는다 — 승인이 멈춘 동안 인박스에 식은 답글이
    # 쌓이지 않게. 넣은 뒤 스냅샷을 다시 읽어 아래 변환 대상에 포함시킨다.
    seeds_added = 0
    if reply_open:
        seeds_added = _add_reply_seeds(
            seed_source or _default_seed_source, now=now, queue_path=queue_path
        )
        if seeds_added:
            data = load_queue(queue_path)

    # LLM 호출 구간 — 락을 쥐지 않는다. 결과만 모아뒀다가 호출이 모두
    # 끝난 뒤 한 트랜잭션 안에서 add_draft 를 실행한다.
    from_materials = 0
    # 오늘 밤 열린 문에 해당하는 소재만 변환 대상이다.
    materials_snapshot = [
        m for m in unused_materials(data) if (reply_open if _is_reply(m) else stock_open)
    ]
    materials = materials_snapshot[:MAX_MATERIALS_PER_NIGHT]
    material_drafts = []
    skipped_seeds: dict[str, str] = {}
    for material in materials:
        if _is_reply(material):
            result = grok.draft_from_reply(material["text"], material.get("parent_text", ""))
            if result.get("skip"):
                skipped_seeds[material["id"]] = result.get("reason", "")
                log_event({
                    "event": "reply_seed_skipped",
                    "material_id": material["id"],
                    "reason": result.get("reason", ""),
                })
                continue
        else:
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
    if stock_open and from_materials == 0 and not materials_snapshot:
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
    if material_drafts or tip_draft_kwargs is not None or skipped_seeds:
        with queue_transaction(queue_path) as tx_data:
            # 혼자 설 수 없다고 판정된 답글은 초안 없이 사용 처리 — 매일 밤 다시
            # 시도하지 않게. 이유는 인박스에서 볼 수 있게 남긴다.
            for material_id, reason in skipped_seeds.items():
                skip_material(tx_data, material_id, reason)
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

    summary = {
        "from_materials": from_materials,
        "tip_drafts": tip_drafts,
        "skipped": False,
        "reply_seeds_added": seeds_added,
        "reply_seeds_skipped": len(skipped_seeds),
    }
    log_event({"event": "run_summary", **summary})
    return summary


if __name__ == "__main__":
    run()
