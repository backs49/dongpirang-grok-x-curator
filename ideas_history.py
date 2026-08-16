"""아이디어 생성 이력 영속화.

아이디어 생성은 토큰 비용이 큰 작업인데 결과가 브라우저 세션에만 있어서
창을 닫으면 사라졌다. 생성 성공 시마다 JSONL 로 남겨 두고, 아이디어 탭의
이력 UI 에서 다시 불러오거나 키워드를 복원해 재생성할 수 있게 한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from grounded_tips import CONTENT_TYPE_GROUNDED_TIP, CONTENT_TYPE_IDEAS, TIP_CATEGORIES

HISTORY_PATH = Path("content_queue/ideas_history.jsonl")


def append_history(
    keywords: str,
    length: int,
    result: dict,
    *,
    mode: str = "",
    engine: str = "",
    prompt_version: str = "",
    content_type: str = CONTENT_TYPE_IDEAS,
    tip_category: str = "",
    references: str = "",
) -> None:
    """생성 결과를 이력 파일에 추가한다. 실패해도 생성 흐름을 막지 않는다."""
    try:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        safe_content_type = (
            content_type
            if isinstance(content_type, str)
            and content_type in {CONTENT_TYPE_IDEAS, CONTENT_TYPE_GROUNDED_TIP}
            else CONTENT_TYPE_IDEAS
        )
        safe_tip_category = (
            tip_category.strip()
            if safe_content_type == CONTENT_TYPE_GROUNDED_TIP
            and isinstance(tip_category, str)
            and tip_category.strip() in TIP_CATEGORIES
            else ""
        )
        entry = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "keywords": keywords,
            "length": length,
            "mode": mode,
            "engine": engine,
            "prompt_version": prompt_version,
            "content_type": safe_content_type,
            "tip_category": safe_tip_category,
            "references": references.strip() if isinstance(references, str) else "",
            "result": result,
        }
        with HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def load_history() -> list[dict]:
    """이력 전체를 최신순으로 반환한다. 깨진 줄은 건너뛴다."""
    if not HISTORY_PATH.is_file():
        return []
    entries: list[dict] = []
    try:
        lines = HISTORY_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict) and isinstance(entry.get("result"), dict):
            entry.setdefault("content_type", CONTENT_TYPE_IDEAS)
            entry.setdefault("tip_category", "")
            entry.setdefault("references", "")
            entries.append(entry)
    entries.reverse()
    return entries
