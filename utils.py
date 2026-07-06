from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# X 크리에이터 수익 공유 요건: 최근 3개월 유기적 노출 500만 회
MONETIZATION_IMPRESSIONS_TARGET = 5_000_000
RECENT_WINDOW_DAYS = 90

# X 애널리틱스 CSV 헤더 별칭 (영문 공식 내보내기 + 한국어 변형)
_ANALYTICS_COLUMN_ALIASES = {
    "text": ("tweet text", "post text", "text", "포스트 텍스트", "트윗 텍스트", "본문"),
    "time": ("time", "date", "created at", "시간", "날짜", "게시 시간"),
    "impressions": ("impressions", "노출수", "노출 수", "노출"),
    "engagements": ("engagements", "참여수", "참여 수", "참여"),
    "likes": ("likes", "좋아요"),
    "replies": ("replies", "답글"),
    "reposts": ("retweets", "reposts", "재게시", "리포스트"),
    "bookmarks": ("bookmarks", "북마크"),
}

_TIME_FORMATS = (
    "%Y-%m-%d %H:%M %z",
    "%Y-%m-%d %H:%M:%S %z",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
)


def generate_tweet_intent_url(text: str) -> str:
    encoded = quote(text, safe="")
    return f"https://x.com/intent/post?text={encoded}"


def generate_search_url(query: str) -> str:
    encoded = quote(query, safe="")
    return f"https://x.com/search?q={encoded}&src=typed_query"


def generate_follow_url(username: str) -> str:
    clean = username.lstrip("@")
    return f"https://x.com/intent/follow?screen_name={clean}"


_GROK_CITATION_RE = re.compile(
    r"<grok:render\b[^>]*?(?:/>|>.*?</grok:render>)",
    re.DOTALL,
)

_HANGUL_RE = re.compile(r"[\uAC00-\uD7AF]")


def contains_hangul(text: str) -> bool:
    """문자열에 한글 음절이 포함되어 있는지 검사한다."""
    if not text:
        return False
    return bool(_HANGUL_RE.search(text))


def strip_grok_citations(text: str) -> str:
    """Grok Live Search가 응답에 끼워 넣는 `<grok:render>` 인용 마크업을 제거한다.
    Grok UI에서만 렌더되는 태그인데 JSON 값에 그대로 새어나와 사용자에게 노출되는
    현상이 있어, 파싱 전 단계에서 일괄 제거한다."""
    if not text:
        return text
    return _GROK_CITATION_RE.sub("", text)


def parse_grok_json(response_text: str) -> dict:
    if not response_text or not response_text.strip():
        return {"error": "빈 응답입니다"}
    text = strip_grok_citations(response_text).strip()
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


def _parse_analytics_time(value: str):
    """애널리틱스 CSV 의 시간 문자열을 datetime 으로. 실패하면 None."""
    value = (value or "").strip()
    if not value:
        return None
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_metric(value) -> int:
    """"1,234" / "1234.0" / 빈 값 등을 관대하게 정수로 변환."""
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def parse_analytics_csv(content: str) -> list[dict]:
    """X 애널리틱스 CSV 내보내기를 파싱한다.

    영문 공식 헤더와 한국어 변형을 별칭 매핑으로 흡수한다.
    impressions 열을 찾지 못하면 형식이 다른 파일로 보고 [] 를 돌려준다.
    """
    try:
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except csv.Error:
        return []
    if not rows or not reader.fieldnames:
        return []

    normalized = {name: (name or "").strip().lower() for name in reader.fieldnames}
    column_for: dict[str, str] = {}
    for field, aliases in _ANALYTICS_COLUMN_ALIASES.items():
        for original, lowered in normalized.items():
            if lowered in aliases:
                column_for[field] = original
                break

    if "impressions" not in column_for:
        return []

    posts = []
    for row in rows:
        impressions = _parse_metric(row.get(column_for["impressions"]))
        post = {
            "text": (row.get(column_for.get("text", ""), "") or "").strip(),
            "time": _parse_analytics_time(row.get(column_for.get("time", ""), "")),
            "impressions": impressions,
        }
        for field in ("engagements", "likes", "replies", "reposts", "bookmarks"):
            post[field] = _parse_metric(row.get(column_for.get(field, ""), ""))
        posts.append(post)
    return posts


def summarize_performance(posts: list[dict], now: datetime | None = None) -> dict:
    """파싱된 포스트 목록에서 수익화 진행률 대시보드용 요약을 만든다."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    window_start = now - timedelta(days=RECENT_WINDOW_DAYS)

    total_impressions = sum(p["impressions"] for p in posts)
    dated = [p for p in posts if p.get("time") is not None]
    has_dates = bool(dated)

    if has_dates:
        recent = []
        for p in dated:
            ts = p["time"]
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= window_start:
                recent.append(p)
        recent_impressions = sum(p["impressions"] for p in recent)
    else:
        # 날짜가 없으면 전체를 최근 성과로 간주하고 UI 에서 안내한다.
        recent_impressions = total_impressions

    total_engagements = sum(p.get("engagements", 0) for p in posts)
    if total_engagements == 0:
        total_engagements = sum(
            p.get("likes", 0) + p.get("replies", 0) + p.get("reposts", 0) + p.get("bookmarks", 0)
            for p in posts
        )
    avg_engagement_pct = (
        total_engagements / total_impressions * 100 if total_impressions else 0.0
    )

    monetization_pct = recent_impressions / MONETIZATION_IMPRESSIONS_TARGET * 100
    daily_avg = recent_impressions / RECENT_WINDOW_DAYS if recent_impressions else 0.0
    remaining = max(0, MONETIZATION_IMPRESSIONS_TARGET - recent_impressions)
    est_days = round(remaining / daily_avg) if daily_avg > 0 else None

    ranked = sorted(posts, key=lambda p: p["impressions"], reverse=True)

    def _brief(post: dict) -> dict:
        impressions = post["impressions"]
        engagements = post.get("engagements", 0) or (
            post.get("likes", 0) + post.get("replies", 0)
            + post.get("reposts", 0) + post.get("bookmarks", 0)
        )
        return {
            "text": post.get("text", ""),
            "impressions": impressions,
            "engagement_pct": engagements / impressions * 100 if impressions else 0.0,
        }

    return {
        "total_posts": len(posts),
        "total_impressions": total_impressions,
        "recent_impressions": recent_impressions,
        "has_dates": has_dates,
        "avg_engagement_pct": avg_engagement_pct,
        "monetization_pct": monetization_pct,
        "daily_avg_impressions": daily_avg,
        "est_days_to_target": est_days,
        "top_posts": [_brief(p) for p in ranked[:3]],
        "bottom_posts": [_brief(p) for p in ranked[::-1][:3] if p["impressions"] >= 0],
    }
