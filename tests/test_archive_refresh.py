import json

import archive_refresh

ENV = {"X_API_KEY": "k", "X_API_KEY_SECRET": "s", "X_ACCESS_TOKEN": "t", "X_ACCESS_TOKEN_SECRET": "ts"}


class _Resp:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


class _Session:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, **kw):
        self.calls.append((url, dict(params or {})))
        if url.endswith("/users/me"):
            return _Resp({"data": {"id": "42"}})
        if "pagination_token" not in (params or {}):
            return _Resp({"data": [{"id": "300", "text": "새 글"}], "meta": {"next_token": "n"}})
        return _Resp({"data": [{"id": "250", "text": "짧게", "note_tweet": {"text": "긴 본문 전체"}}], "meta": {}})


def test_refresh_fetches_since_latest_and_merges(tmp_path):
    path = tmp_path / "my_posts.json"
    path.write_text(json.dumps([{"id": "200", "text": "예전 글"}]), encoding="utf-8")
    session = _Session()

    result = archive_refresh.refresh(path, env=ENV, session=session)

    assert result == {"added": 2, "total": 3}
    assert session.calls[1][1]["since_id"] == "200"
    rows = json.loads(path.read_text(encoding="utf-8"))
    assert [r["id"] for r in rows] == ["300", "250", "200"]
    assert rows[1]["text"] == "긴 본문 전체"


def test_refresh_without_keys_does_nothing(tmp_path):
    assert archive_refresh.refresh(tmp_path / "x.json", env={}) == {"error": "x_api_not_configured"}
