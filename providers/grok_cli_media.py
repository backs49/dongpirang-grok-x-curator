from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from providers.base import ProviderError, ProviderStatus

# grok 이 stdout 에 흘리는 진행 문구와 경로가 한 줄에 붙어 나올 수 있어,
# 절대 경로 패턴을 전부 찾아 실제 존재하는 마지막 파일을 취한다.
_MEDIA_PATH_RE = re.compile(r"/\S+?\.(?:png|jpe?g|webp|mp4)", re.IGNORECASE)


def _run_grok(instruction: str, tools: str, timeout: int, name: str) -> str:
    """grok CLI 를 헤드리스로 실행한다. tools 는 허용할 도구 화이트리스트."""
    cmd = [
        "grok",
        "-p",
        instruction,
        "--output-format",
        "plain",
        "--no-memory",
        "--tools",
        tools,
    ]
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        raise ProviderError(f"{name} timed out after {timeout} seconds")

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "unknown grok error").strip()
        raise ProviderError(f"{name} error: {detail[-500:]}")
    return completed.stdout or ""


def _extract_media_path(stdout: str, suffixes: tuple[str, ...], name: str) -> Path:
    candidates = [
        Path(m)
        for m in _MEDIA_PATH_RE.findall(stdout)
        if Path(m).suffix.lower() in suffixes and Path(m).is_file()
    ]
    if not candidates:
        raise ProviderError(
            f"{name} finished but no media file found in output: {stdout[-300:].strip()}"
        )
    return candidates[-1]


class GrokCliImageProvider:
    """Grok Build CLI 의 Imagine image_gen 도구로 이미지를 생성한다.

    Grok 구독 사용량에 포함되어 별도 API 과금이 없다. 도구는 세션 폴더
    (~/.grok/sessions/...)에 저장하므로, 최종 답변으로 절대 경로만 출력하게
    지시한 뒤 그 파일을 out_path 로 복사한다. 3:4로 생성하며
    image_client.postprocess_for_x 가 같은 3:4 규격(1080×1440)으로 정리한다.
    """

    name = "Grok CLI"
    command = "grok"
    supports_reference = True  # image_edit 로 참조 이미지(마스코트) 기반 생성 가능

    def is_available(self) -> ProviderStatus:
        if shutil.which(self.command):
            return ProviderStatus(True, "grok CLI is available")
        return ProviderStatus(False, "grok CLI not found")

    def generate_image(
        self,
        prompt: str,
        out_path: Path,
        *,
        reference: Path | None = None,
        timeout: int = 360,
    ) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if reference is not None:
            instruction = (
                f"Use the image_edit tool with the reference image at {Path(reference)} "
                "to generate exactly one new image following the prompt below. The "
                "character in the reference image must appear in the new image with "
                "identical fur markings, colors, and proportions. Portrait 3:4 aspect "
                "ratio. After it is generated, your entire final answer must be ONLY "
                "the absolute filesystem path of the saved image file, nothing else.\n\n"
                f"Prompt:\n{prompt.strip()}"
            )
            tools = "image_edit"
        else:
            instruction = (
                "Use the image_gen tool to generate exactly one image from the prompt below, "
                "portrait 3:4 aspect ratio. After it is generated, your entire final answer "
                "must be ONLY the absolute filesystem path of the saved image file, "
                "nothing else.\n\n"
                f"Prompt:\n{prompt.strip()}"
            )
            tools = "image_gen"
        stdout = _run_grok(instruction, tools, timeout, self.name)
        src = _extract_media_path(stdout, (".png", ".jpg", ".jpeg", ".webp"), self.name)
        shutil.copyfile(src, out_path)
        return out_path


class GrokCliVideoProvider:
    """Grok Build CLI 의 Imagine 영상 도구로 짧은 클립을 생성한다.

    image_bytes 가 있으면 image_to_video (이미지 애니메이팅),
    없으면 image_gen 으로 소스 이미지를 만든 뒤 image_to_video 로 잇는다.
    클립 길이는 6초/10초만 지원 — duration 을 가까운 쪽으로 반올림한다.
    resolution 은 도구가 제어를 지원하지 않아 무시된다.
    """

    name = "Grok CLI"
    command = "grok"

    def is_available(self) -> ProviderStatus:
        if shutil.which(self.command):
            return ProviderStatus(True, "grok CLI is available")
        return ProviderStatus(False, "grok CLI not found")

    def generate_video(
        self,
        prompt: str,
        out_path: Path,
        *,
        image_bytes: bytes | None = None,
        duration: int = 6,
        resolution: str = "720p",
        timeout: int = 540,
    ) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        secs = 10 if duration >= 8 else 6

        src_img: Path | None = None
        try:
            if image_bytes:
                src_img = out_path.with_suffix(".src.jpg")
                src_img.write_bytes(image_bytes)
                instruction = (
                    f"Use the image_to_video tool to animate the image file at "
                    f"{src_img} into a {secs}-second clip. Motion direction:\n"
                    f"{prompt.strip()}\n\n"
                    "After the video is generated, your entire final answer must be "
                    "ONLY the absolute filesystem path of the saved video file, "
                    "nothing else."
                )
                tools = "image_to_video"
            else:
                instruction = (
                    "Use the image_gen tool to create one source image from the prompt "
                    f"below, then use the image_to_video tool to animate it into a "
                    f"{secs}-second clip. After the video is generated, your entire "
                    "final answer must be ONLY the absolute filesystem path of the "
                    "saved video file, nothing else.\n\n"
                    f"Prompt:\n{prompt.strip()}"
                )
                tools = "image_gen,image_to_video"

            stdout = _run_grok(instruction, tools, timeout, self.name)
            src = _extract_media_path(stdout, (".mp4",), self.name)
            shutil.copyfile(src, out_path)
            return out_path
        finally:
            if src_img is not None:
                src_img.unlink(missing_ok=True)
