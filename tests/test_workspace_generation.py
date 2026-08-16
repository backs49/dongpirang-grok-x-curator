"""방향 먼저 고르고 한 편만 쓰는 워크스페이스 생성 흐름의 계약 테스트."""

from __future__ import annotations

from grok_client import GrokClient


class FakeProvider:
    name = "Fake CLI"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate_json(self, system_prompt, user_prompt, **kwargs):
        self.calls.append((system_prompt, user_prompt))
        return next(self.responses)


class FakeGroundedProvider(FakeProvider):
    """조사 호출과 작성 호출을 분리해 캡처하는 근거 기반 포스트용 페이크."""

    name = "Fake Grok CLI"

    def __init__(self, responses, research):
        super().__init__(responses)
        self.research_result = research
        self.research_calls = []

    def research_json(self, system_prompt, user_prompt, **kwargs):
        self.research_calls.append((system_prompt, user_prompt))
        return self.research_result


def _direction(**overrides):
    direction = {"title": "A", "hook": "h", "angle": "a", "core_message": "m"}
    direction.update(overrides)
    return direction


def _directions(count):
    return {"directions": [
        {
            "title": f"t{i}",
            "hook": f"h{i}",
            "angle": f"a{i}",
            "core_message": f"m{i}",
        }
        for i in range(count)
    ]}


def _source(url):
    return {
        "title": "Official",
        "url": url,
        "publisher": "Publisher",
        "published_at": "2026-08-16",
        "excerpt": "Evidence",
    }


def _research(*urls):
    return {
        "facts": [{"statement": "검증된 사실", "source_urls": list(urls)}],
        "sources": [_source(url) for url in urls],
    }


def test_generate_directions_returns_exactly_three_compact_cards():
    provider = FakeProvider([{"directions": [
        {"title": "A", "hook": "h1", "angle": "a1", "core_message": "m1"},
        {"title": "B", "hook": "h2", "angle": "a2", "core_message": "m2"},
        {"title": "C", "hook": "h3", "angle": "a3", "core_message": "m3"},
    ]}])
    result = GrokClient(provider=provider).generate_directions(
        "사이드 프로젝트 배포 실수", mode="builder_note", language="ko"
    )
    assert result["directions"][1]["title"] == "B"
    assert "완성된 포스트" not in provider.calls[0][0]


def test_write_post_uses_only_the_selected_direction():
    provider = FakeProvider([{"post": {"title": "A", "content": "완성 글"}}])
    result = GrokClient(provider=provider).write_post(
        keywords="배포 실수",
        direction={"title": "A", "hook": "h", "angle": "a", "core_message": "m"},
        length=280,
        mode="builder_note",
        language="ko",
    )
    assert result["post"]["content"] == "완성 글"
    assert "배포 실수" in provider.calls[0][1]
    assert "core_message" in provider.calls[0][1]


class TestGenerateDirections:
    def test_rejects_two_cards(self):
        provider = FakeProvider([_directions(2)])

        result = GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_directions"}

    def test_rejects_four_cards(self):
        provider = FakeProvider([_directions(4)])

        result = GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_directions"}

    def test_rejects_card_with_missing_field(self):
        payload = _directions(3)
        del payload["directions"][1]["angle"]
        provider = FakeProvider([payload])

        result = GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_directions"}

    def test_rejects_card_with_blank_field(self):
        payload = _directions(3)
        payload["directions"][2]["core_message"] = "   "
        provider = FakeProvider([payload])

        result = GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_directions"}

    def test_passes_provider_error_through(self):
        provider = FakeProvider([{"error": "API 오류"}])

        result = GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        assert result == {"error": "API 오류"}

    def test_prompt_forbids_post_body_image_and_cta(self):
        provider = FakeProvider([_directions(3)])

        GrokClient(provider=provider).generate_directions(
            "배포 실수", mode="builder_note", language="ko"
        )

        system = provider.calls[0][0]
        assert "이미지 프롬프트" in system
        assert "출처 URL" in system
        assert "행동 유도(CTA)" in system

    def test_english_language_instruction_is_explicit(self):
        provider = FakeProvider([_directions(3)])

        GrokClient(provider=provider).generate_directions(
            "deploy mistakes", mode="builder_note", language="en"
        )

        assert "ENGLISH" in provider.calls[0][0]


class TestWritePost:
    def test_rejects_blank_post_content(self):
        provider = FakeProvider([{"post": {"title": "A", "content": "   "}}])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_post"}

    def test_rejects_missing_post_object(self):
        provider = FakeProvider([{"posts": []}])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert result == {"error": "invalid_post"}

    def test_rejects_incomplete_direction_without_calling_provider(self):
        provider = FakeProvider([{"post": {"content": "쓰이면 안 되는 글"}}])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수",
            direction=_direction(core_message=""),
            length=280,
            mode="builder_note",
            language="ko",
        )

        assert result == {"error": "invalid_direction"}
        assert provider.calls == []

    def test_length_and_mode_reach_the_writer_prompt(self):
        provider = FakeProvider([{"post": {"title": "A", "content": "완성 글"}}])

        GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        system = provider.calls[0][0]
        assert "280자" in system
        assert "빌더 노트" in system  # builder_note 모드 카드 라벨


class TestWriteGroundedPost:
    def test_returns_one_verified_post_with_source_metadata(self):
        provider = FakeGroundedProvider(
            [{"post": {
                "title": "수면 팁",
                "content": "본문이다.",
                "evidence_urls": ["https://who.int/a"],
            }}],
            research=_research("https://who.int/a", "https://cdc.gov/b"),
        )

        result = GrokClient(provider=provider).write_grounded_post(
            keywords="수면 습관",
            direction=_direction(),
            category="health",
            references="https://user.example/note",
            length=280,
            mode="builder_note",
            language="ko",
        )

        assert result["post"]["content"] == "본문이다."
        assert result["post"]["sources"] == [_source("https://who.int/a")]
        assert result["topic_category"] == "health"
        assert result["verified_at"]
        assert len(provider.research_calls) == 1
        assert "user.example" in provider.research_calls[0][1]
        assert "user.example" not in provider.calls[0][1]
        assert "core_message" in provider.calls[0][1]

    def test_rejects_evidence_url_not_returned_by_web_tool(self):
        provider = FakeGroundedProvider(
            [{"post": {"content": "본문", "evidence_urls": ["https://user.example/note"]}}],
            research=_research("https://who.int/a", "https://cdc.gov/b"),
        )

        result = GrokClient(provider=provider).write_grounded_post(
            keywords="수면 습관",
            direction=_direction(),
            category="health",
            length=280,
            mode="builder_note",
            language="ko",
        )

        assert result == {"error": "unverified_evidence"}

    def test_rejects_insufficient_research_before_writing(self):
        provider = FakeGroundedProvider(
            [{"post": {"content": "본문", "evidence_urls": ["https://who.int/a"]}}],
            research=_research("https://who.int/a", "https://who.int/b"),
        )

        result = GrokClient(provider=provider).write_grounded_post(
            keywords="수면 습관",
            direction=_direction(),
            category="health",
            mode="builder_note",
            language="ko",
        )

        assert result == {"error": "insufficient_sources"}
        assert provider.calls == []

    def test_rejects_unsafe_personalized_request_without_provider_calls(self):
        provider = FakeGroundedProvider([], research=_research("https://who.int/a"))

        result = GrokClient(provider=provider).write_grounded_post(
            keywords="내 보유주식 매도",
            direction=_direction(),
            category="finance",
            mode="builder_note",
            language="ko",
        )

        assert result == {"error": "unsafe_personalized_request"}
        assert provider.research_calls == []
        assert provider.calls == []

    def test_requires_grok_cli_research_transport(self):
        provider = FakeProvider([])

        result = GrokClient(provider=provider).write_grounded_post(
            keywords="수면 습관",
            direction=_direction(),
            category="health",
            mode="builder_note",
            language="ko",
        )

        assert result == {"error": "grounded_tips_require_grok_cli"}
        assert provider.calls == []


def test_research_runs_only_for_grounded_posts():
    provider = FakeGroundedProvider(
        [_directions(3), {"post": {"title": "A", "content": "완성 글"}}],
        research=_research("https://who.int/a", "https://cdc.gov/b"),
    )
    client = GrokClient(provider=provider)

    client.generate_directions("수면 습관", mode="builder_note", language="ko")
    client.write_post(
        keywords="수면 습관", direction=_direction(), length=280, mode="builder_note", language="ko"
    )

    assert provider.research_calls == []


class TestOptimizePostLanguage:
    def test_explicit_language_overrides_session_default(self):
        provider = FakeProvider([{"score": 90}])

        GrokClient(provider=provider).optimize_post("본문", language="en")

        assert "ENGLISH" in provider.calls[0][0]

    def test_default_language_keeps_current_behavior(self):
        from i18n import get_lang_instruction
        from xalgo_prompts import NATURAL_STYLE_GUIDE, OPTIMIZER_SYSTEM_PROMPT

        provider = FakeProvider([{"score": 90}, {"score": 90}])
        client = GrokClient(provider=provider)

        client.optimize_post("본문")
        client.optimize_post("본문", language=None)

        expected = OPTIMIZER_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + get_lang_instruction()
        assert provider.calls[0][0] == expected
        assert provider.calls[1][0] == expected
