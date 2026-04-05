import json
from utils import (
    generate_tweet_intent_url,
    generate_follow_url,
    parse_grok_json,
    append_viral_tag,
    parse_thread_text,
)


class TestGenerateTweetIntentUrl:
    def test_basic_text(self):
        url = generate_tweet_intent_url("Hello world")
        assert url.startswith("https://x.com/intent/post?text=")
        assert "Hello" in url

    def test_encodes_special_characters(self):
        url = generate_tweet_intent_url("Hello & world #test")
        assert "%26" in url or "&" not in url.split("?text=")[1].split("&")[0]
        assert "intent/post" in url

    def test_korean_text(self):
        url = generate_tweet_intent_url("안녕하세요")
        assert "intent/post" in url
        assert len(url) > len("https://x.com/intent/post?text=")

    def test_empty_text(self):
        url = generate_tweet_intent_url("")
        assert "intent/post" in url


class TestGenerateFollowUrl:
    def test_basic_username(self):
        url = generate_follow_url("mangodaon")
        assert url == "https://x.com/intent/follow?screen_name=mangodaon"

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


class TestParseThreadText:
    def test_split_by_triple_dash(self):
        text = "Tweet 1\n---\nTweet 2\n---\nTweet 3"
        result = parse_thread_text(text)
        assert len(result) == 3
        assert result[0] == "Tweet 1"
        assert result[2] == "Tweet 3"

    def test_split_by_blank_lines(self):
        text = "Tweet 1\n\n\nTweet 2\n\n\nTweet 3"
        result = parse_thread_text(text)
        assert len(result) == 3

    def test_mixed_separators(self):
        text = "Tweet 1\n---\nTweet 2\n\n\nTweet 3"
        result = parse_thread_text(text)
        assert len(result) == 3

    def test_single_tweet(self):
        result = parse_thread_text("Just one tweet")
        assert len(result) == 1
        assert result[0] == "Just one tweet"

    def test_empty_input(self):
        result = parse_thread_text("")
        assert len(result) == 0

    def test_strips_whitespace(self):
        text = "  Tweet 1  \n---\n  Tweet 2  "
        result = parse_thread_text(text)
        assert result[0] == "Tweet 1"
        assert result[1] == "Tweet 2"

    def test_ignores_empty_segments(self):
        text = "Tweet 1\n---\n\n---\nTweet 2"
        result = parse_thread_text(text)
        assert len(result) == 2


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
