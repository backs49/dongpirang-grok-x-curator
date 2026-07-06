"""이미지 생성 프로바이더와 ImageClient 백엔드 자동 선택 로직 테스트.

실제 codex CLI / xAI API 호출 없이 subprocess·SDK 를 목으로 대체한다.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

import providers.codex_cli_image as codex_mod
from providers.base import ProviderError
from providers.codex_cli_image import CodexCliImageProvider
from providers.xai_image import XaiImageProvider

import image_client
from image_client import build_image_client


PNG_BYTES = b"\x89PNG\r\n\x1a\nfakepayload"


# ─── Codex CLI 이미지 프로바이더 ───


class TestCodexCliImageProvider:
    def test_is_available_when_cli_found(self, monkeypatch):
        monkeypatch.setattr(codex_mod.shutil, "which", lambda _: "/usr/bin/codex")
        assert CodexCliImageProvider().is_available().available

    def test_is_unavailable_when_cli_missing(self, monkeypatch):
        monkeypatch.setattr(codex_mod.shutil, "which", lambda _: None)
        status = CodexCliImageProvider().is_available()
        assert not status.available

    def test_generate_image_writes_file(self, monkeypatch, tmp_path):
        out_path = tmp_path / "idea.png"

        def fake_run(cmd, **kwargs):
            # codex exec 이 작업 디렉터리에 파일을 만든 상황을 흉내낸다.
            assert cmd[0] == "codex"
            assert "exec" in cmd
            assert "--skip-git-repo-check" in cmd
            # 출력 디렉터리는 -C 로, 파일명은 지시문에 포함되어야 한다.
            assert str(tmp_path) in cmd
            assert "idea.png" in cmd[-1]
            out_path.write_bytes(PNG_BYTES)

            class R:
                returncode = 0
                stdout = "Done."
                stderr = ""

            return R()

        monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
        result = CodexCliImageProvider().generate_image("a pink paw", out_path)
        assert result == out_path
        assert out_path.read_bytes() == PNG_BYTES

    def test_generate_image_raises_on_nonzero_exit(self, monkeypatch, tmp_path):
        def fake_run(cmd, **kwargs):
            class R:
                returncode = 1
                stdout = ""
                stderr = "usage limit reached"

            return R()

        monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
        with pytest.raises(ProviderError, match="usage limit"):
            CodexCliImageProvider().generate_image("x", tmp_path / "a.png")

    def test_generate_image_raises_when_file_missing(self, monkeypatch, tmp_path):
        def fake_run(cmd, **kwargs):
            class R:
                returncode = 0
                stdout = "Done."
                stderr = ""

            return R()

        monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
        with pytest.raises(ProviderError):
            CodexCliImageProvider().generate_image("x", tmp_path / "a.png")

    def test_generate_image_raises_on_timeout(self, monkeypatch, tmp_path):
        def fake_run(cmd, **kwargs):
            raise codex_mod.subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

        monkeypatch.setattr(codex_mod.subprocess, "run", fake_run)
        with pytest.raises(ProviderError, match="timed out"):
            CodexCliImageProvider().generate_image("x", tmp_path / "a.png")


# ─── xAI API 이미지 프로바이더 ───


class _FakeImagesApi:
    def __init__(self, b64: str):
        self._b64 = b64
        self.last_kwargs = None

    def generate(self, **kwargs):
        self.last_kwargs = kwargs

        class Datum:
            b64_json = self._b64

        class Resp:
            data = [Datum()]

        return Resp()


class TestXaiImageProvider:
    def test_requires_api_key(self):
        status = XaiImageProvider(api_key="").is_available()
        assert not status.available

    def test_available_with_key(self):
        assert XaiImageProvider(api_key="xai-test").is_available().available

    def test_generate_image_decodes_b64_and_writes(self, tmp_path):
        provider = XaiImageProvider(api_key="xai-test")
        fake_api = _FakeImagesApi(base64.b64encode(PNG_BYTES).decode())
        provider._client = type("C", (), {"images": fake_api})()

        out_path = tmp_path / "out.png"
        result = provider.generate_image("a pink paw", out_path)

        assert result == out_path
        assert out_path.read_bytes() == PNG_BYTES
        assert fake_api.last_kwargs["prompt"] == "a pink paw"
        assert fake_api.last_kwargs["response_format"] == "b64_json"


# ─── ImageClient 백엔드 자동 선택 ───


class TestBuildImageClient:
    def test_prefers_codex_when_installed(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/codex")
        client = build_image_client(api_key="xai-test")
        assert client is not None
        assert client.name == "Codex CLI"

    def test_falls_back_to_xai_with_key(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: None)
        client = build_image_client(api_key="xai-test")
        assert client is not None
        assert client.name == "xAI API"

    def test_none_when_no_backend(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: None)
        assert build_image_client(api_key="") is None

    def test_generate_writes_under_output_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/codex")
        client = build_image_client(api_key="", output_dir=tmp_path)

        def fake_generate_image(prompt, out_path, *, timeout=None):
            Path(out_path).write_bytes(PNG_BYTES)
            return Path(out_path)

        client._provider.generate_image = fake_generate_image
        png = client.generate("a pink paw")
        assert png == PNG_BYTES
        written = list(tmp_path.glob("*.png"))
        assert len(written) == 1


def test_img_i18n_keys_cover_all_languages():
    from i18n import _T, LANGUAGES

    for key in ("img_generate_btn", "img_generating", "img_engine_note",
                "img_engine_none", "img_download", "img_error",
                "vid_generate_btn", "vid_generating", "vid_need_key",
                "vid_duration_label", "vid_resolution_label", "vid_cost_note",
                "vid_download", "vid_error"):
        assert set(_T[key]) >= set(LANGUAGES), f"missing translations for {key}"
