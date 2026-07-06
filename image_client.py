from __future__ import annotations

import shutil
import time
from pathlib import Path

from providers.codex_cli_image import CodexCliImageProvider
from providers.xai_image import XaiImageProvider

GENERATED_DIR = Path("generated_images")


def build_copy_prompt(post_content: str, image_prompt: str) -> str:
    post_content = post_content.strip()
    image_prompt = image_prompt.strip()
    if post_content:
        return (
            "Create an image for this X post. Do not include readable text, letters, UI captions, "
            "watermarks, or logos unless explicitly requested.\n\n"
            f"Post context:\n{post_content}\n\n"
            f"Image prompt:\n{image_prompt}"
        )
    return (
        "Create an image from this prompt. Do not include readable text, letters, UI captions, "
        "watermarks, or logos unless explicitly requested.\n\n"
        f"Image prompt:\n{image_prompt}"
    )


class ImageClient:
    """이미지 프로바이더를 감싸 PNG bytes 를 돌려주는 파사드."""

    def __init__(self, provider, output_dir: Path = GENERATED_DIR):
        self._provider = provider
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return self._provider.name

    def generate(self, prompt: str) -> bytes:
        """프롬프트로 이미지를 생성해 output_dir 에 저장하고 bytes 를 반환한다."""
        filename = f"idea_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.png"
        out_path = self._provider.generate_image(prompt, self._output_dir / filename)
        return Path(out_path).read_bytes()


def build_image_client(api_key: str, output_dir: Path = GENERATED_DIR) -> ImageClient | None:
    """사용 가능한 이미지 백엔드를 자동 선택한다.

    1. 로컬 codex CLI 가 있으면 Codex CLI (구독 포함, 추가 과금 없음)
    2. 없으면 xAI API 키가 있을 때 xAI 이미지 API
    3. 둘 다 없으면 None — UI 는 기존 복사용 프롬프트만 보여준다.
    """
    if shutil.which(CodexCliImageProvider.command):
        return ImageClient(CodexCliImageProvider(), output_dir)
    if (api_key or "").strip():
        return ImageClient(XaiImageProvider(api_key), output_dir)
    return None
