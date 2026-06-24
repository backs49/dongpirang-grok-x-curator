import subprocess
from unittest.mock import MagicMock, patch

from providers.base import ProviderStatus, extract_json_object
from providers.claude_cli import ClaudeCliProvider
from providers.grok_cli import GrokCliProvider


class TestProviderStatus:
    def test_available_status_has_message(self):
        status = ProviderStatus(available=True, message="ready")
        assert status.available is True
        assert status.message == "ready"


class TestExtractJsonObject:
    def test_extracts_plain_json(self):
        assert extract_json_object('{"score": 85}') == {"score": 85}

    def test_extracts_json_from_markdown_block(self):
        text = 'Here is the result:\n```json\n{"score": 90}\n```'
        assert extract_json_object(text) == {"score": 90}

    def test_extracts_first_balanced_object(self):
        text = 'analysis first\n{"score": 70, "nested": {"ok": true}}\nthanks'
        assert extract_json_object(text) == {"score": 70, "nested": {"ok": True}}

    def test_invalid_json_returns_error_dict(self):
        result = extract_json_object("not json")
        assert "error" in result


class TestClaudeCliProvider:
    @patch("providers.cli.shutil.which", return_value="/usr/local/bin/claude")
    def test_is_available_when_command_exists(self, _which):
        status = ClaudeCliProvider().is_available()
        assert status.available is True
        assert "claude" in status.message.lower()

    @patch("providers.cli.shutil.which", return_value=None)
    def test_is_unavailable_when_command_missing(self, _which):
        status = ClaudeCliProvider().is_available()
        assert status.available is False
        assert "not found" in status.message.lower()

    @patch("providers.cli.subprocess.run")
    def test_generate_json_invokes_claude_without_tools(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"score": 88}', stderr="")
        result = ClaudeCliProvider().generate_json("SYSTEM", "USER", timeout=30)
        assert result == {"score": 88}
        cmd = mock_run.call_args.args[0]
        assert cmd[:2] == ["claude", "-p"]
        assert "--tools" in cmd
        assert "" in cmd
        assert "--no-session-persistence" in cmd

    @patch("providers.cli.subprocess.run")
    def test_generate_json_handles_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["claude"], timeout=1)
        result = ClaudeCliProvider().generate_json("SYSTEM", "USER", timeout=1)
        assert "error" in result
        assert "timed out" in result["error"].lower()


class TestGrokCliProvider:
    @patch("providers.cli.subprocess.run")
    def test_generate_json_invokes_grok_headless(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
        result = GrokCliProvider().generate_json("SYSTEM", "USER", timeout=30)
        assert result == {"ok": True}
        cmd = mock_run.call_args.args[0]
        assert cmd[:2] == ["grok", "-p"]
        assert "--output-format" in cmd
        assert "plain" in cmd
        assert "--tools" in cmd
        assert "" in cmd

    @patch("providers.cli.subprocess.run")
    def test_generate_text_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")
        result = GrokCliProvider().generate_text("SYSTEM", "USER", timeout=30)
        assert result == "hello"
