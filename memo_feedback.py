"""메모로 쓰기 선택·수정 기록 — 무엇을 골랐고 발행 전에 어떻게 고쳤는지.

AI 채점자 점수보다 정확한 신호는 계정 주인이 직접 지운 표현이다. 발행할 때마다
메모, 초안 5편, 고른 번호, 최종 본문을 남기고, 자주 지운 표현을 모아 보여 준다.
"""

from __future__ import annotations

import difflib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

FEEDBACK_PATH = Path("content_queue/memo_feedback.jsonl")


def build_record(job: dict, choice: int, final_text: str) -> dict | None:
    posts = ((job or {}).get("result") or {}).get("posts") or []
    if not isinstance(choice, int) or not 0 <= choice < len(posts):
        return None
    drafts = [str(p.get("content", "")) for p in posts]
    chosen = drafts[choice]
    final = (final_text or "").strip()
    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "job_id": job.get("id"),
        "engine": job.get("engine"),
        "memo": ((job.get("request") or {}).get("memo") or ""),
        "drafts": drafts,
        "chosen_index": choice,
        "chosen": chosen,
        "final": final,
        "similarity": round(difflib.SequenceMatcher(None, chosen, final).ratio(), 3),
    }


def record_publish(job: dict, choice: int, final_text: str, *, path: Path | None = None) -> dict | None:
    """발행 기록을 한 줄 덧붙인다. 실패해도 발행 흐름을 막지 않는다."""
    record = build_record(job, choice, final_text)
    if record is None:
        return None
    target = FEEDBACK_PATH if path is None else path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        return None
    return record


def load_records(path: Path | None = None) -> list[dict]:
    target = FEEDBACK_PATH if path is None else path
    if not target.is_file():
        return []
    records = []
    for line in target.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _tokens(text: str) -> list[str]:
    return re.findall(r"[가-힣A-Za-z0-9]+|[^\s가-힣A-Za-z0-9]", text)


def summarize(records: list[dict], *, top: int = 15) -> dict:
    """고른 번호 분포, 그대로 올린 비율, 자주 지운/더한 표현."""
    if not records:
        return {"count": 0}
    removed: Counter = Counter()
    added: Counter = Counter()
    for r in records:
        a, b = _tokens(r.get("chosen", "")), _tokens(r.get("final", ""))
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if op in ("delete", "replace"):
                removed[" ".join(a[i1:i2])] += 1
            if op in ("insert", "replace"):
                added[" ".join(b[j1:j2])] += 1
    return {
        "count": len(records),
        "chosen_index": dict(Counter(r.get("chosen_index") for r in records)),
        "unedited_ratio": round(sum(1 for r in records if r.get("chosen") == r.get("final")) / len(records), 2),
        "avg_similarity": round(sum(r.get("similarity", 0) for r in records) / len(records), 3),
        "often_removed": removed.most_common(top),
        "often_added": added.most_common(top),
    }
