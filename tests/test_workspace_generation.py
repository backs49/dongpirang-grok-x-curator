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

    def test_prompt_forbids_alternatives_and_media_instructions(self):
        provider = FakeProvider([{"post": {"title": "A", "content": "완성 글"}}])

        GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        system = provider.calls[0][0]
        assert "대안, 다른 버전, A/B 시안을 만들지 마세요" in system
        assert "이미지·영상 지시를 **절대 넣지 마세요**" in system
        # 모드 블록은 5개 아이디어 기준 문구라 개수·형식 우선순위를 못박아야 한다
        assert "아이디어 개수" in system


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

    def test_prompt_carries_safety_rules_evidence_and_mode_precedence(self):
        provider = FakeGroundedProvider(
            [{"post": {"content": "본문이다.", "evidence_urls": ["https://who.int/a"]}}],
            research=_research("https://who.int/a", "https://cdc.gov/b"),
        )

        GrokClient(provider=provider).write_grounded_post(
            keywords="수면 습관",
            direction=_direction(),
            category="health",
            length=280,
            mode="builder_note",
            language="ko",
        )

        system = provider.calls[0][0]
        assert "개인 진단, 증상 판단, 치료·약물·복용량" in system
        assert "특정 종목 추천, 매수·매도, 자산 배분을 제안하지 않는다" in system
        assert "`evidence_urls`에는 최소 하나가 필요하다" in system
        # 모드 블록은 5개 아이디어 기준 문구라 개수·형식 우선순위를 못박아야 한다
        assert "아이디어 개수" in system

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

    def test_requires_grok_cli_research_transport(self, monkeypatch):
        from providers.base import ProviderStatus
        from providers.grok_cli import GrokCliProvider

        monkeypatch.setattr(GrokCliProvider, "is_available", lambda self: ProviderStatus(False, "x"))
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


class TestSinglePostLintSafetyNet:
    """5개 경로와 같은 S1 상투 표현 안전망이 한 편짜리 글에도 걸리는지."""

    AI_SMELL = "결론적으로 이를 통해 배운 게 있다."
    REWRITTEN = "배운 게 하나 있다. 배포 전에 로그를 본다."

    def test_s1_hit_triggers_exactly_one_rewrite(self):
        provider = FakeProvider([
            {"post": {"title": "A", "content": self.AI_SMELL}},
            {"content": self.REWRITTEN},
        ])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert result["post"]["content"] == self.REWRITTEN
        assert result["post"]["_lint"]["s1"] == []
        assert len(provider.calls) == 2
        assert self.AI_SMELL in provider.calls[1][1]

    def test_rewrite_error_leaves_original_content(self):
        provider = FakeProvider([
            {"post": {"title": "A", "content": self.AI_SMELL}},
            {"error": "API 오류"},
        ])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert result["post"]["content"] == self.AI_SMELL
        assert result["post"]["_lint"]["s1"]

    def test_rewrite_failure_does_not_block_the_flow(self):
        class ExplodingProvider(FakeProvider):
            def generate_json(self, system_prompt, user_prompt, **kwargs):
                if self.calls:
                    self.calls.append((system_prompt, user_prompt))
                    raise RuntimeError("provider down")
                return super().generate_json(system_prompt, user_prompt)

        provider = ExplodingProvider([{"post": {"title": "A", "content": self.AI_SMELL}}])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert result["post"]["content"] == self.AI_SMELL
        assert len(provider.calls) == 2

    def test_clean_content_makes_no_extra_call(self):
        provider = FakeProvider([{"post": {"title": "A", "content": "담백한 본문이다."}}])

        result = GrokClient(provider=provider).write_post(
            keywords="배포 실수", direction=_direction(), length=280, mode="builder_note", language="ko"
        )

        assert len(provider.calls) == 1
        assert result["post"]["_lint"] == {"s1": [], "s2": []}

    def test_grounded_post_is_linted_too(self):
        provider = FakeGroundedProvider(
            [
                {"post": {"content": self.AI_SMELL, "evidence_urls": ["https://who.int/a"]}},
                {"content": self.REWRITTEN},
            ],
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

        assert result["post"]["content"] == self.REWRITTEN
        assert result["post"]["sources"][0]["url"] == "https://who.int/a"
        assert len(provider.calls) == 2


class TestExplicitLanguageIsRequired:
    """워커 스레드에는 Streamlit 세션이 없다 — 언어는 반드시 넘겨받아야 한다."""

    def test_new_methods_require_language_keyword(self):
        import inspect

        for name in ("generate_directions", "write_post", "write_grounded_post"):
            parameter = inspect.signature(getattr(GrokClient, name)).parameters["language"]
            assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
            assert parameter.default is inspect.Parameter.empty

    def test_optimize_post_language_stays_optional(self):
        import inspect

        parameter = inspect.signature(GrokClient.optimize_post).parameters["language"]
        assert parameter.default is None


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

        import voice_card

        expected = OPTIMIZER_SYSTEM_PROMPT + NATURAL_STYLE_GUIDE + voice_card.build_voice_block() + get_lang_instruction()
        assert provider.calls[0][0] == expected
        assert provider.calls[1][0] == expected



def test_grounded_post_researches_with_grok_and_writes_with_selected_engine(monkeypatch):
    """조사는 Grok CLI, 글은 선택한 엔진. 기본 모드는 v2 짧은 프롬프트를 쓴다."""
    from providers.base import ProviderStatus
    from providers.grok_cli import GrokCliProvider
    from xalgo_prompts import GROUNDED_POST_V2_SYSTEM_PROMPT, NATURAL_STYLE_GUIDE

    packet = {
        "facts": [{"statement": "지급 연령이 9세 미만으로 늘었다", "source_urls": ["https://a.go.kr/1", "https://b.kr/2"]}],
        "sources": [{"url": "https://a.go.kr/1", "title": "", "excerpt": ""}, {"url": "https://b.kr/2"}],
    }
    monkeypatch.setattr(GrokCliProvider, "is_available", lambda self: ProviderStatus(True, "ok"))
    monkeypatch.setattr(GrokCliProvider, "research_json", lambda self, s, u, **kw: packet)
    provider = FakeProvider([{"post": {"title": "t", "content": "아동수당 바뀐 거 정리해요", "evidence_urls": ["https://a.go.kr/1"]}}])

    result = GrokClient(provider=provider).write_grounded_post(
        keywords="아동수당", direction=_direction(), category="daily", language="ko"
    )

    assert result["post"]["content"] == "아동수당 바뀐 거 정리해요"
    system = provider.calls[0][0]
    assert GROUNDED_POST_V2_SYSTEM_PROMPT in system
    assert NATURAL_STYLE_GUIDE not in system


def test_legacy_grounded_tips_use_v2_in_my_voice(monkeypatch):
    from providers.base import ProviderStatus
    from providers.grok_cli import GrokCliProvider
    from xalgo_prompts import GROUNDED_TIPS_V2_SYSTEM_PROMPT, NATURAL_STYLE_GUIDE

    packet = {
        "facts": [{"statement": "0세 월 100만 원", "source_urls": ["https://a.go.kr/1", "https://b.kr/2"]}],
        "sources": [{"url": "https://a.go.kr/1"}, {"url": "https://b.kr/2"}],
    }
    monkeypatch.setattr(GrokCliProvider, "is_available", lambda self: ProviderStatus(True, "ok"))
    monkeypatch.setattr(GrokCliProvider, "research_json", lambda self, s, u, **kw: packet)
    provider = FakeProvider([{"ideas": [{"title": "t", "content": "부모급여 정리해요", "evidence_urls": ["https://a.go.kr/1"]}]}])

    result = GrokClient(provider=provider).generate_grounded_tips("부모급여", category="daily", language="ko")

    assert result["ideas"][0]["content"] == "부모급여 정리해요"
    assert GROUNDED_TIPS_V2_SYSTEM_PROMPT in provider.calls[0][0]
    assert NATURAL_STYLE_GUIDE not in provider.calls[0][0]
