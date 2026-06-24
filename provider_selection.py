from __future__ import annotations

from grok_client import GrokClient
from providers.base import ProviderStatus
from providers.claude_cli import ClaudeCliProvider
from providers.grok_cli import GrokCliProvider
from providers.xai_api import XaiApiProvider


ENGINE_OPTIONS = ["Claude CLI", "Grok CLI", "xAI API", "Demo"]


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
