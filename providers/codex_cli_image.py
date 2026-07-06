from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from providers.base import ProviderError, ProviderStatus


class CodexCliImageProvider:
    """로컬 Codex CLI 의 내장 $imagegen 스킬로 이미지를 생성한다.

    ChatGPT 구독 사용량에 포함되므로 별도 API 과금이 없다.
    codex exec 이 작업 디렉터리에 지정된 파일명으로 PNG 를 저장하도록
    지시하고, 종료 후 파일 존재를 검증한다.
    """

    name = "Codex CLI"
    command = "codex"

    def is_available(self) -> ProviderStatus:
        if shutil.which(self.command):
            return ProviderStatus(True, "codex CLI is available")
        return ProviderStatus(False, "codex CLI not found")

    def generate_image(self, prompt: str, out_path: Path, *, timeout: int = 360) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        instruction = (
            "Use $imagegen to generate exactly one image from the prompt below, "
            f"then save it as {out_path.name} in the current working directory. "
            "Do not do anything else.\n\n"
            f"Prompt:\n{prompt.strip()}"
        )
        cmd = [
            self.command,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "-C",
            str(out_path.parent),
            instruction,
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
            raise ProviderError(f"{self.name} timed out after {timeout} seconds")

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "unknown codex error").strip()
            raise ProviderError(f"{self.name} error: {detail[-500:]}")

        if not out_path.is_file() or out_path.stat().st_size == 0:
            detail = (completed.stdout or "").strip()
            raise ProviderError(
                f"{self.name} finished but did not produce {out_path.name}: {detail[-500:]}"
            )

        return out_path
