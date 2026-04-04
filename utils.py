import json
import re
from urllib.parse import quote


def generate_tweet_intent_url(text: str) -> str:
    encoded = quote(text, safe="")
    return f"https://twitter.com/intent/tweet?text={encoded}"


def generate_search_url(query: str) -> str:
    encoded = quote(query, safe="")
    return f"https://x.com/search?q={encoded}&src=typed_query"


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
    parts = re.split(r"\n\s*---\s*\n|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]


def parse_followers_file(uploaded_file) -> set[str]:
    """Parse followers.js or CSV file, return set of identifiers."""
    content = uploaded_file.getvalue().decode("utf-8")
    name = uploaded_file.name.lower()

    if name.endswith(".js"):
        match = re.search(r"=\s*(\[.*\])", content, re.DOTALL)
        if not match:
            return set()
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return set()
        ids = set()
        for item in data:
            inner = item.get("follower") or item.get("following") or {}
            aid = inner.get("accountId", "")
            if aid:
                ids.add(aid)
        return ids

    if name.endswith(".csv"):
        import csv
        import io

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return set()
        col_map = {c.lower().strip(): c for c in reader.fieldnames}
        target = None
        for key in ["username", "handle", "user_name", "screen_name", "screenname", "user"]:
            if key in col_map:
                target = col_map[key]
                break
        if not target:
            for key in ["accountid", "account_id", "id", "user_id", "userid"]:
                if key in col_map:
                    target = col_map[key]
                    break
        if not target:
            return set()
        ids = set()
        for row in reader:
            val = row.get(target, "").strip()
            if val:
                ids.add(val.lstrip("@").lower())
        return ids

    return set()


def compare_followers(previous: set[str], current: set[str]) -> dict:
    """Compare two follower sets and return differences."""
    return {
        "unfollowed": sorted(previous - current),
        "new_followers": sorted(current - previous),
        "unchanged": sorted(previous & current),
    }


def append_viral_tag(text: str, tag: str) -> str:
    text = text.strip()
    tag = tag.strip()
    if not tag:
        return text
    return f"{text}\n\n{tag}"
