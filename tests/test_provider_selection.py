from unittest.mock import MagicMock, patch

from provider_selection import (
    API_MODEL_OPTIONS,
    ENGINE_OPTIONS,
    build_provider,
    uses_api_model_selector,
)


def test_model_selector_is_only_used_for_xai_api():
    assert uses_api_model_selector("xAI API") is True
    assert uses_api_model_selector("Claude CLI") is False
    assert uses_api_model_selector("Grok CLI") is False
    assert uses_api_model_selector("Codex CLI") is False
    assert uses_api_model_selector("Demo") is False


def test_codex_cli_is_a_selectable_engine():
    assert "Codex CLI" in ENGINE_OPTIONS


def test_api_model_options_are_xai_models():
    assert API_MODEL_OPTIONS == [
        "grok-4.3",
        "grok-build-0.1",
        "grok-4.1-fast-reasoning",
        "grok-4.20-reasoning",
    ]


class TestBuildProvider:
    @patch("provider_selection.ClaudeCliProvider")
    def test_builds_claude_cli_provider(self, provider_cls):
        provider = MagicMock()
        provider.is_available.return_value.available = True
        provider.is_available.return_value.message = "ready"
        provider_cls.return_value = provider

        client, status = build_provider("Claude CLI", api_key="", model="")

        assert client is not None
        assert status.available is True
        provider_cls.assert_called_once()

    @patch("provider_selection.GrokCliProvider")
    def test_builds_grok_cli_provider(self, provider_cls):
        provider = MagicMock()
        provider.is_available.return_value.available = True
        provider.is_available.return_value.message = "ready"
        provider_cls.return_value = provider

        client, status = build_provider("Grok CLI", api_key="", model="")

        assert client is not None
        assert status.available is True

    @patch("provider_selection.CodexCliProvider")
    def test_builds_codex_cli_provider(self, provider_cls):
        provider = MagicMock()
        provider.is_available.return_value.available = True
        provider.is_available.return_value.message = "ready"
        provider_cls.return_value = provider

        client, status = build_provider("Codex CLI", api_key="", model="")

        assert client is not None
        assert status.available is True
        provider_cls.assert_called_once()

    def test_demo_returns_no_client(self):
        client, status = build_provider("Demo", api_key="", model="")
        assert client is None
        assert status.available is False
        assert "demo" in status.message.lower()

    def test_xai_api_requires_key(self):
        client, status = build_provider("xAI API", api_key="", model="grok-4.3")
        assert client is None
        assert status.available is False
        assert "api key" in status.message.lower()
