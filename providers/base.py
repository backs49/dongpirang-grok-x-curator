from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from utils import parse_grok_json


@dataclass(frozen=True)
class ProviderStatus:
    available: bool
    message: str


class ProviderError(Exception):
    """Raised for provider setup errors that should be shown to the user."""


class ProviderClient(Protocol):
    name: str
    supports_curator: bool

    def is_available(self) -> ProviderStatus:
        ...

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict:
        ...

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> str:
        ...


def extract_json_object(text: str) -> dict:
    parsed = parse_grok_json(text)
    if "error" not in parsed:
        return parsed

    start = text.find("{")
    if start == -1:
        return parsed

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return parse_grok_json(text[start : idx + 1])

    return parsed
