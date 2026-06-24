from __future__ import annotations

from providers.cli import CliProvider


class GrokCliProvider(CliProvider):
    name = "Grok CLI"
    command = "grok"
    supports_curator = True

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        prompt = self._prompt(
            system_prompt + "\n\nReturn only one valid JSON object. Do not wrap it in markdown.",
            user_prompt,
        )
        return [
            "grok",
            "-p",
            prompt,
            "--output-format",
            "plain",
            "--tools",
            "",
            "--no-memory",
        ]

    def _text_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        return [
            "grok",
            "-p",
            self._prompt(system_prompt, user_prompt),
            "--output-format",
            "plain",
            "--tools",
            "",
            "--no-memory",
        ]
