from unittest.mock import MagicMock, patch

from provider_selection import build_provider


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
