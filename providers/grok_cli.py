from __future__ import annotations

import json
from typing import Any, Iterator

from grounded_tips import normalize_url
from providers.base import extract_json_object
from providers.cli import CliProvider


WEB_RESEARCH_TOOLS = "web_search,web_fetch"


def _iter_source_metadata(value: Any) -> Iterator[dict[str, str]]:
    """도구 스트림의 중첩 rawOutput에서 URL을 가진 자료만 꺼낸다."""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return
        yield from _iter_source_metadata(parsed)
        return

    if isinstance(value, list):
        for item in value:
            yield from _iter_source_metadata(item)
        return

    if not isinstance(value, dict):
        return

    raw_url = value.get("url")
    normalized_url = normalize_url(raw_url) if isinstance(raw_url, str) else ""
    if normalized_url:
        def _text(*keys: str) -> str:
            for key in keys:
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            return ""

        yield {
            "url": normalized_url,
            "title": _text("title", "name"),
            "excerpt": _text("excerpt", "snippet", "text", "content"),
            "publisher": _text("publisher", "site_name", "siteName"),
            "published_at": _text("published_at", "publishedAt", "date"),
        }

    for nested in value.values():
        yield from _iter_source_metadata(nested)


def _parse_research_stream(stdout: str) -> dict:
    """Grok streaming-json의 텍스트와 웹 도구가 실제 반환한 출처를 분리한다."""
    text_chunks: list[str] = []
    sources_by_url: dict[str, dict[str, str]] = {}

    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        if event.get("type") == "text" and isinstance(event.get("data"), str):
            text_chunks.append(event["data"])

        if event.get("type") != "tool_call_update":
            continue
        if event.get("toolName") not in {"web_search", "web_fetch"}:
            continue
        for source in _iter_source_metadata(event.get("rawOutput")):
            sources_by_url.setdefault(source["url"], source)

    packet = extract_json_object("".join(text_chunks))
    if "error" in packet:
        return packet
    # 모델 텍스트 안의 sources는 증거가 아니다. 도구 스트림 출처만 신뢰한다.
    packet["sources"] = list(sources_by_url.values())
    return packet


class GrokCliProvider(CliProvider):
    name = "Grok CLI"
    command = "grok"
    supports_curator = True

    def research_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 300) -> dict:
        """웹 검색/가져오기만 허용한 별도 사실 조사 경로."""
        command = [
            "grok",
            "-p",
            self._prompt(system_prompt, user_prompt),
            "--output-format",
            "streaming-json",
            "--tools",
            WEB_RESEARCH_TOOLS,
            "--max-turns",
            "6",
            "--no-memory",
        ]
        code, stdout, stderr = self._run(command, timeout=timeout)
        if code != 0:
            detail = (stderr or stdout or "unknown error").strip()
            return {"error": f"{self.name} research error: {detail}"}
        return _parse_research_stream(stdout)

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
