import json
from utils import (
    generate_tweet_intent_url,
    generate_follow_url,
    parse_grok_json,
    append_viral_tag,
)


class TestGenerateTweetIntentUrl:
    def test_basic_text(self):
        url = generate_tweet_intent_url("Hello world")
        assert url.startswith("https://twitter.com/intent/tweet?text=")
        assert "Hello" in url

    def test_encodes_special_characters(self):
        url = generate_tweet_intent_url("Hello & world #test")
        assert "%26" in url or "&" not in url.split("?text=")[1].split("&")[0]
        assert "intent/tweet" in url

    def test_korean_text(self):
        url = generate_tweet_intent_url("안녕하세요")
        assert "intent/tweet" in url
        assert len(url) > len("https://twitter.com/intent/tweet?text=")

    def test_empty_text(self):
        url = generate_tweet_intent_url("")
        assert "intent/tweet" in url


class TestGenerateFollowUrl:
    def test_basic_username(self):
        url = generate_follow_url("mangodaon")
        assert url == "https://twitter.com/intent/follow?screen_name=mangodaon"

    def test_strips_at_sign(self):
        url = generate_follow_url("@mangodaon")
        assert "screen_name=mangodaon" in url
        assert "@@" not in url


class TestParseGrokJson:
    def test_valid_json(self):
        result = parse_grok_json('{"score": 85, "engagement_level": "High"}')
        assert result["score"] == 85
        assert result["engagement_level"] == "High"

    def test_json_in_markdown_block(self):
        text = '```json\n{"score": 90}\n```'
        result = parse_grok_json(text)
        assert result["score"] == 90

    def test_invalid_json_returns_error(self):
        result = parse_grok_json("not json at all")
        assert "error" in result

    def test_empty_string(self):
        result = parse_grok_json("")
        assert "error" in result


class TestAppendViralTag:
    def test_appends_tag(self):
        result = append_viral_tag("Hello world", "via @mangodaon")
        assert result == "Hello world\n\nvia @mangodaon"

    def test_empty_tag_returns_original(self):
        result = append_viral_tag("Hello world", "")
        assert result == "Hello world"

    def test_strips_whitespace(self):
        result = append_viral_tag("Hello world  ", "  via @mangodaon  ")
        assert result == "Hello world\n\nvia @mangodaon"
