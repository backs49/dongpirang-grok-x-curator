from __future__ import annotations

from providers.cli import CliProvider


# 이 앱의 작업(한국어 카피라이팅 + JSON 출력)에는 최상위 프론티어 모델이
# 과하다. Sonnet 이 품질 저하 없이 구독 한도를 훨씬 아낀다.
DEFAULT_CLAUDE_MODEL = "sonnet"


class ClaudeCliProvider(CliProvider):
    name = "Claude CLI"
    command = "claude"
    supports_curator = False
    # None 이면 Claude Code 설정을 따른다. 글쓰기 호출은 GrokClient._write_json 이
    # low 로 바꾼다(2026-09-30 실측: Sonnet 5.5 low 5.8점, xhigh 5.3점·두 배 느림).
    reasoning_effort: str | None = None

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        prompt = self._prompt(
            system_prompt + "\n\nReturn only one valid JSON object. Do not wrap it in markdown.",
            user_prompt,
        )
        return [
            "claude",
            "-p",
            prompt,
            "--model",
            DEFAULT_CLAUDE_MODEL,
            "--output-format",
            "text",
            "--tools",
            "",
            "--no-session-persistence",
            *(["--effort", self.reasoning_effort] if self.reasoning_effort else []),
        ]

    def _text_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        return [
            "claude",
            "-p",
            self._prompt(system_prompt, user_prompt),
            "--model",
            DEFAULT_CLAUDE_MODEL,
            "--output-format",
            "text",
            "--tools",
            "",
            "--no-session-persistence",
        ]
