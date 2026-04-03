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
    @patch("grok_client.openai.OpenAI")
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

    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
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

    @patch("grok_client.openai.OpenAI")
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
    @patch("grok_client.openai.OpenAI")
    def test_api_error_returns_error_dict(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.OpenAIError("API Error")

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_post("test")

        assert "error" in result
