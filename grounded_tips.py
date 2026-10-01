"""근거 기반 팁의 입력·출처·생성 결과를 검증하는 순수 정책 경계.

여기서는 네트워크나 모델을 호출하지 않는다. 외부 도구가 모은 연구 패킷과
모델이 작성한 카드가 다음 단계로 넘어가기 전에, 출처와 안전 규칙을 한 곳에서
일관되게 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit


CONTENT_TYPE_IDEAS = "ideas"
CONTENT_TYPE_GROUNDED_TIP = "grounded_tip"
TIP_CATEGORIES = ("daily", "health", "finance", "it_builder")


@dataclass(frozen=True)
class GroundedTipRequest:
    """사용자가 요청한 공공 정보형 팁의 최소 입력값."""

    keywords: str
    category: str
    references: str = ""


def normalize_url(url: str) -> str:
    """비교에 쓸 HTTP(S) URL을 정규화한다.

    fragment와 끝 슬래시는 문서의 실제 출처를 구분하지 않으므로 제거한다.
    query string은 서로 다른 자료를 가리킬 수 있어 유지한다.
    """
    parsed = urlsplit((url or "").strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((scheme, parsed.netloc.lower(), path, parsed.query, ""))


def source_host(url: str) -> str:
    """정규화된 URL의 호스트명. 포트는 독립 출처로 취급하지 않는다."""
    return (urlsplit(normalize_url(url)).hostname or "").lower()


def validate_request(request: GroundedTipRequest) -> str | None:
    """공공 팁 범위를 벗어난 요청이면 사용자에게 보여줄 오류 키를 반환한다."""
    if request.category not in TIP_CATEGORIES or not request.keywords.strip():
        return "invalid_grounded_tip_request"

    text = f"{request.keywords} {request.references}".casefold()
    health_risk_terms = (
        "증상",
        "진단",
        "복용량",
        "용량",
        "처방",
        "약을 먹",
        "약 먹",
        "약물 치료",
        "medication",
        "dosage",
        "diagnosis",
        "symptom",
        "prescription",
    )
    finance_risk_terms = (
        "보유주식",
        "보유 주식",
        "내 주식",
        "내 종목",
        "매수",
        "매도",
        "포트폴리오",
        "자산배분",
        "buy",
        "sell",
        "allocation",
        "holding",
        "portfolio",
    )
    if request.category == "health" and any(term in text for term in health_risk_terms):
        return "unsafe_personalized_request"
    if request.category == "finance" and any(term in text for term in finance_risk_terms):
        return "unsafe_personalized_request"
    return None


def _normalized_source(raw_source: Any) -> dict[str, str] | None:
    if not isinstance(raw_source, dict):
        return None
    url = raw_source.get("url")
    normalized_url = normalize_url(url) if isinstance(url, str) else ""
    if not normalized_url:
        return None
    # 2026-10 Grok CLI 의 검색 결과는 URL 만 싣는다. 제목이 없으면 도메인으로 대신한다.
    title = raw_source.get("title")
    excerpt = raw_source.get("excerpt")
    title = title.strip() if isinstance(title, str) and title.strip() else source_host(normalized_url)
    excerpt = excerpt if isinstance(excerpt, str) else ""
    return {
        "title": title,
        "url": normalized_url,
        "publisher": str(raw_source.get("publisher") or "").strip(),
        "published_at": str(raw_source.get("published_at") or "").strip(),
        "excerpt": excerpt.strip(),
    }


def validate_research_packet(packet: Any) -> dict[str, Any]:
    """연구 결과가 독립된 두 출처와 추적 가능한 사실을 갖췄는지 확인한다."""
    if not isinstance(packet, dict):
        return {"error": "insufficient_sources"}

    raw_sources = packet.get("sources")
    raw_facts = packet.get("facts")
    if not isinstance(raw_sources, list) or not isinstance(raw_facts, list) or not raw_facts:
        return {"error": "insufficient_sources"}

    sources_by_url: dict[str, dict[str, str]] = {}
    for raw_source in raw_sources:
        source = _normalized_source(raw_source)
        if source is not None:
            sources_by_url.setdefault(source["url"], source)

    if len({source_host(url) for url in sources_by_url}) < 2:
        return {"error": "insufficient_sources"}

    # 도구가 실제로 열어 본 URL 을 인용한 사실만 남긴다. 예전에는 사실 하나라도 못 연
    # URL 을 인용하면 조사 전체를 버려서, 멀쩡한 사실까지 잃고 자주 실패했다.
    normalized_facts: list[dict[str, Any]] = []
    for raw_fact in raw_facts:
        if not isinstance(raw_fact, dict):
            continue
        statement = raw_fact.get("statement")
        raw_urls = raw_fact.get("source_urls")
        if not isinstance(statement, str) or not statement.strip() or not isinstance(raw_urls, list):
            continue
        fact_urls: list[str] = []
        for raw_url in raw_urls:
            normalized_url = normalize_url(raw_url) if isinstance(raw_url, str) else ""
            if normalized_url in sources_by_url and normalized_url not in fact_urls:
                fact_urls.append(normalized_url)
        if fact_urls:
            normalized_facts.append({"statement": statement.strip(), "source_urls": fact_urls})

    cited = {url for fact in normalized_facts for url in fact["source_urls"]}
    if not normalized_facts or len({source_host(url) for url in cited}) < 2:
        return {"error": "insufficient_sources"}
    sources_by_url = {url: src for url, src in sources_by_url.items() if url in cited}

    return {"facts": normalized_facts, "sources": list(sources_by_url.values())}


def validate_generated_ideas(ideas: Any, verified_urls: set[str]) -> dict[str, Any]:
    """카드가 연구 도구가 실제 반환한 출처만 인용하는지 검증한다."""
    if not isinstance(ideas, list) or not ideas:
        return {"error": "unverified_evidence"}

    normalized_verified = {normalize_url(url) for url in verified_urls if normalize_url(url)}
    normalized_ideas: list[dict[str, Any]] = []
    for raw_idea in ideas:
        if not isinstance(raw_idea, dict):
            return {"error": "unverified_evidence"}
        content = raw_idea.get("content")
        raw_evidence_urls = raw_idea.get("evidence_urls")
        if not isinstance(content, str) or not content.strip() or not isinstance(raw_evidence_urls, list):
            return {"error": "unverified_evidence"}

        evidence_urls: list[str] = []
        for raw_url in raw_evidence_urls:
            normalized_url = normalize_url(raw_url) if isinstance(raw_url, str) else ""
            if not normalized_url or normalized_url not in normalized_verified:
                return {"error": "unverified_evidence"}
            if normalized_url not in evidence_urls:
                evidence_urls.append(normalized_url)
        if not evidence_urls:
            return {"error": "unverified_evidence"}

        idea = dict(raw_idea)
        idea["content"] = content.strip()
        idea["evidence_urls"] = evidence_urls
        normalized_ideas.append(idea)

    return {"ideas": normalized_ideas}


def validate_generated_post(post: Any, verified_urls: set[str]) -> dict[str, Any]:
    """한 편짜리 포스트에도 카드와 똑같은 출처 규칙을 적용한다."""
    result = validate_generated_ideas([post], verified_urls)
    if "error" in result:
        return result
    return {"post": result["ideas"][0]}
