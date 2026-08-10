"""보이스 카드 — 계정 주인의 실제 글 예시(few-shot) 영속화.

AI티 제거에 가장 효과적인 단일 기법은 본인 글 few-shot 보이스 매칭이다.
사용자가 등록한 실제 포스트와 1회성 스타일 분석을 저장해 두고, 모든
아이디어/초안 생성 프롬프트에 상주 블록으로 주입한다.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

VOICE_CARD_PATH = Path("content_queue/voice_card.json")


def save_voice_card(examples: list[str], analysis: str = "") -> None:
    VOICE_CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "examples": [e.strip() for e in examples if e.strip()],
        "analysis": analysis.strip(),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    VOICE_CARD_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )


def load_voice_card() -> dict:
    """카드를 읽는다. 없거나 손상됐으면 빈 카드 — 흐름을 막지 않는다."""
    if not VOICE_CARD_PATH.is_file():
        return {"examples": [], "analysis": "", "updated_at": ""}
    try:
        data = json.loads(VOICE_CARD_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"examples": [], "analysis": "", "updated_at": ""}
    if not isinstance(data, dict) or not isinstance(data.get("examples"), list):
        return {"examples": [], "analysis": "", "updated_at": ""}
    return {
        "examples": [str(e) for e in data["examples"]],
        "analysis": str(data.get("analysis", "")),
        "updated_at": str(data.get("updated_at", "")),
    }


def split_examples(raw: str) -> list[str]:
    """붙여넣은 텍스트를 포스트 단위로 나눈다. 구분자: `---` 또는 빈 줄 2개+."""
    parts = re.split(r"\n\s*---+\s*\n|\n\s*\n", raw)
    return [p.strip() for p in parts if p.strip()]


def build_voice_block(max_examples: int = 3) -> str:
    """시스템 프롬프트에 붙일 보이스 카드 블록. 카드가 비었으면 빈 문자열."""
    card = load_voice_card()
    if not card["examples"]:
        return ""
    lines = ["\n\n# 계정 주인의 실제 목소리 (이 사람이 쓴 것처럼 들려야 한다)"]
    if card["analysis"]:
        lines.append(f"스타일 분석: {card['analysis']}")
    lines.append("실제 포스트 예시 (문체·리듬·어휘 감각만 흡수, 소재 복제 금지):")
    lines.extend(f"---\n{ex}" for ex in card["examples"][:max_examples])
    return "\n".join(lines) + "\n"
