from __future__ import annotations

import base64
import time
from pathlib import Path

import requests

from providers.base import ProviderError, ProviderStatus

XAI_API_BASE = "https://api.x.ai/v1"
DEFAULT_VIDEO_MODEL = "grok-imagine-video"
POLL_INTERVAL_SECONDS = 5


class XaiVideoProvider:
    """xAI Grok Imagine 영상 생성 프로바이더.

    비동기 API: POST /videos/generations 으로 요청을 제출하고
    GET /videos/{request_id} 를 폴링해 완료되면 임시 URL 의 mp4 를
    즉시 내려받아 저장한다 (URL 은 임시라 바로 다운로드해야 한다).
    image_bytes 를 주면 image-to-video, 없으면 text-to-video.
    """

    name = "xAI API"

    def __init__(self, api_key: str, model: str = DEFAULT_VIDEO_MODEL):
        self.api_key = (api_key or "").strip()
        self.model = model

    def is_available(self) -> ProviderStatus:
        if self.api_key:
            return ProviderStatus(True, "xAI video API key provided")
        return ProviderStatus(False, "xAI API key required for video generation")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_video(
        self,
        prompt: str,
        out_path: Path,
        *,
        image_bytes: bytes | None = None,
        duration: int = 6,
        resolution: str = "720p",
        timeout: int = 600,
    ) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        body = {
            "model": self.model,
            "prompt": prompt.strip(),
            "duration": duration,
            "resolution": resolution,
        }
        if image_bytes:
            encoded = base64.b64encode(image_bytes).decode()
            body["image"] = f"data:image/png;base64,{encoded}"

        try:
            response = requests.post(
                f"{XAI_API_BASE}/videos/generations",
                json=body,
                headers=self._headers(),
                timeout=60,
            )
            response.raise_for_status()
            request_id = response.json().get("request_id")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"{self.name} video submit error: {exc}")

        if not request_id:
            raise ProviderError(f"{self.name} did not return a request_id")

        video_url = self._poll_until_done(request_id, timeout=timeout)

        try:
            download = requests.get(video_url, timeout=120)
            download.raise_for_status()
        except Exception as exc:
            raise ProviderError(f"{self.name} video download error: {exc}")

        out_path.write_bytes(download.content)
        return out_path

    def _poll_until_done(self, request_id: str, *, timeout: int) -> str:
        deadline = time.monotonic() + timeout
        while True:
            if time.monotonic() >= deadline:
                raise ProviderError(
                    f"{self.name} video generation timed out after {timeout} seconds"
                )
            time.sleep(POLL_INTERVAL_SECONDS)

            try:
                response = requests.get(
                    f"{XAI_API_BASE}/videos/{request_id}",
                    headers=self._headers(),
                    timeout=60,
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                raise ProviderError(f"{self.name} video poll error: {exc}")

            status = payload.get("status", "")
            if status == "done":
                url = (payload.get("video") or {}).get("url", "")
                if not url:
                    raise ProviderError(f"{self.name} finished without a video URL")
                return url
            if status in ("failed", "error", "rejected"):
                detail = payload.get("error") or payload.get("detail") or status
                raise ProviderError(f"{self.name} video generation failed: {detail}")
