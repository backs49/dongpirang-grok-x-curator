from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from providers.base import ProviderStatus, extract_json_object


# 2026-09-30 메모 블라인드 채점: Codex 중 gpt-6-luna + low 가 품질과 속도
# 모두 가장 나았다(low 5.5, medium 5.3, high 5.0, xhigh 5.2, max 4.5.
# Sol 은 강도 불문 4.5–4.9). 모델은 ~/.codex/config.toml 을 따르지 않는다.
DEFAULT_CODEX_MODEL = "gpt-6-luna"
DEFAULT_CODEX_EFFORT = "low"


class CodexCliProvider:
    """로컬 Codex CLI 텍스트 프로바이더 (ChatGPT 구독 기반).

    codex exec 은 진행 로그를 stdout 에 섞어 내보내므로, 최종 응답은
    --output-last-message 파일로 받아 깨끗하게 읽는다. 분석 작업에는
    셸 실행이 필요 없어 read-only 샌드박스 + --ephemeral 로 실행한다.
    """

    name = "Codex CLI"
    command = "codex"
    supports_curator = False
    # 분석·검토 호출은 예전 값 medium 을 유지하고, 글쓰기 호출만
    # GrokClient._write_json 이 DEFAULT_CODEX_EFFORT(low)로 바꿨다가 되돌린다.
    reasoning_effort: str | None = "medium"

    def is_available(self) -> ProviderStatus:
        if shutil.which(self.command):
            return ProviderStatus(True, f"{self.command} CLI is available")
        return ProviderStatus(False, f"{self.command} CLI not found")

    def _prompt(self, system_prompt: str, user_prompt: str) -> str:
        return f"{system_prompt.strip()}\n\nUser request:\n{user_prompt.strip()}".strip()

    def _run_exec(self, prompt: str, *, timeout: int) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "last_message.txt"
            cmd = [
                self.command,
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "-s",
                "read-only",
                "--color",
                "never",
                "-m",
                DEFAULT_CODEX_MODEL,
                *(
                    ["-c", f'model_reasoning_effort="{self.reasoning_effort}"']
                    if self.reasoning_effort
                    else []
                ),
                "-o",
                str(out_file),
                prompt,
            ]
            try:
                completed = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return 124, "", f"{self.name} timed out after {timeout} seconds"

            message = ""
            if out_file.is_file():
                message = out_file.read_text(encoding="utf-8")
            return completed.returncode, message, completed.stderr or completed.stdout

    # 추론형 모델 + 긴 시스템 프롬프트 조합은 2분을 넘기는 경우가 있어
    # 다른 CLI(120초)보다 여유 있게 잡는다. 배치 실행이라 대기 비용이 없다.
    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> dict:
        prompt = self._prompt(
            system_prompt
            + "\n\nReturn only one valid JSON object. Do not wrap it in markdown. "
            "Do not run any commands.",
            user_prompt,
        )
        code, message, detail = self._run_exec(prompt, timeout=timeout)
        if code != 0:
            return {"error": f"{self.name} error: {(detail or 'unknown codex error').strip()}"}
        return extract_json_object(message)

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> str:
        prompt = self._prompt(system_prompt + "\n\nDo not run any commands.", user_prompt)
        code, message, detail = self._run_exec(prompt, timeout=timeout)
        if code != 0:
            return f"{self.name} error: {(detail or 'unknown codex error').strip()}"
        return message.strip()
