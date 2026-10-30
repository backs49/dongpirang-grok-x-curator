"""답글 → 원글 씨앗. 계정 주인이 최근 단 답글 중 생각이 담긴 것을 골라 소재로 쓴다.

왜 답글인가: 2026-10 기준 이 계정은 한 달에 답글 135개를 직접 쓰고 원글은 1개였다.
메모 실측(2026-09-30)에서 사람다운 글을 만든 건 프롬프트 규칙이 아니라 실제로 겪은
디테일과 본인 입장이었는데, 답글에는 그게 이미 들어 있다. 키워드로 팁을 짓는 대신
본인이 이미 한 말을 혼자 서는 글로 옮긴다.

여기서는 후보만 고른다(규칙 기반, 넉넉하게). 혼자 설 수 있는 생각인지 최종 판단은
글을 쓰는 모델이 skip 으로 한다 — 짧은 답글은 원글 없이는 뜻이 안 통하는 게 많다.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone

import stance_archive

# 최근 며칠 안 답글만 본다. 지난 소재는 이미 식은 얘기다.
WINDOW_DAYS = 2
MAX_SEEDS = 2
# @멘션·링크·기호를 뺀 글자 수. 10월 답글 135개 중 15자 이상은 약 60개였다.
MIN_CORE_CHARS = 15
# 인사·축하·위로·감사는 상대에게 하는 말이라 혼자 서는 글이 못 된다.
_SOCIAL = re.compile(
    r"명복|축하|감사|고맙|고생|생일|토닥|다행|화이팅|파이팅|응원|반가|바래요|바랍니다|가즈아|힘내"
)
# 가족 기록(찰떡이)은 보이스 카드와 마찬가지로 소재에서 뺀다.
_PRIVATE = re.compile(r"찰떡")


def load_rows() -> list[dict]:
    """아카이브 원본 행. 없거나 깨졌으면 빈 목록."""
    try:
        data = json.loads(stance_archive.ARCHIVE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def _parent_id(row: dict) -> str | None:
    for ref in row.get("referenced_tweets") or []:
        if isinstance(ref, dict) and ref.get("type") == "replied_to" and ref.get("id"):
            return str(ref["id"])
    return None


def _clean(text: str) -> str:
    text = re.sub(r"^(@\w+\s*)+", "", text.strip())
    return re.sub(r"https?://\S+", "", text).strip()


def _created(row: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(str(row.get("created_at", "")).replace("Z", "+00:00"))
    except ValueError:
        return None


def newest_id(rows: list[dict]) -> str | None:
    ids = [str(r["id"]) for r in rows if str(r.get("id", "")).isdigit()]
    return max(ids, key=int, default=None)


def pick_seeds(
    rows: list[dict],
    *,
    after_id: str | None,
    now: datetime,
    limit: int = MAX_SEEDS,
    generated: str | None = None,
) -> list[dict]:
    """after_id 이후, 최근 WINDOW_DAYS 일 안의 답글에서 씨앗 후보를 고른다.

    길수록(할 말이 많을수록), 노출이 많을수록 앞에 둔다. 반환 항목:
    {"reply_id", "parent_id", "text"}.
    """
    cutoff = now.astimezone(timezone.utc) - timedelta(days=WINDOW_DAYS)
    if generated is None:
        generated = stance_archive._generated_corpus()
    scored = []
    for row in rows:
        rid = str(row.get("id", ""))
        raw = row.get("text")
        if not rid.isdigit() or not isinstance(raw, str):
            continue
        if after_id and int(rid) <= int(after_id):
            continue
        created = _created(row)
        if created is None or created < cutoff:
            continue
        parent = _parent_id(row)
        if parent is None and not raw.lstrip().startswith("@"):
            continue  # 원글이다
        text = _clean(raw)
        core = stance_archive._norm(text)
        if len(core) < MIN_CORE_CHARS or _SOCIAL.search(text) or _PRIVATE.search(text):
            continue
        if len(core) >= 15 and core[:25] in generated:
            continue  # 이 도구가 만든 글을 답글로 옮긴 것
        impressions = (row.get("public_metrics") or {}).get("impression_count", 0) or 0
        score = len(core) + 8 * math.log10(1 + impressions)
        scored.append((score, {"reply_id": rid, "parent_id": parent, "text": text}))
    scored.sort(key=lambda x: -x[0])
    return [seed for _, seed in scored[:limit]]
