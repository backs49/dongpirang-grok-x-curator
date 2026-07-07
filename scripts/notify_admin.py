#!/usr/bin/env python3
"""관리자 1인에게만 텔레그램 메시지를 보내는 발송기.

ai-trader 의 notify_telegram.py 와 달리 **게스트 팬아웃이 없다** —
수신자는 .env 의 TELEGRAM_CHAT_ID(관리자) 단 한 명이며, 이 스크립트는
설계상 다른 chat_id 를 알지 못한다. TELEGRAM_GUEST_CHAT_IDS 류의 키는
읽지 않는다 (터널 URL 등 민감 정보가 게스트에게 새는 것을 방지).

사용:
    python scripts/notify_admin.py "보낼 메시지"
    echo "메시지" | python scripts/notify_admin.py

stdlib 만 사용. 실패 시 stderr 에 사유를 남기고 종료 코드 1.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from publisher import load_env  # noqa: E402


def send_to_admin(text: str) -> bool:
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_chat_id = env.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not admin_chat_id:
        print("notify_admin: TELEGRAM_BOT_TOKEN/CHAT_ID 미설정", file=sys.stderr)
        return False

    data = urllib.parse.urlencode(
        {"chat_id": admin_chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage", data=data
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except Exception as exc:
        print(f"notify_admin: 발송 실패: {type(exc).__name__}", file=sys.stderr)
        return False
    if not payload.get("ok"):
        print(f"notify_admin: API 거부: {payload.get('description')}", file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    text = " ".join(argv[1:]) if len(argv) > 1 else sys.stdin.read().strip()
    if not text:
        print("notify_admin: 보낼 메시지가 비어 있음", file=sys.stderr)
        return 1
    return 0 if send_to_admin(text) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
