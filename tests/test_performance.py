"""X 애널리틱스 CSV 파싱 + 성과 요약 + 수익화 진행률 계산 테스트."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from utils import (
    MONETIZATION_IMPRESSIONS_TARGET,
    parse_analytics_csv,
    summarize_performance,
)
from demo_data import SAMPLE_ANALYTICS_CSV


NOW = datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc)


ENGLISH_CSV = """\
"Tweet id","Tweet permalink","Tweet text","time","impressions","engagements","engagement rate","retweets","replies","likes","bookmarks"
"1","https://x.com/u/status/1","첫 포스트입니다","2026-06-20 09:00 +0000","12500","430","0.0344","12","8","210","45"
"2","https://x.com/u/status/2","두 번째 포스트","2026-06-25 21:00 +0000","3400","80","0.0235","2","1","40","9"
"3","https://x.com/u/status/3","오래된 포스트","2026-01-05 10:00 +0000","9000","300","0.0333","5","3","150","20"
"""

KOREAN_CSV = """\
포스트 텍스트,날짜,노출수,좋아요,답글,재게시,북마크
"한국어 헤더 포스트",2026-07-01,1500,30,5,2,4
"""

MINIMAL_CSV = """\
text,impressions
"날짜 없는 포스트",700
"""


class TestParseAnalyticsCsv:
    def test_parses_english_export(self):
        posts = parse_analytics_csv(ENGLISH_CSV)
        assert len(posts) == 3
        first = posts[0]
        assert first["text"] == "첫 포스트입니다"
        assert first["impressions"] == 12500
        assert first["likes"] == 210
        assert first["replies"] == 8
        assert first["reposts"] == 12
        assert first["bookmarks"] == 45
        assert first["engagements"] == 430
        assert first["time"] is not None

    def test_parses_korean_headers(self):
        posts = parse_analytics_csv(KOREAN_CSV)
        assert len(posts) == 1
        assert posts[0]["impressions"] == 1500
        assert posts[0]["reposts"] == 2
        assert posts[0]["time"] is not None

    def test_minimal_columns_ok(self):
        posts = parse_analytics_csv(MINIMAL_CSV)
        assert len(posts) == 1
        assert posts[0]["impressions"] == 700
        assert posts[0]["time"] is None

    def test_numbers_with_commas(self):
        posts = parse_analytics_csv('text,impressions\n"a","1,234,567"\n')
        assert posts[0]["impressions"] == 1234567

    def test_missing_impressions_column_returns_empty(self):
        assert parse_analytics_csv("foo,bar\n1,2\n") == []

    def test_garbage_returns_empty(self):
        assert parse_analytics_csv("") == []

    def test_sample_csv_parses(self):
        posts = parse_analytics_csv(SAMPLE_ANALYTICS_CSV)
        assert len(posts) >= 5
        assert all(p["impressions"] > 0 for p in posts)
        assert all(p["time"] is not None for p in posts)


class TestSummarizePerformance:
    def test_totals_and_recent_window(self):
        posts = parse_analytics_csv(ENGLISH_CSV)
        summary = summarize_performance(posts, now=NOW)

        assert summary["total_posts"] == 3
        assert summary["total_impressions"] == 12500 + 3400 + 9000
        # 90일 창: 1월 포스트는 제외
        assert summary["recent_impressions"] == 12500 + 3400
        assert summary["has_dates"] is True

    def test_progress_and_estimate(self):
        posts = parse_analytics_csv(ENGLISH_CSV)
        summary = summarize_performance(posts, now=NOW)

        expected_pct = (12500 + 3400) / MONETIZATION_IMPRESSIONS_TARGET * 100
        assert abs(summary["monetization_pct"] - expected_pct) < 0.01
        assert summary["daily_avg_impressions"] > 0
        assert summary["est_days_to_target"] > 0

    def test_engagement_rate_from_engagements(self):
        posts = parse_analytics_csv(ENGLISH_CSV)
        summary = summarize_performance(posts, now=NOW)
        expected = (430 + 80 + 300) / (12500 + 3400 + 9000) * 100
        assert abs(summary["avg_engagement_pct"] - expected) < 0.01

    def test_engagement_rate_fallback_without_engagements(self):
        posts = parse_analytics_csv(KOREAN_CSV)
        summary = summarize_performance(posts, now=NOW)
        expected = (30 + 5 + 2 + 4) / 1500 * 100
        assert abs(summary["avg_engagement_pct"] - expected) < 0.01

    def test_undated_posts_count_as_recent(self):
        posts = parse_analytics_csv(MINIMAL_CSV)
        summary = summarize_performance(posts, now=NOW)
        assert summary["has_dates"] is False
        assert summary["recent_impressions"] == 700

    def test_top_and_bottom_posts(self):
        posts = parse_analytics_csv(ENGLISH_CSV)
        summary = summarize_performance(posts, now=NOW)
        assert summary["top_posts"][0]["impressions"] == 12500
        assert summary["bottom_posts"][0]["impressions"] == 3400

    def test_empty_posts(self):
        summary = summarize_performance([], now=NOW)
        assert summary["total_posts"] == 0
        assert summary["monetization_pct"] == 0
        assert summary["est_days_to_target"] is None


class _FakeProvider:
    supports_curator = False

    def __init__(self):
        self.last_call = None

    def generate_json(self, system_prompt, user_prompt, **kwargs):
        self.last_call = (system_prompt, user_prompt)
        return {"summary": "ok"}


class TestAnalyzePerformance:
    def test_sends_summary_and_posts_to_provider(self):
        from grok_client import GrokClient

        provider = _FakeProvider()
        grok = GrokClient(provider=provider)
        posts = parse_analytics_csv(ENGLISH_CSV)
        summary = summarize_performance(posts, now=NOW)

        result = grok.analyze_performance(summary)

        assert result == {"summary": "ok"}
        system_prompt, user_prompt = provider.last_call
        assert "먹히는 패턴" in system_prompt
        assert "최근 90일 노출: 15,900" in user_prompt
        assert "첫 포스트입니다" in user_prompt  # 상위 포스트 인용
        assert "[하위 포스트]" in user_prompt


def test_perf_i18n_keys_cover_all_languages():
    from i18n import _T, LANGUAGES

    keys = [k for k in _T if k.startswith("perf_")] + ["tab_performance"]
    assert len(keys) > 20
    for key in keys:
        assert set(_T[key]) >= set(LANGUAGES), f"missing translations for {key}"
