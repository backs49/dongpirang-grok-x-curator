"""xAI 영상 생성 프로바이더 + VideoClient 선택 로직 테스트 (HTTP 목)."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

import providers.xai_video as video_mod
from providers.base import ProviderError
from providers.xai_video import XaiVideoProvider

import image_client
from image_client import build_video_client

MP4_BYTES = b"\x00\x00\x00 ftypisom-fake-mp4"
PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


class _FakeResponse:
    def __init__(self, json_data=None, content=b"", status_code=200):
        self._json = json_data or {}
        self.content = content
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise video_mod.requests.HTTPError(f"HTTP {self.status_code}")


def _install_happy_path(monkeypatch, poll_pending_times=1):
    """제출 → (pending × n) → done → mp4 다운로드 흐름을 목으로 구성."""
    calls = {"post": [], "get": []}

    def fake_post(url, **kwargs):
        calls["post"].append((url, kwargs))
        return _FakeResponse({"request_id": "req-123"})

    def fake_get(url, **kwargs):
        calls["get"].append((url, kwargs))
        if url.endswith("video.mp4"):
            return _FakeResponse(content=MP4_BYTES)
        if len([u for u, _ in calls["get"] if "req-123" in u]) <= poll_pending_times:
            return _FakeResponse({"status": "pending"})
        return _FakeResponse(
            {"status": "done", "video": {"url": "https://vidgen.x.ai/video.mp4"}}
        )

    monkeypatch.setattr(video_mod.requests, "post", fake_post)
    monkeypatch.setattr(video_mod.requests, "get", fake_get)
    monkeypatch.setattr(video_mod.time, "sleep", lambda _: None)
    return calls


class TestXaiVideoProvider:
    def test_requires_api_key(self):
        assert not XaiVideoProvider(api_key="").is_available().available
        assert XaiVideoProvider(api_key="xai-x").is_available().available

    def test_generate_video_text_to_video(self, monkeypatch, tmp_path):
        calls = _install_happy_path(monkeypatch)
        out = tmp_path / "clip.mp4"

        result = XaiVideoProvider(api_key="xai-x").generate_video(
            "a paw print animating", out, duration=6, resolution="720p"
        )

        assert result == out
        assert out.read_bytes() == MP4_BYTES
        submit_url, submit_kwargs = calls["post"][0]
        assert submit_url.endswith("/videos/generations")
        body = submit_kwargs["json"]
        assert body["model"] == "grok-imagine-video"
        assert body["duration"] == 6
        assert body["resolution"] == "720p"
        assert "image" not in body

    def test_generate_video_image_to_video_sends_image_object(self, monkeypatch, tmp_path):
        calls = _install_happy_path(monkeypatch)

        XaiVideoProvider(api_key="xai-x").generate_video(
            "animate this", tmp_path / "c.mp4", image_bytes=PNG_BYTES
        )

        body = calls["post"][0][1]["json"]
        # API 스펙: image 는 {"url": <https 또는 base64 data URI>} 객체다.
        assert isinstance(body["image"], dict)
        assert body["image"]["url"].startswith("data:image/png;base64,")
        encoded = body["image"]["url"].split(",", 1)[1]
        assert base64.b64decode(encoded) == PNG_BYTES

    def test_submit_error_surfaces_api_detail(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            video_mod.requests, "post",
            lambda url, **kw: _FakeResponse(
                {"error": "image must be an object"}, status_code=422
            ),
        )

        with pytest.raises(ProviderError, match="image must be an object"):
            XaiVideoProvider(api_key="xai-x").generate_video(
                "x", tmp_path / "c.mp4", image_bytes=PNG_BYTES
            )

    def test_generate_video_raises_on_failed_status(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            video_mod.requests, "post",
            lambda url, **kw: _FakeResponse({"request_id": "req-9"}),
        )
        monkeypatch.setattr(
            video_mod.requests, "get",
            lambda url, **kw: _FakeResponse(
                {"status": "failed", "error": "moderation block"}
            ),
        )
        monkeypatch.setattr(video_mod.time, "sleep", lambda _: None)

        with pytest.raises(ProviderError, match="moderation block"):
            XaiVideoProvider(api_key="xai-x").generate_video("x", tmp_path / "c.mp4")

    def test_generate_video_times_out_while_polling(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            video_mod.requests, "post",
            lambda url, **kw: _FakeResponse({"request_id": "req-9"}),
        )
        monkeypatch.setattr(
            video_mod.requests, "get",
            lambda url, **kw: _FakeResponse({"status": "pending"}),
        )
        monkeypatch.setattr(video_mod.time, "sleep", lambda _: None)

        fake_now = iter(range(0, 100000, 400))
        monkeypatch.setattr(video_mod.time, "monotonic", lambda: next(fake_now))

        with pytest.raises(ProviderError, match="timed out"):
            XaiVideoProvider(api_key="xai-x").generate_video(
                "x", tmp_path / "c.mp4", timeout=600
            )


class TestBuildVideoClient:
    def test_none_without_key_or_cli(self, monkeypatch):
        import image_client as ic

        monkeypatch.setattr(ic.shutil, "which", lambda _: None)
        assert build_video_client(api_key="") is None

    def test_client_with_key(self, monkeypatch, tmp_path):
        import image_client as ic

        monkeypatch.setattr(ic.shutil, "which", lambda _: None)
        client = build_video_client(api_key="xai-x", output_dir=tmp_path)
        assert client is not None
        assert client.name == "xAI API"

    def test_generate_writes_and_returns_bytes(self, monkeypatch, tmp_path):
        client = build_video_client(api_key="xai-x", output_dir=tmp_path)

        def fake_generate_video(prompt, out_path, **kwargs):
            Path(out_path).write_bytes(MP4_BYTES)
            return Path(out_path)

        client._provider.generate_video = fake_generate_video
        data = client.generate("animate", image_bytes=PNG_BYTES)
        assert data == MP4_BYTES
        assert list(tmp_path.glob("*.mp4"))
