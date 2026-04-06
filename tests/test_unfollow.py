"""Tests for parse_followers_file and compare_followers utilities."""

import io
from utils import parse_followers_file, compare_followers


class _FakeUpload:
    """Minimal file-like object that mimics Streamlit's UploadedFile."""

    def __init__(self, name: str, content: str):
        self.name = name
        self._content = content.encode("utf-8")

    def getvalue(self) -> bytes:
        return self._content


# ─── parse_followers_file ───


class TestParseFollowersJs:
    def test_followers_js(self):
        js = (
            'window.__twttr = window.__twttr || {};\n'
            'window.__twttr.YTweetDeck = window.__twttr.YTweetDeck || {};\n'
            'window.__twttr.YTweetDeck.followers = [\n'
            '  {"follower": {"accountId": "111"}},\n'
            '  {"follower": {"accountId": "222"}}\n'
            ']'
        )
        result = parse_followers_file(_FakeUpload("follower.js", js))
        assert result == {"111", "222"}

    def test_following_js(self):
        js = 'window.x = [{"following": {"accountId": "333"}}]'
        result = parse_followers_file(_FakeUpload("following.js", js))
        assert result == {"333"}

    def test_malformed_js_returns_empty(self):
        result = parse_followers_file(_FakeUpload("follower.js", "not valid"))
        assert result == set()

    def test_empty_js_returns_empty(self):
        result = parse_followers_file(_FakeUpload("follower.js", ""))
        assert result == set()

    def test_invalid_json_in_js(self):
        js = "window.x = [{bad json}]"
        result = parse_followers_file(_FakeUpload("data.js", js))
        assert result == set()


class TestParseFollowersCsv:
    def test_username_column(self):
        csv = "username\nalice\nbob\ncharlie"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"alice", "bob", "charlie"}

    def test_handle_column(self):
        csv = "handle,bio\n@alice,hello\n@bob,world"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"alice", "bob"}

    def test_accountid_column(self):
        csv = "AccountId,name\n111,Alice\n222,Bob"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"111", "222"}

    def test_strips_at_prefix(self):
        csv = "username\n@alice\n@bob"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"alice", "bob"}

    def test_lowercases_usernames(self):
        csv = "username\nAlice\nBOB"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"alice", "bob"}

    def test_empty_csv(self):
        result = parse_followers_file(_FakeUpload("data.csv", ""))
        assert result == set()

    def test_no_matching_column(self):
        csv = "email,name\na@b.com,Alice"
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == set()

    def test_skips_empty_values(self):
        csv = "username\nalice\n\nbob\n  "
        result = parse_followers_file(_FakeUpload("data.csv", csv))
        assert result == {"alice", "bob"}


class TestParseFollowersUnsupported:
    def test_unsupported_extension(self):
        result = parse_followers_file(_FakeUpload("data.txt", "hello"))
        assert result == set()


# ─── compare_followers ───


class TestCompareFollowers:
    def test_basic_comparison(self):
        old = {"a", "b", "c", "d"}
        new = {"b", "c", "e"}
        result = compare_followers(old, new)
        assert result["unfollowed"] == ["a", "d"]
        assert result["new_followers"] == ["e"]
        assert result["unchanged"] == ["b", "c"]

    def test_no_changes(self):
        users = {"a", "b", "c"}
        result = compare_followers(users, users)
        assert result["unfollowed"] == []
        assert result["new_followers"] == []
        assert result["unchanged"] == ["a", "b", "c"]

    def test_all_unfollowed(self):
        result = compare_followers({"a", "b"}, set())
        assert result["unfollowed"] == ["a", "b"]
        assert result["new_followers"] == []
        assert result["unchanged"] == []

    def test_all_new(self):
        result = compare_followers(set(), {"x", "y"})
        assert result["unfollowed"] == []
        assert result["new_followers"] == ["x", "y"]
        assert result["unchanged"] == []

    def test_empty_sets(self):
        result = compare_followers(set(), set())
        assert result["unfollowed"] == []
        assert result["new_followers"] == []
        assert result["unchanged"] == []

    def test_results_are_sorted(self):
        result = compare_followers({"c", "a", "b"}, {"b", "d", "a"})
        assert result["unfollowed"] == ["c"]
        assert result["new_followers"] == ["d"]
        assert result["unchanged"] == ["a", "b"]
