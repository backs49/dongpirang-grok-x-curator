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

    @patch("providers.cli.subprocess.run")
    def test_research_command_allows_only_web_tools(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="\n".join([
            '{"type":"tool_call_update","toolName":"web_fetch","rawOutput":{"url":"https://who.int/a","title":"WHO","excerpt":"A"}}',
            '{"type":"tool_call_update","toolName":"web_fetch","rawOutput":{"url":"https://cdc.gov/b","title":"CDC","excerpt":"B"}}',
            '{"type":"text","data":"{\\"facts\\":[{\\"statement\\":\\"fact\\",\\"source_urls\\":[\\"https://who.int/a\\",\\"https://cdc.gov/b\\"]}]}"}',
        ]))

        result = GrokCliProvider().research_json("SYSTEM", "USER", timeout=30)

        command = mock_run.call_args.args[0]
        assert command[command.index("--tools") + 1] == "web_search,web_fetch"
        assert command[command.index("--output-format") + 1] == "streaming-json"
        assert "--no-memory" in command
        assert {item["url"] for item in result["sources"]} == {
            "https://who.int/a",
            "https://cdc.gov/b",
        }
        assert result["facts"][0]["statement"] == "fact"

    @patch("providers.cli.subprocess.run")
    def test_research_ignores_malformed_stream_lines_and_deduplicates_sources(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="\n".join([
            "not json",
            '{"type":"tool_call_update","toolName":"web_fetch","rawOutput":{"url":"https://WHO.int/a/","title":"WHO","excerpt":"A"}}',
            '{"type":"tool_call_update","toolName":"web_fetch","rawOutput":{"url":"https://who.int/a","title":"WHO second","excerpt":"B"}}',
            '{"type":"text","data":"{\\"facts\\":[]}"}',
        ]))

        result = GrokCliProvider().research_json("SYSTEM", "USER")

        assert result["facts"] == []
        assert result["sources"] == [{
            "url": "https://who.int/a",
            "title": "WHO",
            "excerpt": "A",
            "publisher": "",
            "published_at": "",
        }]

    @patch("providers.cli.subprocess.run")
    def test_research_returns_provider_error_on_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="bad token", stdout="")

        result = GrokCliProvider().research_json("SYSTEM", "USER")

        assert result["error"] == "Grok CLI research error: bad token"
