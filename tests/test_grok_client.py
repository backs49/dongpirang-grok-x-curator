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
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "recommendations": [
                {"summary": "Post 1", "why_recommended": "Trending"},
                {"summary": "Post 2", "why_recommended": "Relevant"},
                {"summary": "Post 3", "why_recommended": "Popular"},
            ]
        })
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.curate_feed("AI")

        assert "recommendations" in result
        assert len(result["recommendations"]) == 3


class TestErrorHandling:
    @patch("grok_client.openai.OpenAI")
    def test_api_error_returns_error_dict(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.OpenAIError("API Error")

        grok = GrokClient(api_key="test", model="grok-4.1-fast-reasoning")
        result = grok.optimize_post("test")

        assert "error" in result
