from unittest.mock import MagicMock

from grok_client import GrokClient


class TestProviderFacade:
    def test_optimize_post_delegates_to_provider(self):
        provider = MagicMock()
        provider.generate_json.return_value = {"score": 91}
        client = GrokClient(provider=provider)

        result = client.optimize_post("hello", image_desc="screenshot", hashtags="#ai")

        assert result == {"score": 91}
        system_prompt, user_prompt = provider.generate_json.call_args.args[:2]
        assert "포스트 내용" in user_prompt
        assert "screenshot" in user_prompt
        assert "#ai" in user_prompt
        assert isinstance(system_prompt, str)

    def test_generate_ideas_delegates_to_provider(self):
        provider = MagicMock()
        provider.generate_json.return_value = {"ideas": [{"title": "A"}]}
        client = GrokClient(provider=provider)

        result = client.generate_ideas("AI", length=300)

        assert result["ideas"][0]["title"] == "A"
        user_prompt = provider.generate_json.call_args.args[1]
        assert "AI" in user_prompt

    def test_curate_feed_uses_provider_method_when_available(self):
        provider = MagicMock()
        provider.supports_curator = True
        provider.curate_feed.return_value = {"recommendations": [{"summary": "Post"}]}
        client = GrokClient(provider=provider)

        result = client.curate_feed("AI")

        assert result["recommendations"][0]["summary"] == "Post"
        provider.curate_feed.assert_called_once_with("AI")

    def test_curate_feed_fallback_when_provider_lacks_real_time_search(self):
        provider = MagicMock()
        provider.supports_curator = False
        provider.generate_json.return_value = {
            "recommendations": [
                {
                    "summary": "Search for AI founders",
                    "why_recommended": "Claude-only fallback",
                    "search_keywords": "AI founders",
                    "suggested_reply": "Great point. What changed your mind?",
                    "engagement_hint": "Use this after checking X manually.",
                }
            ]
        }
        client = GrokClient(provider=provider)

        result = client.curate_feed("AI founders")

        assert result["recommendations"][0]["search_keywords"] == "AI founders"
        assert provider.generate_json.called
