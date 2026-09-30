"""2026-09-29 X 알고리즘 변경 후속(후킹 모드, 상세 보기, 관심 없음 리스크)."""

import writing_modes
from utils import parse_analytics_csv, summarize_performance
from xalgo_prompts import PERFORMANCE_SYSTEM_PROMPT, RISK_CHECK_SYSTEM_PROMPT


def test_hook_mode_requires_body_to_pay_off():
    rules = writing_modes.WRITING_MODES["hook"]["rules"]
    assert "본문이 반드시 갚는다" in rules
    assert "낚시 제목처럼 굴되" not in rules


def test_detail_expands_parsed_and_summarized():
    csv_text = (
        "Post text,Date,Impressions,Engagements,Likes,Detail Expands\n"
        "a,2026-09-30,1000,50,10,120\n"
        "b,2026-09-29,500,5,1,10\n"
    )
    posts = parse_analytics_csv(csv_text)
    assert posts[0]["detail_expands"] == 120
    summary = summarize_performance(posts)
    assert summary["has_detail"] is True
    assert round(summary["avg_detail_pct"], 2) == 8.67
    assert round(summary["top_posts"][0]["detail_pct"], 1) == 12.0


def test_csv_without_detail_column_keeps_old_shape():
    posts = parse_analytics_csv("Post text,Impressions\na,100\n")
    summary = summarize_performance(posts)
    assert summary["has_detail"] is False
    assert "detail_pct" not in summary["top_posts"][0]


def test_risk_and_performance_prompts_cover_new_signals():
    assert "관심 없음" in RISK_CHECK_SYSTEM_PROMPT
    assert "참여 구걸" in RISK_CHECK_SYSTEM_PROMPT
    assert "상세 보기" in PERFORMANCE_SYSTEM_PROMPT
