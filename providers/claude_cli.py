from __future__ import annotations

from providers.cli import CliProvider


class ClaudeCliProvider(CliProvider):
    name = "Claude CLI"
    command = "claude"
    supports_curator = False

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        prompt = self._prompt(
            system_prompt + "\n\nReturn only one valid JSON object. Do not wrap it in markdown.",
            user_prompt,
        )
        return [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "text",
            "--tools",
            "",
            "--no-session-persistence",
        ]

    def _text_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        return [
            "claude",
            "-p",
            self._prompt(system_prompt, user_prompt),
            "--output-format",
            "text",
            "--tools",
            "",
            "--no-session-persistence",
        ]
