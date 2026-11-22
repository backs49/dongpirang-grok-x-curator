from __future__ import annotations

import fcntl
import json
import tempfile
import time
from pathlib import Path

from providers.base import extract_json_object
from providers.cli import CliProvider


# Gemini 4 글쓰기 모델. 평가 승자로 고정한다(task 2026-11-22-agy-cli-provider).
DEFAULT_AGY_MODEL = "gemini-4-neon-low"
# agy 호출은 프로세스를 넘어 한 번에 하나만. 2026-11-22 평가에서 8개를 병렬로 돌리자
# 도중에 로그인이 풀렸고, 다시 로그인하려면 터미널에서 직접 agy 를 띄워야 했다.
# 아이디어·워크스페이스 워커는 작업마다 따로 뜨는 프로세스라 파일 잠금으로 막는다.
AGY_LOCK_PATH = Path(tempfile.gettempdir()) / "dongpirang-agy.lock"
# 로그인이 풀리면 앱 안에서는 복구할 수 없다. agy 로그인 화면은 진짜 터미널(TTY)이
# 있어야 뜬다 — Claude Code 의 `! agy` 로도 안 된다(2026-11-22 실측).
_LOGGED_OUT_MARKERS = ("authentication required", "authentication failed", "not logged in")
LOGIN_HINT = "agy 로그인이 풀렸어요. 터미널에서 agy 를 실행해 다시 로그인한 뒤 재시도하세요"


class AgyCliProvider(CliProvider):
    """agy(Antigravity) CLI. 사이드바 선택 엔진 전용, 야간 배치에는 쓰지 않는다.

    agy 에는 도구를 끄는 설정과 세션 무저장 플래그가 없다. --mode plan --sandbox 와
    매 호출 새 빈 임시 폴더로 명령 실행·폴더 밖 읽기를 막는다. 남는 차이(도구 목록 노출,
    agy 쪽 대화 저장)는 D-012 에서 수용했다. --settings 의 deny 규칙은 실측에서
    아무것도 막지 못했다.
    """

    name = "agy CLI"
    command = "agy"
    supports_curator = False
    # effort 는 모델 id 접미사(-low)로만 정한다. --effort 를 같이 넘기면 두 장치가
    # 겹쳐 agy 업데이트 뒤 어느 쪽이 먹는지 알 수 없다. 그래서 reasoning_effort 속성을
    # 두지 않는다(GrokClient._write_json 의 low 전환 대상이 아니다).

    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_AGY_MODEL

    def _command(self, prompt: str, timeout: int) -> list[str]:
        # agy 가 스스로 끝낼 여유를 둔다. 프로세스 강제 종료와 같은 순간이면 토큰
        # 갱신 도중에 죽어 로그인이 풀릴 수 있다(재로그인은 터미널에서만 된다).
        print_timeout = max(timeout - 10, 1)
        return [
            "agy",
            "-p",
            prompt,
            "--model",
            self.model,
            "--output-format",
            "json",
            "--mode",
            "plan",
            "--sandbox",
            "--print-timeout",
            f"{print_timeout}s",
        ]

    @staticmethod
    def _envelope(stdout: str) -> dict | None:
        # agy 는 결과 봉투 앞뒤에 안내 줄(예: "jetski: ...")을 섞는다. 뒤에서부터 찾는다.
        for line in reversed(stdout.strip().splitlines()):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and "status" in data:
                return data
        return None

    def _call(self, prompt: str, timeout: int) -> tuple[str | None, str | None]:
        """(응답, 오류). 거부되거나 막혀도 agy 는 SUCCESS + 빈 응답을 준다."""
        deadline = time.monotonic() + timeout
        with open(AGY_LOCK_PATH, "a") as lock:
            # 기다리는 시간도 timeout 안에 든다. 앞 호출이 안 끝나면 오류로 돌려준다.
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 파일을 닫으면 풀린다
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        return None, "다른 agy 호출이 끝나지 않아 기다리다 시간 초과"
                    time.sleep(0.2)
            remaining = max(round(deadline - time.monotonic()), 1)
            with tempfile.TemporaryDirectory(prefix="agy-") as cwd:
                code, stdout, stderr = self._run(
                    self._command(prompt, remaining), timeout=remaining, cwd=cwd
                )
        if any(m in f"{stdout}\n{stderr}".lower() for m in _LOGGED_OUT_MARKERS):
            return None, LOGIN_HINT
        if code != 0:
            return None, (stderr or stdout or "unknown provider error").strip()
        env = self._envelope(stdout)
        if env is None:
            return None, f"응답 형식을 알 수 없음: {(stdout or stderr).strip()[:200]}"
        denied = env.get("denied_actions")
        if denied:
            actions = ", ".join(str(d.get("action")) for d in denied if isinstance(d, dict))
            return None, f"도구 사용이 거부됨({actions})"
        response = (env.get("response") or "").strip()
        if env.get("status") != "SUCCESS" or not response:
            return None, f"빈 응답 또는 실패 상태({env.get('status')})"
        return response, None

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> dict:
        prompt = self._prompt(
            system_prompt + "\n\nReturn only one valid JSON object. Do not wrap it in markdown.",
            user_prompt,
        )
        response, error = self._call(prompt, timeout)
        if error:
            return {"error": f"{self.name} error: {error}"}
        return extract_json_object(response)

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> str:
        response, error = self._call(self._prompt(system_prompt, user_prompt), timeout)
        if error:
            return f"{self.name} error: {error}"
        return response
