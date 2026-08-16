"""근거 기반 팁의 입력·출처·카드 검증 테스트."""

from __future__ import annotations

from grounded_tips import (
    GroundedTipRequest,
    TIP_CATEGORIES,
    normalize_url,
    validate_generated_ideas,
    validate_request,
    validate_research_packet,
)


def _source(url: str, **overrides: str) -> dict[str, str]:
    source = {
        "title": "Official source",
        "url": url,
        "publisher": "Publisher",
        "published_at": "2026-08-16",
        "excerpt": "Evidence",
    }
    source.update(overrides)
    return source


def _packet(*urls: str) -> dict:
    return {
        "facts": [{"statement": "검증된 사실", "source_urls": list(urls)}],
        "sources": [_source(url) for url in urls],
    }


class TestGroundedTipRequest:
    def test_supported_categories_are_stable(self):
        assert TIP_CATEGORIES == ("daily", "health", "finance", "it_builder")

    def test_general_public_requests_are_allowed(self):
        assert validate_request(GroundedTipRequest("직장인 수면 습관", "health")) is None
        assert validate_request(GroundedTipRequest("금융사기 예방법", "finance")) is None
        assert validate_request(GroundedTipRequest("브라우저 탭 정리", "daily")) is None
        assert validate_request(GroundedTipRequest("배포 체크리스트", "it_builder")) is None

    def test_rejects_invalid_category_and_empty_keywords(self):
        assert validate_request(GroundedTipRequest("주제", "unknown")) == "invalid_grounded_tip_request"
        assert validate_request(GroundedTipRequest("   ", "daily")) == "invalid_grounded_tip_request"

    def test_rejects_individual_health_and_finance_decisions(self):
        assert validate_request(GroundedTipRequest("혈압약 복용량", "health")) == "unsafe_personalized_request"
        assert validate_request(GroundedTipRequest("내 증상 진단", "health")) == "unsafe_personalized_request"
        assert validate_request(GroundedTipRequest("내 보유주식 매도", "finance")) == "unsafe_personalized_request"
        assert validate_request(GroundedTipRequest("매수할 종목", "finance")) == "unsafe_personalized_request"


class TestResearchPacket:
    def test_requires_two_distinct_source_hosts(self):
        packet = _packet("https://a.gov/one", "https://a.gov/two")
        assert validate_research_packet(packet)["error"] == "insufficient_sources"

    def test_returns_normalized_two_host_packet(self):
        packet = _packet("HTTPS://WHO.INT/sleep/", "https://cdc.gov/sleep")
        result = validate_research_packet(packet)
        assert "error" not in result
        assert {source["url"] for source in result["sources"]} == {
            "https://who.int/sleep",
            "https://cdc.gov/sleep",
        }

    def test_rejects_malformed_or_incomplete_sources(self):
        packet = _packet("https://who.int/sleep", "https://cdc.gov/sleep")
        packet["sources"][1] = _source("not a URL", excerpt="")
        assert validate_research_packet(packet)["error"] == "insufficient_sources"

    def test_deduplicates_equivalent_source_urls(self):
        packet = {
            "facts": [{
                "statement": "검증된 사실",
                "source_urls": ["https://who.int/sleep/", "https://who.int/sleep"],
            }],
            "sources": [
                _source("https://who.int/sleep/"),
                _source("https://who.int/sleep"),
            ],
        }
        result = validate_research_packet(packet)
        assert result["error"] == "insufficient_sources"

    def test_rejects_fact_with_source_outside_collected_sources(self):
        packet = _packet("https://who.int/sleep", "https://cdc.gov/sleep")
        packet["facts"][0]["source_urls"] = ["https://untrusted.example/note"]
        assert validate_research_packet(packet)["error"] == "insufficient_sources"


class TestGeneratedIdeas:
    def test_user_reference_is_not_automatically_evidence(self):
        response = validate_generated_ideas(
            [{"content": "본문", "evidence_urls": ["https://user.example/note"]}],
            {"https://who.int/sleep", "https://cdc.gov/sleep"},
        )
        assert response["error"] == "unverified_evidence"

    def test_rejects_empty_content_or_evidence(self):
        verified = {"https://who.int/sleep", "https://cdc.gov/sleep"}
        assert validate_generated_ideas([{"content": "", "evidence_urls": list(verified)}], verified)["error"] == "unverified_evidence"
        assert validate_generated_ideas([{"content": "본문", "evidence_urls": []}], verified)["error"] == "unverified_evidence"

    def test_accepts_only_verified_evidence_and_deduplicates_urls(self):
        verified = {"https://who.int/sleep", "https://cdc.gov/sleep"}
        result = validate_generated_ideas(
            [{
                "title": "수면 팁",
                "content": "본문",
                "evidence_urls": ["https://who.int/sleep/", "https://who.int/sleep"],
            }],
            verified,
        )
        assert "error" not in result
        assert result["ideas"][0]["evidence_urls"] == ["https://who.int/sleep"]


def test_normalize_url_removes_fragment_and_trailing_slash():
    assert normalize_url(" HTTPS://Example.COM/path/#section ") == "https://example.com/path"
