"""과거 글 아카이브(content_queue/my_posts.json) 갱신 — X API 로 새 글·답글만 받아 합친다.

입장 근거(stance_archive)와 답글 말투 예시가 이 파일을 읽는다. 한 번 내려받은 채로
두면 낡으므로 매일 마지막으로 받은 글 이후(since_id)만 가져와 덧붙인다.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

import publisher
import stance_archive

API = "https://api.x.com/2"
FIELDS = "created_at,public_metrics,referenced_tweets,note_tweet,edit_history_tweet_ids"


def _auth(env: dict) -> OAuth1:
    return OAuth1(env["X_API_KEY"], env["X_API_KEY_SECRET"], env["X_ACCESS_TOKEN"], env["X_ACCESS_TOKEN_SECRET"])


def merge(existing: list[dict], fetched: list[dict]) -> list[dict]:
    """id 로 중복을 빼고 최신순으로. 긴 글은 note_tweet 본문을 text 로 쓴다."""
    by_id = {str(r.get("id")): r for r in existing if isinstance(r, dict) and r.get("id")}
    for row in fetched:
        row = dict(row)
        note = (row.get("note_tweet") or {}).get("text")
        if note:
            row["text"] = note
        by_id[str(row["id"])] = row
    return sorted(by_id.values(), key=lambda r: int(r["id"]), reverse=True)


def fetch_new(env: dict, since_id: str | None, *, session=requests) -> list[dict]:
    auth = _auth(env)
    me = session.get(f"{API}/users/me", auth=auth, timeout=30)
    me.raise_for_status()
    user_id = me.json()["data"]["id"]
    params = {"max_results": 100, "tweet.fields": FIELDS, "exclude": "retweets"}
    if since_id:
        params["since_id"] = since_id
    rows: list[dict] = []
    for _ in range(32):  # 타임라인 API 한도(최근 3200개)
        r = session.get(f"{API}/users/{user_id}/tweets", params=params, auth=auth, timeout=30)
        r.raise_for_status()
        body = r.json()
        rows.extend(body.get("data") or [])
        token = (body.get("meta") or {}).get("next_token")
        if not token:
            break
        params["pagination_token"] = token
    return rows


def refresh(path: Path | None = None, *, env: dict | None = None, session=requests) -> dict:
    target = stance_archive.ARCHIVE_PATH if path is None else path
    env = env if env is not None else publisher.load_env()
    if not all(env.get(k) for k in ("X_API_KEY", "X_API_KEY_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")):
        return {"error": "x_api_not_configured"}
    try:
        existing = json.loads(target.read_text(encoding="utf-8")) if target.is_file() else []
    except (OSError, json.JSONDecodeError):
        existing = []
    since_id = max((str(r["id"]) for r in existing if r.get("id")), key=int, default=None)
    fetched = fetch_new(env, since_id, session=session)
    merged = merge(existing, fetched)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)
    os.replace(tmp, target)
    return {"added": len(merged) - len(existing), "total": len(merged)}
