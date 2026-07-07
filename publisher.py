"""X API 발행 클라이언트 (OAuth 1.0a 사용자 컨텍스트).

.env 의 소비자 키 + 액세스 토큰으로 POST /2/tweets 를 호출한다.
키는 로그·예외 메시지에 절대 노출하지 않는다.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

from providers.base import ProviderError

ENV_PATH = Path(".env")
POST_TWEET_URL = "https://api.x.com/2/tweets"

_REQUIRED_KEYS = (
    "X_API_KEY",
    "X_API_KEY_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET",
)


def load_env(path: Path = ENV_PATH) -> dict:
    """단순 .env 파서. 환경변수가 이미 있으면 그것을 우선한다."""
    values: dict[str, str] = {}
    path = Path(path)
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    for key in _REQUIRED_KEYS:
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


class XPublisher:
    def __init__(self, env: dict | None = None):
        self._env = env if env is not None else load_env()

    def is_configured(self) -> bool:
        return all(self._env.get(k) for k in _REQUIRED_KEYS)

    def _auth(self) -> OAuth1:
        return OAuth1(
            self._env["X_API_KEY"],
            self._env["X_API_KEY_SECRET"],
            self._env["X_ACCESS_TOKEN"],
            self._env["X_ACCESS_TOKEN_SECRET"],
        )

    def post_text(self, text: str) -> dict:
        """텍스트 포스트를 발행하고 {"id": ..., "text": ...} 를 돌려준다."""
        if not self.is_configured():
            raise ProviderError("X API keys are not configured (.env)")

        text = (text or "").strip()
        if not text:
            raise ProviderError("empty post text")

        try:
            response = requests.post(
                POST_TWEET_URL,
                json={"text": text},
                auth=self._auth(),
                timeout=30,
            )
        except Exception as exc:
            raise ProviderError(f"X API request failed: {type(exc).__name__}")

        if response.status_code >= 400:
            detail = ""
            try:
                body = response.json()
                detail = body.get("detail") or body.get("title") or str(body)[:200]
            except Exception:
                detail = (response.text or "")[:200]
            raise ProviderError(f"X API error HTTP {response.status_code}: {detail}")

        data = response.json().get("data", {})
        if not data.get("id"):
            raise ProviderError("X API returned no tweet id")
        return data
