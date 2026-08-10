from __future__ import annotations

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from providers.codex_cli_image import CodexCliImageProvider
from providers.grok_cli_media import GrokCliImageProvider, GrokCliVideoProvider
from providers.xai_image import XaiImageProvider
from providers.xai_video import XaiVideoProvider

GENERATED_DIR = Path("generated_images")

# X 타임라인에서 크롭 없이 가장 크게 보이는 세로 규격 (3:4).
# xAI Grok Imagine 이 지원하는 세로 비율 중 X 가 크롭 없이 보여주는 최대치.
X_IMAGE_MAX = (1080, 1440)
X_IMAGE_MAX_RATIO = 4 / 3  # height/width — 이보다 길면 피드에서 잘린다

_IMAGE_RULES = (
    "Aspect ratio: portrait 4:5. "
    "Do not include readable text, letters, UI captions, watermarks, or logos "
    "unless explicitly requested. "
    "STYLE (mandatory, overrides the image prompt below if they conflict): render in a "
    "bold graphic style — flat editorial illustration, comic panel, or exaggerated "
    "cartoon — with clean shapes and a restrained palette of 2-3 strong colors. "
    "No garish neon-on-neon. NEVER render soft photorealism or a stock-photo look: "
    "no golden-hour cinematic haze, no cozy lamp-lit realism, no bland minimalism, "
    "no person gazing into the distance. Photorealism is allowed only if the image "
    "prompt explicitly demands it. "
    "READABILITY (mandatory): a viewer must understand the situation within 3 seconds "
    "without any caption — ONE focal point, a simple background, and a scene that "
    "clearly matches the post's core message. "
    "TONE (mandatory): exaggeration must stay playful and likable — NEVER gross, "
    "grotesque, disturbing, or body-horror. No slime, goo, vomit, melting bodies, "
    "or distorted anatomy. "
    "Build the whole image around ONE scroll-stopper: an unexpected juxtaposition, "
    "exaggerated humorous scale, a painfully relatable everyday moment, a bold single "
    "subject against strong color contrast, or a close-up with visible emotion."
)


def _log_generation(output_dir: Path, entry: dict) -> None:
    """생성 이력을 gen_log.jsonl 에 남긴다.

    UI 세션이 사라져도 어떤 프롬프트로 어떤 파일이 만들어졌는지 나중에
    추적·품질 검토할 수 있게 하는 용도. 실패해도 생성 흐름을 막지 않는다.
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        entry = {"at": datetime.now().isoformat(timespec="seconds"), **entry}
        with (output_dir / "gen_log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ─── 고정 마스코트 (동피랑고양이) ───
# 프로필의 갈색 태비 고양이를 3D 캐릭터화한 브랜드 마스코트.
# 참조 이미지를 지원하는 엔진(Grok CLI image_edit)은 이 파일을 레퍼런스로
# 사용해 캐릭터 일관성을 유지하고, 미지원 엔진은 텍스트 묘사로 근사한다.
MASCOT_PATH = Path("assets/mascot_dongpi.jpg")

_MASCOT_RULES = (
    "Aspect ratio: portrait 4:5. "
    "Do not include readable text, letters, UI captions, watermarks, or logos "
    "unless explicitly requested. "
    "MASCOT (mandatory): the protagonist is the fixed brand mascot — an adorable "
    "chubby brown tabby cat with dark stripes, white chest, muzzle and paws, big "
    "glossy green eyes, a pink nose and pink paw pads. Its fur markings, colors and "
    "proportions must stay identical in every image so it is recognizably the same "
    "character. Replace any human protagonist in the scene with this cat acting out "
    "the situation — anthropomorphic poses are encouraged (typing, driving, holding "
    "coffee). "
    "STYLE (mandatory): cute 3D animated-movie render — soft detailed fur, big "
    "expressive eyes, warm soft lighting, clean simple background. "
    "READABILITY (mandatory): a viewer must understand the situation within 3 seconds "
    "without any caption — ONE focal point, and a scene that clearly matches the "
    "post's core message. "
    "TONE (mandatory): exaggeration stays playful and lovable — NEVER gross, "
    "grotesque, disturbing, or body-horror."
)


def build_copy_prompt(post_content: str, image_prompt: str, mascot: bool = False) -> str:
    post_content = post_content.strip()
    image_prompt = image_prompt.strip()
    rules = _MASCOT_RULES if mascot else _IMAGE_RULES
    if post_content:
        return (
            f"Create a scroll-stopping image for this X post. {rules}\n\n"
            f"Post context:\n{post_content}\n\n"
            f"Image prompt:\n{image_prompt}"
        )
    return (
        f"Create a scroll-stopping image from this prompt. {rules}\n\n"
        f"Image prompt:\n{image_prompt}"
    )


def postprocess_for_x(src_path: Path) -> bytes:
    """생성 원본을 X 업로드 규격으로 정리한다.

    3:4보다 길면 중앙 크롭, 1080×1440 안으로 다운스케일, JPEG 재인코딩.
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

    def generate(
        self, prompt: str, reference: Path | None = None, style: str = ""
    ) -> bytes:
        """프롬프트로 이미지를 생성해 X 규격(3:4)으로 후처리하고 bytes 를 반환한다.

        reference: 캐릭터 일관성용 참조 이미지 (지원 프로바이더만 사용).
        style: gen_log 기록용 스타일 모드 키.
        """
        filename = f"idea_{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000:03d}.png"
        use_ref = (
            reference is not None
            and Path(reference).is_file()
            and getattr(self._provider, "supports_reference", False)
        )
        if use_ref:
            out_path = self._provider.generate_image(
                prompt, self._output_dir / filename, reference=Path(reference)
            )
        else:
            out_path = self._provider.generate_image(prompt, self._output_dir / filename)
        data = postprocess_for_x(Path(out_path))
        from xalgo_prompts import PROMPT_VERSION

        _log_generation(
            self._output_dir,
            {
                "kind": "image",
                "engine": self.name,
                "file": Path(out_path).stem,
                "mascot_ref": bool(use_ref),
                "style": style,
                "prompt_version": PROMPT_VERSION,
                "prompt": prompt,
            },
        )
        return data


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
        _log_generation(
            self._output_dir,
            {"kind": "video", "engine": self.name, "file": filename, "prompt": prompt},
        )
        return Path(out_path).read_bytes()


def build_video_client(api_key: str, output_dir: Path = GENERATED_DIR) -> VideoClient | None:
    """영상 백엔드 선택. 로컬 grok CLI(Imagine) 우선, 없으면 xAI API 키."""
    if shutil.which(GrokCliVideoProvider.command):
        return VideoClient(GrokCliVideoProvider(), output_dir)
    if (api_key or "").strip():
        return VideoClient(XaiVideoProvider(api_key), output_dir)
    return None
