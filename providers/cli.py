from __future__ import annotations

import shutil
import subprocess

from providers.base import ProviderStatus, extract_json_object


class CliProvider:
    name = "CLI"
    command = ""
    supports_curator = False

    def is_available(self) -> ProviderStatus:
        if shutil.which(self.command):
            return ProviderStatus(True, f"{self.command} CLI is available")
        return ProviderStatus(False, f"{self.command} CLI not found")

    def _prompt(self, system_prompt: str, user_prompt: str) -> str:
        return f"{system_prompt.strip()}\n\nUser request:\n{user_prompt.strip()}".strip()

    def _run(self, cmd: list[str], *, timeout: int) -> tuple[int, str, str]:
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
        return completed.returncode, completed.stdout, completed.stderr

    # v2 아이디어 프롬프트(모드 블록+스타일 가이드+보이스 카드)가 커지면서
    # 5개 아이디어 생성이 120초를 넘기는 일이 잦아 300초로 상향 (2026-08-11).
    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> dict:
        code, stdout, stderr = self._run(self._json_command(system_prompt, user_prompt), timeout=timeout)
        if code != 0:
            detail = (stderr or stdout or "unknown provider error").strip()
            return {"error": f"{self.name} error: {detail}"}
        return extract_json_object(stdout)

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> str:
        code, stdout, stderr = self._run(self._text_command(system_prompt, user_prompt), timeout=timeout)
        if code != 0:
            detail = (stderr or stdout or "unknown provider error").strip()
            return f"{self.name} error: {detail}"
        return stdout.strip()

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        raise NotImplementedError

    def _text_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        raise NotImplementedError
