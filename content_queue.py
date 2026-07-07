"""발행 큐 저장소.

앱(발행 큐 탭)과 배치 스크립트(초안 생성·발행 워커)가 공유하는
로컬 JSON 파일 기반 큐. 스키마:

{
  "materials": [{"id", "text", "created_at", "used"}],
  "drafts": [{"id", "text", "pillar", "status", "slot",
               "image_prompt", "material_id", "created_at"}]
}

status: draft → approved → published (또는 rejected)
slot: 승인 시 배정되는 발행 예정 시각 (ISO 문자열, 로컬 시간)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

QUEUE_PATH = Path("content_queue/queue.json")

# 발행 슬롯: 평일 08시·19시, 토요일 10시, 일요일 없음 (스케줄러 탭의
# 한국 시간대 피크 지식을 그대로 반영)
_WEEKDAY_SLOTS = {
    0: (8, 19),   # 월
    1: (8, 19),   # 화
    2: (8, 19),   # 수
    3: (8, 19),   # 목
    4: (8, 19),   # 금
    5: (10,),     # 토
    6: (),        # 일
}

PILLARS = ("build_in_public", "retrospective", "tip", "curation")


def empty_queue() -> dict:
    return {"materials": [], "drafts": []}


def load_queue(path: Path = QUEUE_PATH) -> dict:
    path = Path(path)
    if not path.is_file():
        return empty_queue()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_queue()
    if not isinstance(data, dict):
        return empty_queue()
    data.setdefault("materials", [])
    data.setdefault("drafts", [])
    return data


def save_queue(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def next_slots(after: datetime, count: int) -> list[datetime]:
    """after 이후의 발행 슬롯을 시간순으로 count 개 돌려준다."""
    slots: list[datetime] = []
    day = after.replace(hour=0, minute=0, second=0, microsecond=0)
    while len(slots) < count:
        for hour in _WEEKDAY_SLOTS[day.weekday()]:
            slot = day.replace(hour=hour)
            if slot > after:
                slots.append(slot)
                if len(slots) == count:
                    break
        day += timedelta(days=1)
    return slots


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def add_material(data: dict, text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    material = {
        "id": _new_id(),
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "used": False,
    }
    data["materials"].append(material)
    return material


def unused_materials(data: dict) -> list[dict]:
    return [m for m in data["materials"] if not m.get("used")]


def remove_material(data: dict, material_id: str) -> None:
    data["materials"] = [m for m in data["materials"] if m["id"] != material_id]


def add_draft(
    data: dict,
    *,
    text: str,
    pillar: str,
    image_prompt: str = "",
    material_id: str | None = None,
) -> dict:
    draft = {
        "id": _new_id(),
        "text": text,
        "pillar": pillar,
        "status": "draft",
        "slot": None,
        "image_prompt": image_prompt,
        "material_id": material_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    data["drafts"].append(draft)
    if material_id:
        for m in data["materials"]:
            if m["id"] == material_id:
                m["used"] = True
    return draft


def _find_draft(data: dict, draft_id: str) -> dict | None:
    for d in data["drafts"]:
        if d["id"] == draft_id:
            return d
    return None


def approve_draft(data: dict, draft_id: str, now: datetime | None = None) -> dict | None:
    """초안을 승인하고 아직 배정되지 않은 가장 이른 슬롯을 배정한다."""
    draft = _find_draft(data, draft_id)
    if draft is None:
        return None
    now = now or datetime.now()
    taken = {
        d["slot"]
        for d in data["drafts"]
        if d.get("slot") and d["status"] in ("approved", "published")
    }
    for slot in next_slots(now, count=len(taken) + 1):
        iso = slot.isoformat()
        if iso not in taken:
            draft["slot"] = iso
            break
    draft["status"] = "approved"
    return draft


def reject_draft(data: dict, draft_id: str) -> None:
    draft = _find_draft(data, draft_id)
    if draft:
        draft["status"] = "rejected"
        draft["slot"] = None


def update_draft_text(data: dict, draft_id: str, text: str) -> None:
    draft = _find_draft(data, draft_id)
    if draft:
        draft["text"] = text


def remove_draft(data: dict, draft_id: str) -> None:
    data["drafts"] = [d for d in data["drafts"] if d["id"] != draft_id]
