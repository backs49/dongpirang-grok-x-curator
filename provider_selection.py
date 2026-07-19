from __future__ import annotations

from grok_client import GrokClient
from providers.base import ProviderStatus
from providers.claude_cli import ClaudeCliProvider
from providers.codex_cli import CodexCliProvider
from providers.grok_cli import GrokCliProvider
from providers.xai_api import XaiApiProvider


# 첫 항목이 사이드바 기본값이다. Grok CLI 가 기본 (구독 한도가 넉넉).
ENGINE_OPTIONS = ["Grok CLI", "Claude CLI", "Codex CLI", "xAI API", "Demo"]
API_MODEL_OPTIONS = [
    "grok-4.3",
    "grok-build-0.1",
    "grok-4.1-fast-reasoning",
    "grok-4.20-reasoning",
]


def uses_api_model_selector(engine: str) -> bool:
    return engine == "xAI API"


def build_provider(
    engine: str,
    api_key: str = "",
    model: str = "grok-4.3",
) -> tuple[GrokClient | None, ProviderStatus]:
    if engine == "Demo":
        return None, ProviderStatus(False, "Demo mode")
    if engine == "Claude CLI":
        provider = ClaudeCliProvider()
    elif engine == "Grok CLI":
        provider = GrokCliProvider()
    elif engine == "Codex CLI":
        provider = CodexCliProvider()
    elif engine == "xAI API":
        if not api_key:
            return None, ProviderStatus(False, "xAI API key required")
        provider = XaiApiProvider(api_key=api_key, model=model)
    else:
        return None, ProviderStatus(False, f"Unknown engine: {engine}")

    status = provider.is_available()
    if not status.available:
        return None, status
    return GrokClient(provider=provider, model=model), status
