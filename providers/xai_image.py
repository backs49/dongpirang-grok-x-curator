from __future__ import annotations

import base64
from pathlib import Path

from providers.base import ProviderError, ProviderStatus

DEFAULT_IMAGE_MODEL = "grok-imagine-image-quality"


class XaiImageProvider:
    """xAI 이미지 생성 API (Grok Imagine) 프로바이더.

    OpenAI SDK 호환 엔드포인트를 사용하며 b64_json 응답을 받아
    파일로 저장한다. 배포 환경(Streamlit Cloud 등)처럼 로컬 CLI 가
    없는 곳에서의 이미지 생성 경로다.
    """

    name = "xAI API"

    def __init__(self, api_key: str, model: str = DEFAULT_IMAGE_MODEL):
        self.api_key = (api_key or "").strip()
        self.model = model
        self._client = None

    def is_available(self) -> ProviderStatus:
        if self.api_key:
            return ProviderStatus(True, "xAI image API key provided")
        return ProviderStatus(False, "xAI API key required for image generation")

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(base_url="https://api.x.ai/v1", api_key=self.api_key)
        return self._client

    def generate_image(self, prompt: str, out_path: Path, *, timeout: int = 120) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = self._get_client().images.generate(
                model=self.model,
                prompt=prompt.strip(),
                response_format="b64_json",
            )
            b64 = response.data[0].b64_json
        except ProviderError:
            raise
        except Exception as exc:  # SDK 예외를 사용자 표시용 오류로 변환
            raise ProviderError(f"{self.name} image error: {exc}")

        if not b64:
            raise ProviderError(f"{self.name} returned an empty image payload")

        out_path.write_bytes(base64.b64decode(b64))
        return out_path
