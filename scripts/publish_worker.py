#!/usr/bin/env python3
"""예약 발행 워커 (4c).

launchd/cron 이 발행 슬롯 시각(평일 08·19시, 토 10시)마다 실행한다.
멱등 설계라 아무 때나 여러 번 실행해도 안전하다:

- 승인됨(approved) + 슬롯 도래 + 유예시간(90분) 이내 → 발행
- 유예시간을 넘긴 슬롯(맥이 잠들어 있었던 경우 등) → 다음 빈 슬롯으로 재배정
- 기본은 dry-run. 실제 발행은 --live 플래그 또는 X_PUBLISH_LIVE=1.

사용:
  python scripts/publish_worker.py            # dry-run (발행 예정만 출력)
  python scripts/publish_worker.py --live     # 실제 발행
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from content_queue import QUEUE_PATH, approve_draft, queue_transaction  # noqa: E402
from providers.base import ProviderError  # noqa: E402
from publisher import XPublisher  # noqa: E402

GRACE = timedelta(minutes=90)
LOG_PATH = QUEUE_PATH.parent / "publish_log.jsonl"


def log_event(event: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {"at": datetime.now().isoformat(timespec="seconds"), **event}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(json.dumps(event, ensure_ascii=False))


def run(
    now: datetime | None = None,
    live: bool = False,
    queue_path=QUEUE_PATH,
    publisher=None,
) -> dict:
    """반환: {"posted": n, "reassigned": n, "pending": n}

    이중 게시를 막기 위해 두 트랜잭션으로 나눈다:

    1. 클레임 (락 아래) — 이전 실행이 크래시로 "publishing" 상태로 남긴
       초안은 재발행하지 않고 "error" 로 표시한다(실제로 발행됐는지 알 수
       없으므로 이중 게시 방지가 우선). 도래한 승인 초안은 live 모드에서
       "publishing" 으로 찜해 디스크에 즉시 반영한다 — 그래야 동시에 도는
       다른 워커 실행이 같은 초안을 다시 집지 않는다.
    2. 락 밖 — 찜한 초안에 대해서만 실제 X API 호출(post_text). 네트워크
       왕복 동안 큐 락을 잡지 않는다.
    3. 기록 (락 아래, live 이고 클레임이 있을 때만) — 성공하면 published,
       실패하면 슬롯을 유지한 채 approved 로 되돌려 다음 실행에서 재시도.
    """
    now = now or datetime.now()
    if live and publisher is None:
        publisher = XPublisher()

    posted = reassigned = pending = 0
    claims: list[dict] = []  # [{"id", "text"}] — 트랜잭션1에서 찜한 초안

    with queue_transaction(queue_path) as data:
        for draft in data["drafts"]:
            if draft["status"] == "publishing":
                draft["status"] = "error"
                log_event({
                    "event": "stale_publishing_needs_review",
                    "draft_id": draft["id"],
                })

        for draft in data["drafts"]:
            if draft["status"] != "approved" or not draft.get("slot"):
                continue
            slot = datetime.fromisoformat(draft["slot"])

            if slot > now:
                pending += 1
                continue

            if now - slot > GRACE:
                # 슬롯을 놓침 (맥 꺼짐 등) — 억지 발행 대신 다음 빈 슬롯으로 재배정
                old_slot = draft["slot"]
                approve_draft(data, draft["id"], now=now)
                reassigned += 1
                log_event({
                    "event": "slot_missed_reassigned",
                    "draft_id": draft["id"],
                    "old_slot": old_slot,
                    "new_slot": draft["slot"],
                })
                continue

            if not live:
                log_event({
                    "event": "dry_run_would_post",
                    "draft_id": draft["id"],
                    "slot": draft["slot"],
                    "text_preview": draft["text"][:60],
                })
                posted += 1
                continue

            draft["status"] = "publishing"
            claims.append({"id": draft["id"], "text": draft["text"]})

    results = []
    for claim in claims:
        try:
            result = publisher.post_text(claim["text"])
        except ProviderError as exc:
            results.append({"id": claim["id"], "ok": False, "error": str(exc)})
        else:
            results.append({"id": claim["id"], "ok": True, "tweet_id": result["id"]})

    if live and claims:
        with queue_transaction(queue_path) as data:
            by_id = {d["id"]: d for d in data["drafts"]}
            for r in results:
                draft = by_id.get(r["id"])
                if draft is None:
                    continue
                if r["ok"]:
                    draft["status"] = "published"
                    draft["tweet_id"] = r["tweet_id"]
                    draft["published_at"] = now.isoformat(timespec="seconds")
                    posted += 1
                    log_event({
                        "event": "published",
                        "draft_id": draft["id"],
                        "tweet_id": r["tweet_id"],
                        "url": f"https://x.com/i/status/{r['tweet_id']}",
                    })
                else:
                    draft["status"] = "approved"
                    log_event({
                        "event": "publish_failed",
                        "draft_id": draft["id"],
                        "error": r["error"],
                    })

    summary = {"posted": posted, "reassigned": reassigned, "pending": pending}
    log_event({"event": "run_summary", "live": live, **summary})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="실제로 발행한다")
    args = parser.parse_args()
    live = args.live or os.environ.get("X_PUBLISH_LIVE") == "1"
    run(live=live)
