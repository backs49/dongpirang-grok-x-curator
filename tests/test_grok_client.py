import json
import openai
from unittest.mock import MagicMock, patch
from grok_client import GrokClient


class TestGrokClientInit:
    def test_creates_openai_client(self):
        client = GrokClient(api_key="test-key", model="grok-4.1-fast-reasoning")
        assert client.model == "grok-4.1-fast-reasoning"
        assert client.client is not None

    def test_base_url_is_xai(self):
        client = GrokClient(api_key="test-key", model="grok-4.1-fast-reasoning")
        assert "x.ai" in str(client.client.base_url)


class TestOptimizePost:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_parsed_json(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 85,
            "engagement_level": "High",
            "reasons": ["Good content"],
            "suggestions": ["Add a question"],
            "optimized_post": "Optimized text"
        })
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_post("Hello world")

        assert result["score"] == 85
        assert result["engagement_level"] == "High"
        mock_client.chat.completions.create.assert_called_once()

    @patch("providers.xai_api.openai.OpenAI")
    def test_passes_image_desc_and_hashtags(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 90}'
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        grok.optimize_post("text", image_desc="sunset photo", hashtags="#sunset")

        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args[1]["messages"][1]["content"]
        assert "sunset photo" in user_msg
        assert "#sunset" in user_msg


class TestGenerateIdeas:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_ideas_list(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "ideas": [{"title": f"Idea {i}", "content": f"Content {i}"} for i in range(5)]
        })
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.generate_ideas("AI, Python")

        assert "ideas" in result
        assert len(result["ideas"]) == 5


class TestCurateFeed:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_recommendations(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Responses API mock
        mock_text_part = MagicMock()
        mock_text_part.type = "output_text"
        mock_text_part.text = json.dumps({
            "recommendations": [
                {"summary": "Post 1", "why_recommended": "Trending"},
                {"summary": "Post 2", "why_recommended": "Relevant"},
                {"summary": "Post 3", "why_recommended": "Popular"},
            ]
        })
        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = [mock_text_part]
        mock_response = MagicMock()
        mock_response.output = [mock_message]
        mock_client.responses.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.curate_feed("AI")

        assert "recommendations" in result
        assert len(result["recommendations"]) == 3


class TestOptimizeThread:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_thread_analysis(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "tweets": [
                {"position": 1, "score": 85, "decay_multiplier": 1.0, "effective_score": 85, "analysis": "Strong hook"},
                {"position": 2, "score": 70, "decay_multiplier": 0.79, "effective_score": 55, "analysis": "Good body"},
            ],
            "overall_score": 70,
            "thread_flow": {"hook_quality": "Strong", "narrative_arc": "Good flow", "cta_analysis": "Needs CTA", "optimal_tweet_count": 3},
            "optimized_thread": ["Optimized 1", "Optimized 2"],
            "strategy_notes": ["Add images"]
        })
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_thread("Tweet 1\n---\nTweet 2")

        assert result["overall_score"] == 70
        assert len(result["tweets"]) == 2
        assert result["thread_flow"]["hook_quality"] == "Strong"

    def test_rejects_single_tweet(self):
        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_thread("Just one tweet")
        assert "error" in result


class TestPlanSchedule:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_schedule(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "schedule": [
                {"position": 1, "topic_summary": "AI", "recommended_time": "오전 8:00", "recommended_day": "오늘", "reason": "출근 시간", "decay_from_previous": 1.0, "expected_visibility": "High"},
            ],
            "posting_order": [1],
            "topic_diversity_score": 80,
            "time_gap_analysis": "Good spacing",
            "decay_visualization": [{"post": 1, "visibility_percent": 100}],
            "overall_strategy": "Post at peak times"
        })
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.plan_schedule([{"topic": "AI trends"}])

        assert "schedule" in result
        assert result["topic_diversity_score"] == 80


class TestComparePosts:
    @patch("providers.xai_api.openai.OpenAI")
    def test_returns_comparison(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "post_a": {"score": 72, "engagement_level": "Medium", "strengths": ["Good list"], "weaknesses": ["No CTA"]},
            "post_b": {"score": 85, "engagement_level": "High", "strengths": ["Strong hook"], "weaknesses": ["Too short"]},
            "winner": "B",
            "score_difference": 13,
            "comparative_analysis": {"reply": {"advantage": "B", "reason": "B has a question"}},
            "improvement_for_loser": ["Add CTA"],
            "best_of_both": "Combined best post"
        })
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.compare_posts("Post A text", "Post B text")

        assert result["winner"] == "B"
        assert result["score_difference"] == 13

    @patch("providers.xai_api.openai.OpenAI")
    def test_sends_both_posts_in_single_call(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"winner": "A", "score_difference": 5}'
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        grok.compare_posts("Post A", "Post B")

        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        user_msg = call_args[1]["messages"][1]["content"]
        assert "포스트 A" in user_msg
        assert "포스트 B" in user_msg


class TestErrorHandling:
    @patch("providers.xai_api.openai.OpenAI")
    def test_api_error_returns_error_dict(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.OpenAIError("API Error")

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_post("test")

        assert "error" in result


class _CaptureProvider:
    """system/user 프롬프트를 캡처하고 준비된 응답을 차례로 돌려주는 페이크."""

    name = "Fake"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []  # (system, user) 튜플

    def generate_json(self, system, user):
        self.calls.append((system, user))
        return self.responses.pop(0) if self.responses else {"error": "exhausted"}


def _five_ideas(content="담백한 본문이다. 숫자 3이 있다."):
    return {
        "ideas": [
            {"title": f"t{i}", "content": content, "image_prompt": "scene"}
            for i in range(5)
        ]
    }


class TestGenerateIdeasV2:
    def test_mode_block_and_default_mode_injected(self):
        import writing_modes

        provider = _CaptureProvider([_five_ideas()])
        grok = GrokClient(provider=provider)
        result = grok.generate_ideas("AI")

        system = provider.calls[0][0]
        assert "글쓰기 모드 배정" in system  # 자동 믹스 블록
        # 자동 믹스: 라벨이 비어 있으면 톤 순환으로 보정된다
        labels = [idea["mode"] for idea in result["ideas"]]
        assert labels == [
            writing_modes.WRITING_MODES[k]["label"] for k in writing_modes.TONE_ROTATION
        ]

    def test_single_mode_injected(self):
        provider = _CaptureProvider([_five_ideas()])
        grok = GrokClient(provider=provider)
        result = grok.generate_ideas("AI", mode="kimhoon")

        system = provider.calls[0][0]
        assert "김훈체" in system
        assert all(idea["mode"] == "김훈체" for idea in result["ideas"])

    def test_avoid_block_from_history(self, monkeypatch, tmp_path):
        import ideas_history

        hist = tmp_path / "h.jsonl"
        monkeypatch.setattr(ideas_history, "HISTORY_PATH", hist)
        ideas_history.append_history(
            "AI", 0,
            {"ideas": [{"title": "이전 아이디어 제목", "content": "이전 훅 문장.\n나머지"}]},
        )
        provider = _CaptureProvider([_five_ideas()])
        grok = GrokClient(provider=provider)
        grok.generate_ideas("AI")

        system = provider.calls[0][0]
        assert "이전 아이디어 제목" in system
        assert "이전 훅 문장" in system

    def test_lint_attached_and_clean_content_no_retry(self):
        provider = _CaptureProvider([_five_ideas()])
        grok = GrokClient(provider=provider)
        result = grok.generate_ideas("AI")

        assert len(provider.calls) == 1  # 재시도 없음
        assert result["ideas"][0]["_lint"] == {"s1": [], "s2": []}

    def test_s1_triggers_single_rewrite(self):
        bad = _five_ideas("이것이 중요합니다. 결론적으로 좋습니다.")
        rewrites = {
            "rewrites": [
                {"index": i + 1, "content": "고쳐 쓴 담백한 문장이다."} for i in range(5)
            ]
        }
        provider = _CaptureProvider([bad, rewrites])
        grok = GrokClient(provider=provider)
        result = grok.generate_ideas("AI")

        assert len(provider.calls) == 2  # 1회 한정 재시도
        assert result["ideas"][0]["content"] == "고쳐 쓴 담백한 문장이다."
        assert result["ideas"][0]["_lint"]["s1"] == []

    def test_rewrite_failure_keeps_original(self):
        bad = _five_ideas("이것이 중요합니다.")
        provider = _CaptureProvider([bad, {"error": "boom"}])
        grok = GrokClient(provider=provider)
        result = grok.generate_ideas("AI")

        assert result["ideas"][0]["content"] == "이것이 중요합니다."
        assert result["ideas"][0]["_lint"]["s1"]  # 배지용 정보 유지

    def test_error_result_passthrough(self):
        provider = _CaptureProvider([{"error": "provider down"}])
        grok = GrokClient(provider=provider)
        assert grok.generate_ideas("AI") == {"error": "provider down"}


class TestAnalyzeVoice:
    def test_delegates_with_joined_examples(self):
        provider = _CaptureProvider([{"analysis": "담백한 평어체"}])
        grok = GrokClient(provider=provider)
        result = grok.analyze_voice(["예시 하나", "예시 둘"])

        assert result == {"analysis": "담백한 평어체"}
        system, user = provider.calls[0]
        assert "문체 분석가" in system
        assert "예시 하나" in user and "예시 둘" in user
