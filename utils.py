import json
import re
from urllib.parse import quote


def generate_tweet_intent_url(text: str) -> str:
    encoded = quote(text, safe="")
    return f"https://twitter.com/intent/tweet?text={encoded}"


def generate_follow_url(username: str) -> str:
    clean = username.lstrip("@")
    return f"https://twitter.com/intent/follow?screen_name={clean}"


def parse_grok_json(response_text: str) -> dict:
    if not response_text or not response_text.strip():
        return {"error": "빈 응답입니다"}
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "JSON 파싱 실패", "raw": response_text}


def parse_thread_text(raw_text: str) -> list[str]:
    text = raw_text.replace("\r\n", "\n")
    parts = re.split(r"\n\s*---\s*\n|\n{3,}", text)
    return [p.strip() for p in parts if p.strip()]


def append_viral_tag(text: str, tag: str) -> str:
    text = text.strip()
    tag = tag.strip()
    if not tag:
        return text
    return f"{text}\n\n{tag}"
