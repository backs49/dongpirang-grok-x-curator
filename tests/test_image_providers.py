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
    def test_prefers_grok_by_default(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/cli")
        client = build_image_client(api_key="xai-test")
        assert client is not None
        assert client.name == "Grok CLI"

    def test_engine_codex_when_selected(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/cli")
        client = build_image_client(api_key="", engine="Codex CLI")
        assert client is not None
        assert client.name == "Codex CLI"

    def test_falls_back_when_selected_cli_missing(self, monkeypatch):
        monkeypatch.setattr(
            image_client.shutil,
            "which",
            lambda cmd: "/usr/bin/codex" if cmd == "codex" else None,
        )
        client = build_image_client(api_key="", engine="Grok CLI")
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

    def test_video_prefers_grok_cli(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/grok")
        client = image_client.build_video_client(api_key="")
        assert client is not None
        assert client.name == "Grok CLI"

    def test_video_falls_back_to_xai(self, monkeypatch):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: None)
        client = image_client.build_video_client(api_key="xai-test")
        assert client is not None
        assert client.name == "xAI API"

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


# ─── X 규격 후처리 (postprocess_for_x) ───


class TestPostprocessForX:
    def _make_png(self, tmp_path, width, height):
        from PIL import Image

        path = tmp_path / "src.png"
        Image.new("RGB", (width, height), (200, 50, 50)).save(path, "PNG")
        return path

    def _open(self, data):
        import io

        from PIL import Image

        return Image.open(io.BytesIO(data))

    def test_tall_image_center_cropped_to_4x5_and_jpeg(self, tmp_path):
        from image_client import postprocess_for_x

        src = self._make_png(tmp_path, 941, 1672)  # 9:16급 세로
        data = postprocess_for_x(src)

        assert data[:2] == b"\xff\xd8"  # JPEG magic
        im = self._open(data)
        assert abs(im.height / im.width - 1.25) < 0.01  # 4:5
        assert im.width <= 1080 and im.height <= 1350
        assert not src.exists()  # 원본 PNG 는 제거
        assert (tmp_path / "src.jpg").exists()

    def test_oversized_image_downscaled(self, tmp_path):
        from image_client import postprocess_for_x

        src = self._make_png(tmp_path, 2048, 2048)
        im = self._open(postprocess_for_x(src))
        assert im.width <= 1080 and im.height <= 1350

    def test_landscape_image_kept_and_converted(self, tmp_path):
        from image_client import postprocess_for_x

        src = self._make_png(tmp_path, 1536, 1024)
        im = self._open(postprocess_for_x(src))
        assert abs(im.width / im.height - 1.5) < 0.01  # 비율 유지
        assert im.width <= 1080

    def test_unparseable_file_returned_as_is(self, tmp_path):
        from image_client import postprocess_for_x

        src = tmp_path / "bad.png"
        src.write_bytes(PNG_BYTES)  # 진짜 PNG 가 아닌 페이로드
        assert postprocess_for_x(src) == PNG_BYTES
        assert src.exists()


def test_copy_prompt_contains_viral_and_aspect_rules():
    from image_client import build_copy_prompt

    for prompt in (
        build_copy_prompt("post body", "a red mug"),
        build_copy_prompt("", "a red mug"),
    ):
        assert "4:5" in prompt
        assert "scroll-stopper" in prompt
        assert "no golden-hour" in prompt.lower() or "golden-hour" in prompt


# ─── Grok CLI 미디어 프로바이더 ───


class TestGrokCliMediaProviders:
    def _fake_run(self, monkeypatch, stdout, returncode=0):
        import providers.grok_cli_media as media_mod

        calls = {}

        def fake_run(cmd, capture_output, text, timeout, check):
            calls["cmd"] = cmd
            return type(
                "R", (), {"returncode": returncode, "stdout": stdout, "stderr": ""}
            )()

        monkeypatch.setattr(media_mod.subprocess, "run", fake_run)
        return calls

    def test_image_copies_session_file_to_out_path(self, monkeypatch, tmp_path):
        from providers.grok_cli_media import GrokCliImageProvider

        session_file = tmp_path / "1.jpg"
        session_file.write_bytes(b"\xff\xd8fake")
        calls = self._fake_run(
            monkeypatch, f"Generating now.{session_file}"
        )

        out = tmp_path / "out.png"
        result = GrokCliImageProvider().generate_image("a cat", out)

        assert result == out
        assert out.read_bytes() == b"\xff\xd8fake"
        assert "--tools" in calls["cmd"] and "image_gen" in calls["cmd"]

    def test_image_raises_when_no_path_in_output(self, monkeypatch, tmp_path):
        from providers.grok_cli_media import GrokCliImageProvider

        self._fake_run(monkeypatch, "something went sideways, no file")
        with pytest.raises(ProviderError):
            GrokCliImageProvider().generate_image("a cat", tmp_path / "out.png")

    def test_video_with_source_image_uses_image_to_video(self, monkeypatch, tmp_path):
        from providers.grok_cli_media import GrokCliVideoProvider

        session_mp4 = tmp_path / "1.mp4"
        session_mp4.write_bytes(b"mp4data")
        calls = self._fake_run(monkeypatch, f"done {session_mp4}")

        out = tmp_path / "clip.mp4"
        result = GrokCliVideoProvider().generate_video(
            "cat types", out, image_bytes=b"\xff\xd8img", duration=6
        )

        assert result == out
        assert out.read_bytes() == b"mp4data"
        prompt_arg = calls["cmd"][2]
        assert "image_to_video" in prompt_arg
        assert "6-second" in prompt_arg
        assert not (tmp_path / "clip.src.jpg").exists()  # 소스 임시파일 정리됨

    def test_video_duration_snaps_to_ten(self, monkeypatch, tmp_path):
        from providers.grok_cli_media import GrokCliVideoProvider

        session_mp4 = tmp_path / "2.mp4"
        session_mp4.write_bytes(b"mp4data")
        calls = self._fake_run(monkeypatch, str(session_mp4))

        GrokCliVideoProvider().generate_video(
            "cat", tmp_path / "c.mp4", image_bytes=None, duration=9
        )
        prompt_arg = calls["cmd"][2]
        assert "10-second" in prompt_arg
        assert "image_gen,image_to_video" in calls["cmd"]


# ─── 마스코트 모드 ───


class TestMascotMode:
    def test_mascot_prompt_swaps_style_rules(self):
        from image_client import build_copy_prompt

        plain = build_copy_prompt("post", "scene")
        mascot = build_copy_prompt("post", "scene", mascot=True)
        assert "MASCOT (mandatory)" in mascot
        assert "brown tabby cat" in mascot
        assert "3D animated-movie render" in mascot
        assert "MASCOT" not in plain

    def test_generate_passes_reference_to_supporting_provider(self, monkeypatch, tmp_path):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/grok")
        client = build_image_client(api_key="", output_dir=tmp_path)
        assert client.name == "Grok CLI"

        ref = tmp_path / "mascot.jpg"
        ref.write_bytes(b"\xff\xd8ref")
        seen = {}

        def fake_generate_image(prompt, out_path, *, reference=None, timeout=None):
            seen["reference"] = reference
            Path(out_path).write_bytes(PNG_BYTES)
            return Path(out_path)

        client._provider.generate_image = fake_generate_image
        client.generate("scene", reference=ref)
        assert seen["reference"] == ref

    def test_generate_skips_reference_when_unsupported(self, monkeypatch, tmp_path):
        monkeypatch.setattr(image_client.shutil, "which", lambda _: "/usr/bin/cli")
        client = build_image_client(api_key="", engine="Codex CLI", output_dir=tmp_path)
        assert client.name == "Codex CLI"

        ref = tmp_path / "mascot.jpg"
        ref.write_bytes(b"\xff\xd8ref")

        def fake_generate_image(prompt, out_path, *, timeout=None):
            # reference 키워드가 오면 TypeError 가 났을 것 — 순수 시그니처 확인
            Path(out_path).write_bytes(PNG_BYTES)
            return Path(out_path)

        client._provider.generate_image = fake_generate_image
        assert client.generate("scene", reference=ref) == PNG_BYTES

    def test_grok_provider_uses_image_edit_with_reference(self, monkeypatch, tmp_path):
        from providers.grok_cli_media import GrokCliImageProvider
        import providers.grok_cli_media as media_mod

        session_file = tmp_path / "1.jpg"
        session_file.write_bytes(b"\xff\xd8fake")
        calls = {}

        def fake_run(cmd, capture_output, text, timeout, check):
            calls["cmd"] = cmd
            return type("R", (), {"returncode": 0, "stdout": str(session_file), "stderr": ""})()

        monkeypatch.setattr(media_mod.subprocess, "run", fake_run)
        ref = tmp_path / "mascot.jpg"
        ref.write_bytes(b"\xff\xd8ref")
        GrokCliImageProvider().generate_image("scene", tmp_path / "out.png", reference=ref)

        prompt_arg = calls["cmd"][2]
        assert "image_edit" in prompt_arg
        assert str(ref) in prompt_arg
        assert "image_edit" in calls["cmd"]  # --tools 값
