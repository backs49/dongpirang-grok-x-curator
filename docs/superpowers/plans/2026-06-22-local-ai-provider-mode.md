# Local AI Provider Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-selectable local AI mode so the Streamlit app can use locally authenticated Claude/Grok CLIs, keep xAI API support, preserve demo mode, and add copy-first image prompt controls.

**Architecture:** Replace direct app dependence on `GrokClient` with a small provider layer. CLI providers wrap `claude -p` and `grok -p`; xAI API keeps the existing OpenAI-compatible implementation; tabs continue calling the same high-level methods through a facade so UI changes stay small.

**Tech Stack:** Python 3, Streamlit, OpenAI Python SDK, `subprocess.run`, pytest, unittest.mock.

## Global Constraints

- Do not scrape or automate the Claude, ChatGPT, or Grok web UI.
- Do not attempt to reuse ChatGPT Plus/Pro browser sessions as an API.
- Do not remove the existing xAI API path.
- Do not implement a full local model/Ollama provider in the first pass.
- Do not change the existing output schemas for tabs unless a schema is already broken.
- Default writing tasks to Claude CLI when Claude CLI and Grok CLI are both available.
- Default curator tasks to Grok CLI or xAI API because curator depends on Grok/X search capabilities.
- Treat local CLI providers as local-only and disable or hide them in hosted deployments where CLIs and user OAuth state are unavailable.
- Store generated images under `generated_images/` and add that directory to `.gitignore` when image generation storage is implemented.

---

## File Structure

- Create `providers/__init__.py`: exports provider classes and selection helpers.
- Create `providers/base.py`: provider protocol, provider status object, CLI JSON parsing helpers, provider errors.
- Create `providers/cli.py`: shared subprocess-backed provider utilities.
- Create `providers/claude_cli.py`: Claude CLI implementation.
- Create `providers/grok_cli.py`: Grok CLI implementation.
- Create `providers/xai_api.py`: xAI API implementation adapted from current `GrokClient`.
- Modify `grok_client.py`: turn it into a compatibility facade that delegates to a provider, preserving existing tab method names.
- Modify `app.py`: replace Grok-key-only sidebar with AI engine selection and provider construction.
- Modify `tabs/tab_curator.py`: add no-real-time-search fallback messaging path when provider lacks curator support.
- Modify `tabs/tab_ideas.py`: add copy-first image prompt controls.
- Modify `i18n.py`: add provider, local-generation, curator-fallback, and image-copy labels.
- Modify `.gitignore`: ignore `generated_images/`.
- Create `tests/test_providers.py`: provider status, CLI command, JSON parsing, error behavior.
- Create `tests/test_provider_facade.py`: compatibility facade routes existing methods to provider methods.
- Create `tests/test_image_workflow.py`: image prompt copy helper behavior.

---

### Task 1: Provider Core And CLI Providers

**Files:**
- Create: `providers/__init__.py`
- Create: `providers/base.py`
- Create: `providers/cli.py`
- Create: `providers/claude_cli.py`
- Create: `providers/grok_cli.py`
- Test: `tests/test_providers.py`

**Interfaces:**
- Produces: `ProviderStatus`, `ProviderError`, `ProviderClient`, `extract_json_object(text: str) -> dict`, `ClaudeCliProvider`, `GrokCliProvider`.
- Consumes: existing `utils.parse_grok_json`.

- [ ] **Step 1: Write failing provider core tests**

Add this file:

```python
# tests/test_providers.py
import json
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
        text = 'Here is the result:\\n```json\\n{"score": 90}\\n```'
        assert extract_json_object(text) == {"score": 90}

    def test_extracts_first_balanced_object(self):
        text = 'analysis first\\n{"score": 70, "nested": {"ok": true}}\\nthanks'
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
        mock_run.return_value = MagicMock(returncode=0, stdout="hello\\n", stderr="")
        result = GrokCliProvider().generate_text("SYSTEM", "USER", timeout=30)
        assert result == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_providers.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'providers'`.

- [ ] **Step 3: Implement provider base**

Create `providers/base.py`:

```python
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
```

Create `providers/__init__.py`:

```python
from providers.base import ProviderClient, ProviderError, ProviderStatus
from providers.claude_cli import ClaudeCliProvider
from providers.grok_cli import GrokCliProvider

__all__ = [
    "ProviderClient",
    "ProviderError",
    "ProviderStatus",
    "ClaudeCliProvider",
    "GrokCliProvider",
]
```

- [ ] **Step 4: Implement shared CLI provider**

Create `providers/cli.py`:

```python
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
        return f"{system_prompt.strip()}\\n\\nUser request:\\n{user_prompt.strip()}".strip()

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

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict:
        code, stdout, stderr = self._run(self._json_command(system_prompt, user_prompt), timeout=timeout)
        if code != 0:
            detail = (stderr or stdout or "unknown provider error").strip()
            return {"error": f"{self.name} error: {detail}"}
        return extract_json_object(stdout)

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> str:
        code, stdout, stderr = self._run(self._text_command(system_prompt, user_prompt), timeout=timeout)
        if code != 0:
            detail = (stderr or stdout or "unknown provider error").strip()
            return f"{self.name} error: {detail}"
        return stdout.strip()

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        raise NotImplementedError

    def _text_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        raise NotImplementedError
```

- [ ] **Step 5: Implement Claude CLI provider**

Create `providers/claude_cli.py`:

```python
from __future__ import annotations

from providers.cli import CliProvider


class ClaudeCliProvider(CliProvider):
    name = "Claude CLI"
    command = "claude"
    supports_curator = False

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        prompt = self._prompt(
            system_prompt + "\\n\\nReturn only one valid JSON object. Do not wrap it in markdown.",
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
```

- [ ] **Step 6: Implement Grok CLI provider**

Create `providers/grok_cli.py`:

```python
from __future__ import annotations

from providers.cli import CliProvider


class GrokCliProvider(CliProvider):
    name = "Grok CLI"
    command = "grok"
    supports_curator = True

    def _json_command(self, system_prompt: str, user_prompt: str) -> list[str]:
        prompt = self._prompt(
            system_prompt + "\\n\\nReturn only one valid JSON object. Do not wrap it in markdown.",
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
```

- [ ] **Step 7: Run provider tests**

Run:

```bash
pytest tests/test_providers.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit Task 1**

```bash
git add providers tests/test_providers.py
git commit -m "feat: add local CLI providers"
```

---

### Task 2: xAI API Provider And Compatibility Facade

**Files:**
- Create: `providers/xai_api.py`
- Modify: `grok_client.py`
- Test: `tests/test_provider_facade.py`
- Modify tests only if existing `tests/test_grok_client.py` imports need patch paths updated.

**Interfaces:**
- Consumes: `ProviderClient.generate_json`, `ProviderClient.generate_text`.
- Produces: `XaiApiProvider(api_key: str, model: str)`, `GrokClient(api_key: str = "", model: str = "", provider: ProviderClient | None = None)`.
- Preserves existing methods: `optimize_post`, `generate_ideas`, `curate_feed`, `optimize_thread`, `plan_schedule`, `check_risk`, `compare_posts`.

- [ ] **Step 1: Write failing facade tests**

Create `tests/test_provider_facade.py`:

```python
from unittest.mock import MagicMock

from grok_client import GrokClient


class TestProviderFacade:
    def test_optimize_post_delegates_to_provider(self):
        provider = MagicMock()
        provider.generate_json.return_value = {"score": 91}
        client = GrokClient(provider=provider)

        result = client.optimize_post("hello", image_desc="screenshot", hashtags="#ai")

        assert result == {"score": 91}
        system_prompt, user_prompt = provider.generate_json.call_args.args[:2]
        assert "포스트 내용" in user_prompt
        assert "screenshot" in user_prompt
        assert "#ai" in user_prompt
        assert isinstance(system_prompt, str)

    def test_generate_ideas_delegates_to_provider(self):
        provider = MagicMock()
        provider.generate_json.return_value = {"ideas": [{"title": "A"}]}
        client = GrokClient(provider=provider)

        result = client.generate_ideas("AI", length=300)

        assert result["ideas"][0]["title"] == "A"
        user_prompt = provider.generate_json.call_args.args[1]
        assert "AI" in user_prompt

    def test_curate_feed_uses_provider_method_when_available(self):
        provider = MagicMock()
        provider.curate_feed.return_value = {"recommendations": [{"summary": "Post"}]}
        client = GrokClient(provider=provider)

        result = client.curate_feed("AI")

        assert result["recommendations"][0]["summary"] == "Post"
        provider.curate_feed.assert_called_once_with("AI")

    def test_curate_feed_fallback_when_provider_lacks_real_time_search(self):
        provider = MagicMock()
        provider.supports_curator = False
        provider.generate_json.return_value = {
            "recommendations": [
                {
                    "summary": "Search for AI founders",
                    "why_recommended": "Claude-only fallback",
                    "search_keywords": "AI founders",
                    "suggested_reply": "Great point. What changed your mind?",
                    "engagement_hint": "Use this after checking X manually.",
                }
            ]
        }
        client = GrokClient(provider=provider)

        result = client.curate_feed("AI founders")

        assert result["recommendations"][0]["search_keywords"] == "AI founders"
        assert provider.generate_json.called
```

- [ ] **Step 2: Run facade test to verify it fails**

Run:

```bash
pytest tests/test_provider_facade.py -v
```

Expected: FAIL because `GrokClient.__init__` does not accept `provider`.

- [ ] **Step 3: Implement xAI API provider by moving current API behavior**

Create `providers/xai_api.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta

import openai

from i18n import (
    get_content_language_pair,
    get_lang,
    get_lang_instruction,
    get_output_language_name,
)
from providers.base import ProviderStatus
from utils import contains_hangul, parse_grok_json
from xalgo_prompts import CURATOR_SYSTEM_PROMPT


class XaiApiProvider:
    name = "xAI API"
    supports_curator = True

    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
        self.model = model

    def is_available(self) -> ProviderStatus:
        return ProviderStatus(bool(self.client), "xAI API configured")

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                timeout=timeout,
            )
            return parse_grok_json(response.choices[0].message.content or "")
        except openai.OpenAIError as e:
            return {"error": f"xAI API error: {str(e)}"}

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=timeout,
            )
            return (response.choices[0].message.content or "").strip()
        except openai.OpenAIError as e:
            return f"xAI API error: {str(e)}"

    def curate_feed(self, interests: str) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        output_lang_name = get_output_language_name()
        system_prompt = CURATOR_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            language_pair=get_content_language_pair(),
            output_language=output_lang_name,
        )
        today = datetime.now()
        from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        user_content = (
            f"User interests: {interests}\\n\\n"
            f"Output language for ALL JSON text values: {output_lang_name}. "
            f"This applies to suggested_reply and every other field — do not match "
            f"the source post's language."
        )

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt + get_lang_instruction()},
                    {"role": "user", "content": user_content},
                ],
                tools=[{"type": "x_search", "from_date": from_date, "to_date": to_date}],
                text={"format": {"type": "json_object"}},
            )
            text_content = ""
            for item in response.output:
                if getattr(item, "type", None) == "message":
                    for part in getattr(item, "content", []):
                        if hasattr(part, "text"):
                            text_content = part.text
            result = parse_grok_json(text_content)
            self._fix_korean_leakage(result)
            return result
        except openai.OpenAIError as e:
            return {"error": f"xAI API error: {str(e)}"}

    def _fix_korean_leakage(self, result: dict) -> None:
        if get_lang() == "ko":
            return
        recs = result.get("recommendations")
        if not isinstance(recs, list):
            return
        target_lang = get_output_language_name()
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            reply = rec.get("suggested_reply", "")
            if not isinstance(reply, str) or not contains_hangul(reply):
                continue
            translated = self._translate_reply(reply, target_lang)
            if translated:
                rec["suggested_reply"] = translated

    def _translate_reply(self, text: str, target_lang: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a translator. Rewrite the user's text in natural, "
                            f"casual {target_lang} suitable for a social media reply. "
                            f"Preserve tone and emojis. Output ONLY the translated text, "
                            f"no quotes, no explanations."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except openai.OpenAIError:
            return ""
```

- [ ] **Step 4: Refactor `grok_client.py` into compatibility facade**

Replace direct SDK calls in `grok_client.py` with this facade skeleton, preserving existing prompt construction:

```python
from datetime import datetime

from providers.xai_api import XaiApiProvider
from utils import parse_thread_text
from i18n import get_lang_instruction
from xalgo_prompts import (
    OPTIMIZER_SYSTEM_PROMPT,
    IDEAS_SYSTEM_PROMPT,
    CURATOR_SYSTEM_PROMPT,
    THREAD_SYSTEM_PROMPT,
    SCHEDULER_SYSTEM_PROMPT,
    AB_COMPARE_SYSTEM_PROMPT,
    RISK_CHECK_SYSTEM_PROMPT,
)


class GrokClient:
    def __init__(self, api_key: str = "", model: str = "grok-4.1-fast-reasoning", provider=None):
        self.provider = provider or XaiApiProvider(api_key=api_key, model=model)
        self.model = model
        self.client = getattr(self.provider, "client", None)

    def optimize_post(self, text: str, image_desc: str = "", hashtags: str = "") -> dict:
        user_content = f"포스트 내용:\\n{text}"
        if image_desc:
            user_content += f"\\n\\n이미지 설명: {image_desc}"
        if hashtags:
            user_content += f"\\n\\n해시태그: {hashtags}"
        return self.provider.generate_json(OPTIMIZER_SYSTEM_PROMPT + get_lang_instruction(), user_content)

    def generate_ideas(self, keywords: str, length: int = 0) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        if length and length > 0:
            length_instruction = (
                f"**분량: 반드시 정확히 약 {length}자(±10% 이내)**. "
                f"사용자가 직접 지정한 분량이므로 엄격하게 지키세요. "
                f"한두 줄로 끝내지 마세요. 구체적인 예시, 수치, 경험을 포함하여 충실하게 작성하세요."
            )
        else:
            length_instruction = (
                "**분량: 반드시 200~500자**. "
                "한두 줄로 끝내지 마세요. 구체적인 예시, 수치, 경험을 포함하여 충실하게 작성하세요."
            )
        system_prompt = IDEAS_SYSTEM_PROMPT.format(
            current_date_kr=current_date_kr,
            length_instruction=length_instruction,
        )
        return self.provider.generate_json(
            system_prompt + get_lang_instruction(),
            f"관심사/키워드: {keywords}",
        )

    def curate_feed(self, interests: str) -> dict:
        if hasattr(self.provider, "curate_feed") and getattr(self.provider, "supports_curator", False):
            return self.provider.curate_feed(interests)
        system_prompt = CURATOR_SYSTEM_PROMPT.format(
            current_date_kr=datetime.now().strftime("%Y년 %m월 %d일"),
            language_pair="Korean and English",
            output_language="Korean",
        )
        user_prompt = (
            f"관심사: {interests}\\n\\n"
            "You cannot access live X search in this mode. Generate 3 manual search recommendations "
            "with summary, why_recommended, search_keywords, suggested_reply, and engagement_hint. "
            "Do not claim that these are real-time posts."
        )
        return self.provider.generate_json(system_prompt + get_lang_instruction(), user_prompt)

    def optimize_thread(self, thread_text: str) -> dict:
        tweets = parse_thread_text(thread_text)
        if len(tweets) < 2:
            return {"error": "스레드는 최소 2개 이상의 트윗이 필요합니다. --- 또는 빈 줄로 구분하세요."}
        parts = [f"[트윗 {i+1}]\\n{t}" for i, t in enumerate(tweets)]
        user_content = f"스레드 분석 요청 (총 {len(tweets)}개 트윗):\\n\\n" + "\\n\\n".join(parts)
        return self.provider.generate_json(THREAD_SYSTEM_PROMPT + get_lang_instruction(), user_content)

    def plan_schedule(self, posts_info: list) -> dict:
        current_date_kr = datetime.now().strftime("%Y년 %m월 %d일")
        system_prompt = SCHEDULER_SYSTEM_PROMPT.format(current_date_kr=current_date_kr)
        parts = []
        for i, info in enumerate(posts_info):
            topic = info.get("topic", "").strip()
            content = info.get("content", "").strip()
            part = f"[포스트 {i+1}]\\n주제: {topic or '미정'}"
            if content:
                part += f"\\n내용: {content}"
            parts.append(part)
        user_content = f"스케줄 최적화 요청 (총 {len(posts_info)}개 포스트):\\n\\n" + "\\n\\n".join(parts)
        return self.provider.generate_json(system_prompt + get_lang_instruction(), user_content)

    def check_risk(self, text: str, image_desc: str = "") -> dict:
        user_content = f"포스트 내용:\\n{text}"
        if image_desc:
            user_content += f"\\n\\n이미지 설명: {image_desc}"
        return self.provider.generate_json(RISK_CHECK_SYSTEM_PROMPT + get_lang_instruction(), user_content)

    def compare_posts(self, post_a: str, post_b: str) -> dict:
        user_content = f"두 포스트를 비교 분석해주세요:\\n\\n=== 포스트 A ===\\n{post_a}\\n\\n=== 포스트 B ===\\n{post_b}"
        return self.provider.generate_json(AB_COMPARE_SYSTEM_PROMPT + get_lang_instruction(), user_content)
```

- [ ] **Step 5: Run facade and existing Grok tests**

Run:

```bash
pytest tests/test_provider_facade.py tests/test_grok_client.py -v
```

Expected: PASS. If tests patching `grok_client.openai.OpenAI` fail because OpenAI construction moved, update those tests to patch `providers.xai_api.openai.OpenAI`.

- [ ] **Step 6: Commit Task 2**

```bash
git add providers/xai_api.py grok_client.py tests/test_provider_facade.py tests/test_grok_client.py
git commit -m "refactor: route generation through providers"
```

---

### Task 3: Streamlit Engine Selection And Tab Routing

**Files:**
- Modify: `app.py`
- Modify: `tabs/tab_curator.py`
- Modify: `i18n.py`
- Test: `tests/test_provider_selection.py`

**Interfaces:**
- Consumes: `ClaudeCliProvider`, `GrokCliProvider`, `XaiApiProvider`, `GrokClient(provider=...)`.
- Produces: `build_provider(engine: str, api_key: str, model: str) -> tuple[GrokClient | None, ProviderStatus]` in `app.py` or a new `provider_selection.py`.

- [ ] **Step 1: Write failing provider selection tests**

Create `tests/test_provider_selection.py`:

```python
from unittest.mock import MagicMock, patch

from provider_selection import build_provider


class TestBuildProvider:
    @patch("provider_selection.ClaudeCliProvider")
    def test_builds_claude_cli_provider(self, provider_cls):
        provider = MagicMock()
        provider.is_available.return_value.available = True
        provider.is_available.return_value.message = "ready"
        provider_cls.return_value = provider

        client, status = build_provider("Claude CLI", api_key="", model="")

        assert client is not None
        assert status.available is True
        provider_cls.assert_called_once()

    @patch("provider_selection.GrokCliProvider")
    def test_builds_grok_cli_provider(self, provider_cls):
        provider = MagicMock()
        provider.is_available.return_value.available = True
        provider.is_available.return_value.message = "ready"
        provider_cls.return_value = provider

        client, status = build_provider("Grok CLI", api_key="", model="")

        assert client is not None
        assert status.available is True

    def test_demo_returns_no_client(self):
        client, status = build_provider("Demo", api_key="", model="")
        assert client is None
        assert status.available is False
        assert "demo" in status.message.lower()

    def test_xai_api_requires_key(self):
        client, status = build_provider("xAI API", api_key="", model="grok-4.3")
        assert client is None
        assert status.available is False
        assert "api key" in status.message.lower()
```

- [ ] **Step 2: Run selection tests to verify they fail**

Run:

```bash
pytest tests/test_provider_selection.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'provider_selection'`.

- [ ] **Step 3: Implement provider selection helper**

Create `provider_selection.py`:

```python
from __future__ import annotations

from grok_client import GrokClient
from providers.base import ProviderStatus
from providers.claude_cli import ClaudeCliProvider
from providers.grok_cli import GrokCliProvider
from providers.xai_api import XaiApiProvider


ENGINE_OPTIONS = ["Claude CLI", "Grok CLI", "xAI API", "Demo"]


def build_provider(engine: str, api_key: str = "", model: str = "grok-4.3") -> tuple[GrokClient | None, ProviderStatus]:
    if engine == "Demo":
        return None, ProviderStatus(False, "Demo mode")
    if engine == "Claude CLI":
        provider = ClaudeCliProvider()
    elif engine == "Grok CLI":
        provider = GrokCliProvider()
    elif engine == "xAI API":
        if not api_key:
            return None, ProviderStatus(False, "xAI API key required")
        provider = XaiApiProvider(api_key=api_key, model=model)
    else:
        return None, ProviderStatus(False, f"Unknown engine: {engine}")

    status = provider.is_available()
    if not status.available:
        return None, status
    return GrokClient(provider=provider, model=model), status
```

- [ ] **Step 4: Add i18n labels**

In `i18n.py`, add these keys near app-level labels:

```python
    "ai_engine_section": {
        "ko": "AI ENGINE",
        "en": "AI ENGINE",
        "ja": "AI ENGINE",
    },
    "ai_engine_label": {
        "ko": "실행 엔진",
        "en": "AI engine",
        "ja": "実行エンジン",
    },
    "provider_status_ready": {
        "ko": "사용 가능",
        "en": "Ready",
        "ja": "使用可能",
    },
    "provider_status_unavailable": {
        "ko": "사용할 수 없음",
        "en": "Unavailable",
        "ja": "使用不可",
    },
    "local_generation_needed": {
        "ko": "로컬 생성을 사용하려면 Claude 또는 Grok CLI 로그인이 필요합니다.",
        "en": "Local generation requires a logged-in Claude or Grok CLI.",
        "ja": "ローカル生成にはClaudeまたはGrok CLIのログインが必要です。",
    },
    "curator_fallback_notice": {
        "ko": "현재 엔진은 실시간 X 검색을 사용할 수 없어 검색 키워드와 답글 초안만 생성합니다.",
        "en": "The current engine cannot use live X search, so it will generate search keywords and reply drafts only.",
        "ja": "現在のエンジンではリアルタイムX検索を使用できないため、検索キーワードと返信案のみ生成します。",
    },
```

- [ ] **Step 5: Wire sidebar in `app.py`**

In `app.py`, import the helper:

```python
from provider_selection import ENGINE_OPTIONS, build_provider
```

Replace the `API CONNECTION` sidebar block with:

```python
    with st.container(border=True):
        st.markdown(
            '<span class="sidebar-section-label">AI ENGINE</span>',
            unsafe_allow_html=True,
        )

        engine = st.selectbox(
            t("ai_engine_label"),
            ENGINE_OPTIONS,
            index=0,
            key="ai_engine",
        )

        api_key = ""
        remember_key = False
        saved_key = st.session_state.get("_saved_api_key", "")
        if engine == "xAI API":
            api_key = _untracked_text_input(
                t("api_key_label"),
                type="password",
                help=t("api_key_help"),
                placeholder="xai-...",
                value=saved_key,
            )
            remember_key = st.checkbox(
                t("api_key_remember"),
                value=bool(saved_key),
                help=t("api_key_remember_help"),
            )
            if remember_key and api_key and api_key != saved_key:
                cookie_manager.set(COOKIE_KEY, api_key, key="save_cookie")
                st.session_state._saved_api_key = api_key
            elif not remember_key and saved_key:
                cookie_manager.delete(COOKIE_KEY, key="delete_cookie")
                st.session_state._saved_api_key = ""
            st.caption(t("api_key_privacy"))

        model = st.selectbox(
            t("model_select"),
            ["grok-4.3", "grok-build-0.1", "grok-4.1-fast-reasoning", "grok-4.20-reasoning"],
            help=t("model_help"),
        )
```

Replace current Grok client initialization with:

```python
grok, provider_status = build_provider(
    st.session_state.get("ai_engine", "Claude CLI"),
    api_key=api_key,
    model=model,
)
if provider_status.available:
    st.sidebar.success(f"{t('provider_status_ready')}: {provider_status.message}")
else:
    st.sidebar.info(f"{t('provider_status_unavailable')}: {provider_status.message}")
```

Keep the existing demo mode injection when `grok is None`.

- [ ] **Step 6: Add curator fallback notice**

In `tabs/tab_curator.py`, after `if grok is None`, add:

```python
    elif not getattr(getattr(grok, "provider", None), "supports_curator", False):
        st.info(t("curator_fallback_notice"))
```

- [ ] **Step 7: Run focused tests**

Run:

```bash
pytest tests/test_provider_selection.py tests/test_provider_facade.py tests/test_utils.py -v
```

Expected: PASS.

- [ ] **Step 8: Run app import smoke test**

Run:

```bash
python3 -m py_compile app.py provider_selection.py grok_client.py providers/*.py tabs/tab_curator.py i18n.py
```

Expected: PASS with no output.

- [ ] **Step 9: Commit Task 3**

```bash
git add app.py provider_selection.py tabs/tab_curator.py i18n.py tests/test_provider_selection.py
git commit -m "feat: add AI engine selection"
```

---

### Task 4: Copy-First Image Prompt Workflow

**Files:**
- Create: `image_client.py`
- Modify: `tabs/tab_ideas.py`
- Modify: `i18n.py`
- Modify: `.gitignore`
- Test: `tests/test_image_workflow.py`

**Interfaces:**
- Produces: `build_copy_prompt(post_content: str, image_prompt: str) -> str`.
- Consumes: existing `idea["content"]` and `idea["image_prompt"]`.

- [ ] **Step 1: Write failing image workflow tests**

Create `tests/test_image_workflow.py`:

```python
from image_client import build_copy_prompt


class TestBuildCopyPrompt:
    def test_combines_post_context_and_image_prompt(self):
        result = build_copy_prompt("Post about weekend writing", "A cozy desk, no text")
        assert "Post about weekend writing" in result
        assert "A cozy desk, no text" in result
        assert "no text" in result

    def test_handles_empty_post_content(self):
        result = build_copy_prompt("", "A cinematic portrait")
        assert result.startswith("Create an image")
        assert "A cinematic portrait" in result
```

- [ ] **Step 2: Run image tests to verify they fail**

Run:

```bash
pytest tests/test_image_workflow.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'image_client'`.

- [ ] **Step 3: Implement image prompt helper**

Create `image_client.py`:

```python
from __future__ import annotations


def build_copy_prompt(post_content: str, image_prompt: str) -> str:
    post_content = post_content.strip()
    image_prompt = image_prompt.strip()
    if post_content:
        return (
            "Create an image for this X post. Do not include readable text, letters, UI captions, "
            "watermarks, or logos unless explicitly requested.\\n\\n"
            f"Post context:\\n{post_content}\\n\\n"
            f"Image prompt:\\n{image_prompt}"
        )
    return (
        "Create an image from this prompt. Do not include readable text, letters, UI captions, "
        "watermarks, or logos unless explicitly requested.\\n\\n"
        f"Image prompt:\\n{image_prompt}"
    )
```

- [ ] **Step 4: Add i18n labels for image prompt controls**

In `i18n.py`, add:

```python
    "ideas_copy_image_prompt_title": {
        "ko": "복사용 이미지 생성 프롬프트",
        "en": "Copy-ready image prompt",
        "ja": "コピー用画像生成プロンプト",
    },
    "ideas_copy_image_prompt_caption": {
        "ko": "ChatGPT, Grok Imagine, Gemini 등에 붙여넣어 사용하세요.",
        "en": "Paste this into ChatGPT, Grok Imagine, Gemini, or another image tool.",
        "ja": "ChatGPT、Grok Imagine、Geminiなどに貼り付けて使用してください。",
    },
```

- [ ] **Step 5: Wire copy prompt into `tabs/tab_ideas.py`**

Import helper:

```python
from image_client import build_copy_prompt
```

Replace the existing image prompt render block:

```python
                if image_prompt:
                    st.markdown(f"**{t('ideas_image_prompt_title')}**")
                    st.caption(t("ideas_image_prompt_caption"))
                    st.code(image_prompt, language="", wrap_lines=True)
```

with:

```python
                if image_prompt:
                    st.markdown(f"**{t('ideas_image_prompt_title')}**")
                    st.caption(t("ideas_image_prompt_caption"))
                    st.code(image_prompt, language="", wrap_lines=True)

                    copy_prompt = build_copy_prompt(content, image_prompt)
                    st.markdown(f"**{t('ideas_copy_image_prompt_title')}**")
                    st.caption(t("ideas_copy_image_prompt_caption"))
                    st.code(copy_prompt, language="", wrap_lines=True)
```

- [ ] **Step 6: Ignore generated image output directory**

Add to `.gitignore`:

```gitignore
generated_images/
```

- [ ] **Step 7: Run image workflow tests**

Run:

```bash
pytest tests/test_image_workflow.py tests/test_utils.py -v
```

Expected: PASS.

- [ ] **Step 8: Run full test suite**

Run:

```bash
pytest -v
```

Expected: PASS.

- [ ] **Step 9: Commit Task 4**

```bash
git add image_client.py tabs/tab_ideas.py i18n.py .gitignore tests/test_image_workflow.py
git commit -m "feat: add copy-ready image prompts"
```

---

## Self-Review

Spec coverage:

- Local Claude/Grok CLI support is covered by Task 1 and Task 3.
- Existing xAI API path is covered by Task 2.
- Demo mode preservation is covered by Task 3.
- Curator routing and fallback are covered by Task 2 and Task 3.
- Copy-first image workflow is covered by Task 4.
- Optional API image generation is intentionally deferred after the copy-first workflow, matching the phased spec.
- Hosted deployment CLI disabling is represented by provider status and local-only wording; implementation can later add environment detection if Streamlit Cloud deployment needs it.

Placeholder scan:

- No TBD/TODO/fill-later placeholders.
- Every task has concrete files, interfaces, tests, commands, and commit steps.

Type consistency:

- `ProviderStatus.available` and `ProviderStatus.message` are used consistently.
- `generate_json(system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict` is used consistently.
- `GrokClient(provider=...)` facade is used consistently by provider selection and tests.

