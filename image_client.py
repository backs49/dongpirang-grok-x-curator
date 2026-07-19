from __future__ import annotations

import shutil
import time
from pathlib import Path

from providers.codex_cli_image import CodexCliImageProvider
from providers.grok_cli_media import GrokCliImageProvider, GrokCliVideoProvider
from providers.xai_image import XaiImageProvider
from providers.xai_video import XaiVideoProvider

GENERATED_DIR = Path("generated_images")

# X 타임라인에서 크롭 없이 가장 크게 보이는 세로 규격 (4:5)
X_IMAGE_MAX = (1080, 1350)
X_IMAGE_MAX_RATIO = 1.25  # height/width — 이보다 길면 피드에서 잘린다

_IMAGE_RULES = (
    "Aspect ratio: portrait 4:5. "
    "Do not include readable text, letters, UI captions, watermarks, or logos "
    "unless explicitly requested. "
    "STYLE (mandatory, overrides the image prompt below if they conflict): render in a "
    "bold graphic style — flat editorial illustration, comic panel, or exaggerated "
    "cartoon — with punchy high-contrast colors and clean shapes. NEVER render soft "
    "photorealism or a stock-photo look: no golden-hour cinematic haze, no cozy "
    "lamp-lit realism, no bland minimalism, no person gazing into the distance. "
    "Photorealism is allowed only if the image prompt explicitly demands it. "
    "Build the whole image around ONE scroll-stopper: an unexpected juxtaposition, "
    "exaggerated humorous scale, a painfully relatable everyday moment, a bold single "
    "subject against strong color contrast, or a close-up with visible emotion."
)


def build_copy_prompt(post_content: str, image_prompt: str) -> str:
    post_content = post_content.strip()
    image_prompt = image_prompt.strip()
    if post_content:
        return (
            f"Create a scroll-stopping image for this X post. {_IMAGE_RULES}\n\n"
            f"Post context:\n{post_content}\n\n"
            f"Image prompt:\n{image_prompt}"
        )
    return (
        f"Create a scroll-stopping image from this prompt. {_IMAGE_RULES}\n\n"
        f"Image prompt:\n{image_prompt}"
    )


def postprocess_for_x(src_path: Path) -> bytes:
    """생성 원본을 X 업로드 규격으로 정리한다.

    4:5보다 길면 중앙 크롭, 1080×1350 안으로 다운스케일, JPEG 재인코딩.
    1.5MB PNG 가 수백 KB 로 줄고 타임라인 크롭도 사라진다.
    Pillow 를 못 쓰는 환경에서는 원본 bytes 를 그대로 돌려준다.
    """
    src_path = Path(src_path)
    try:
        from PIL import Image

        with Image.open(src_path) as im:
            im = im.convert("RGB")
            w, h = im.size
            if h / w > X_IMAGE_MAX_RATIO:
                new_h = int(w * X_IMAGE_MAX_RATIO)
                top = (h - new_h) // 2
                im = im.crop((0, top, w, top + new_h))
            im.thumbnail(X_IMAGE_MAX, Image.LANCZOS)
            out_path = src_path.with_suffix(".jpg")
            im.save(out_path, "JPEG", quality=87, optimize=True)
    except Exception:
        return src_path.read_bytes()

    if out_path != src_path:
        src_path.unlink(missing_ok=True)
    return out_path.read_bytes()


class ImageClient:
    """이미지 프로바이더를 감싸 X 규격 JPEG bytes 를 돌려주는 파사드."""

    def __init__(self, provider, output_dir: Path = GENERATED_DIR):
        self._provider = provider
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return self._provider.name

    def generate(self, prompt: str) -> bytes:
        """프롬프트로 이미지를 생성해 X 규격으로 후처리하고 bytes 를 반환한다."""
        filename = f"idea_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.png"
        out_path = self._provider.generate_image(prompt, self._output_dir / filename)
        return postprocess_for_x(Path(out_path))


# 사이드바 이미지 엔진 선택지. Grok CLI 가 기본 (Imagine 한도가 넉넉).
IMAGE_ENGINE_OPTIONS = ["Grok CLI", "Codex CLI"]


def build_image_client(
    api_key: str,
    output_dir: Path = GENERATED_DIR,
    engine: str = "Grok CLI",
) -> ImageClient | None:
    """이미지 백엔드를 선택한다.

    사용자가 고른 engine(기본 Grok CLI)을 우선 시도하고, 없으면
    Grok CLI → Codex CLI → xAI API 순서로 폴백한다.
    전부 없으면 None — UI 는 기존 복사용 프롬프트만 보여준다.
    """
    preferred = {
        "Grok CLI": GrokCliImageProvider,
        "Codex CLI": CodexCliImageProvider,
    }.get(engine, GrokCliImageProvider)

    chain = [preferred] + [
        cls
        for cls in (GrokCliImageProvider, CodexCliImageProvider)
        if cls is not preferred
    ]
    for cls in chain:
        if shutil.which(cls.command):
            return ImageClient(cls(), output_dir)
    if (api_key or "").strip():
        return ImageClient(XaiImageProvider(api_key), output_dir)
    return None


class VideoClient:
    """영상 프로바이더를 감싸 mp4 bytes 를 돌려주는 파사드."""

    def __init__(self, provider, output_dir: Path = GENERATED_DIR):
        self._provider = provider
        self._output_dir = Path(output_dir)

    @property
    def name(self) -> str:
        return self._provider.name

    def generate(
        self,
        prompt: str,
        *,
        image_bytes: bytes | None = None,
        duration: int = 6,
        resolution: str = "720p",
    ) -> bytes:
        filename = f"clip_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.mp4"
        out_path = self._provider.generate_video(
            prompt,
            self._output_dir / filename,
            image_bytes=image_bytes,
            duration=duration,
            resolution=resolution,
        )
        return Path(out_path).read_bytes()


def build_video_client(api_key: str, output_dir: Path = GENERATED_DIR) -> VideoClient | None:
    """영상 백엔드 선택. 로컬 grok CLI(Imagine) 우선, 없으면 xAI API 키."""
    if shutil.which(GrokCliVideoProvider.command):
        return VideoClient(GrokCliVideoProvider(), output_dir)
    if (api_key or "").strip():
        return VideoClient(XaiVideoProvider(api_key), output_dir)
    return None
