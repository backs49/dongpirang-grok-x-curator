# Local AI Provider Mode Design

## Summary

Dongpirang Grok X Curator currently requires a Grok/xAI API key before users can generate real results. The new design changes the app from a Grok-key-only Streamlit app into a local AI provider selector that can use locally authenticated AI CLIs, while preserving the existing xAI API path for Grok-specific features.

The primary local workflow is:

- Writing, analysis, thread optimization, scheduling, A/B comparison, and risk checks use the locally installed `claude` CLI by default.
- X real-time curation uses `grok` CLI or xAI API because it depends on Grok/X search capabilities.
- Image support starts with high-quality prompt copy workflows and later adds optional xAI Imagine/OpenAI image generation when API keys are available.

This design intentionally separates local subscription-backed CLI execution from direct API execution. CLI providers can use the user's local OAuth/subscription state. API providers continue to require their own API keys.

## Goals

- Let local users generate recommendations without entering a Grok API key when `claude` or `grok` CLI is already authenticated.
- Keep the existing xAI API mode for users who want direct API usage or X search through official xAI tools.
- Make provider choice explicit and inspectable in the sidebar.
- Preserve existing demo mode for visitors with no configured provider.
- Add an image workflow that is useful without an API key and expandable when xAI/OpenAI image APIs are configured.

## Non-Goals

- Do not scrape or automate the Claude, ChatGPT, or Grok web UI.
- Do not attempt to reuse ChatGPT Plus/Pro browser sessions as an API.
- Do not remove the existing xAI API path.
- Do not implement a full local model/Ollama provider in the first pass.
- Do not change the existing output schemas for tabs unless a schema is already broken.

## Current Context

The existing app is a Streamlit application centered on `GrokClient`. `GrokClient` uses the OpenAI Python SDK with `base_url="https://api.x.ai/v1"`. Most tabs follow a common contract: build a system/user prompt, request JSON, parse JSON, and render the result.

The exception is the curator tab, which depends on xAI's `x_search` tool. That dependency should remain Grok/xAI-oriented rather than being forced through Claude.

Local verification found both CLIs installed and usable in headless mode:

- `claude -p "Reply with exactly OK"` returned `OK`.
- `grok -p "Reply with exactly OK"` returned `OK` when allowed to write its normal user-level session files.

xAI documentation confirms:

- Grok Build can run interactively, headlessly, or via API.
- `grok-build-0.1` is available through the xAI API.
- xAI supports OpenAI-compatible API usage.
- xAI Imagine image generation is available through `grok-imagine-image-quality`.
- X Search is available as the `x_search` tool through xAI SDK/API-compatible flows.

## Architecture

Replace the single-purpose `GrokClient` role with provider-oriented clients.

Proposed modules:

- `providers/base.py`: common provider protocol and result types.
- `providers/claude_cli.py`: local Claude CLI provider.
- `providers/grok_cli.py`: local Grok Build CLI provider.
- `providers/xai_api.py`: direct xAI API provider, adapted from the current `GrokClient`.
- `image_client.py`: image prompt copy helpers and optional API image generation.

The app should instantiate one text provider and, where needed, one Grok-capable curation provider. Provider selection is controlled in the sidebar.

Common provider interface:

```python
class ProviderClient:
    name: str

    def is_available(self) -> tuple[bool, str]:
        ...

    def generate_json(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> dict:
        ...

    def generate_text(self, system_prompt: str, user_prompt: str, *, timeout: int = 120) -> str:
        ...
```

The interface should hide whether the backend is a CLI subprocess or an SDK/API call. Tab code should not build subprocess commands directly.

## Provider Behavior

### Claude CLI

Claude CLI is the default local writing provider.

It should call `claude -p` in non-interactive mode with:

- a strict system prompt requesting JSON only for structured tabs,
- no file-editing tools,
- no session persistence where possible,
- a timeout,
- the current project directory as working directory.

Expected usage:

- post optimization,
- idea generation,
- thread optimization,
- schedule planning,
- A/B comparison,
- risk checks.

Claude CLI should not be the primary implementation for X real-time search because it does not expose xAI's `x_search` tool.

### Grok CLI

Grok CLI is the default local provider for Grok-specific behavior and an optional text provider.

It should call `grok -p` in headless mode with:

- plain or JSON output,
- no unnecessary tools,
- a timeout,
- the current project directory as working directory.

Expected usage:

- X curator mode when local Grok auth is available,
- fallback text generation if the user prefers Grok Build,
- future Grok-specific workflows.

Grok may write session files under the user's home directory. This is expected outside the sandboxed test environment.

### xAI API

xAI API preserves the current Grok API behavior and enables official tool use.

It should keep OpenAI-compatible usage for:

- text responses,
- structured outputs,
- `x_search`,
- image generation with `grok-imagine-image-quality`.

The existing `GrokClient` methods can be migrated into this provider in small steps.

### Demo

Demo remains the no-configuration fallback. If no provider is available, the app should keep showing preset results and explain what is needed to enable local generation.

## Sidebar UI

Rename the current `API CONNECTION` section to `AI ENGINE`.

Controls:

- provider selectbox: `Claude CLI`, `Grok CLI`, `xAI API`, `Demo`.
- provider status line: available, unavailable, login needed, or API key needed.
- optional xAI API key field, shown only when `xAI API` or xAI image generation is enabled.
- optional OpenAI API key field for future OpenAI image generation.
- model selector scoped to the selected provider.

The selected provider should be stored in `st.session_state` so tab reruns do not reset user choice.

## Tab Routing

Default tab routing:

- Optimizer: selected text provider, default Claude CLI.
- Ideas: selected text provider, default Claude CLI.
- Thread: selected text provider, default Claude CLI.
- Scheduler: selected text provider, default Claude CLI.
- A/B compare: selected text provider, default Claude CLI.
- Risk check: selected text provider, default Claude CLI.
- Curator: Grok CLI or xAI API preferred.
- Unfollow: local logic unchanged.

When the selected provider cannot support a tab, the tab should show a focused fallback:

- If curator has no Grok-capable provider, generate search keywords and suggested replies without claiming real-time X search.
- If no text provider is available, keep demo mode active.

## Image Workflow

The first implementation should improve the current image prompt workflow without requiring image API credentials.

In the Ideas tab, each generated idea already includes `image_prompt`. Add controls below that prompt:

- copy-ready prompt display,
- optional "Generate with xAI Imagine" when xAI API credentials are available,
- optional "Generate with OpenAI Image API" when OpenAI API credentials are available.

Generated images should be displayed inline. If the API returns temporary URLs, the app should download images promptly and save them under `generated_images/` with stable local filenames.

The app should not promise ChatGPT/Codex subscription-backed image generation through an API unless an official local CLI or API path is verified later. Without API credentials, the supported workflow is prompt copy into ChatGPT, Grok Imagine, or another subscribed UI.

## Error Handling

Provider availability:

- Missing `claude` command: mark Claude CLI unavailable.
- Missing `grok` command: mark Grok CLI unavailable.
- OAuth/login expired: show provider-specific login guidance.
- API key missing: hide API-only generation buttons and show API key guidance.

CLI execution:

- Timeout: show a short timeout error and preserve previous result.
- Non-zero exit: show stderr summary without leaking secrets.
- JSON parse failure: try extracting the first JSON object from the output; if that fails, show a parse error and keep raw output in an expander for local debugging.

API execution:

- Authentication failure: ask for the relevant API key.
- Rate limit/quota failure: show a quota message.
- Network failure: show a retry-later message.
- Image URL expiration: save images locally as soon as they are returned.

## Testing Strategy

Unit tests:

- provider command construction,
- JSON extraction from CLI output,
- provider availability checks,
- tab routing decisions,
- image prompt handling.

Mock tests:

- mock `subprocess.run` for Claude/Grok success, failure, timeout, and malformed JSON.
- mock xAI/OpenAI API clients for image URL and base64 responses.

Regression tests:

- API-key-free demo mode still renders preset results.
- Claude CLI provider can produce expected JSON when subprocess output is valid.
- Curator does not claim real-time X search unless Grok CLI or xAI API is selected.

## Implementation Phases

### Phase 1: Local Text Provider Mode

- Add provider abstraction.
- Add Claude CLI provider.
- Add Grok CLI provider.
- Wire Optimizer, Ideas, Thread, Scheduler, A/B, and Risk tabs through the selected text provider.
- Keep the current xAI API behavior available.
- Preserve demo mode.

### Phase 2: Curator Routing

- Route curator through Grok CLI or xAI API.
- Add Claude-only curator fallback that generates search keywords and reply drafts without real-time X claims.
- Update i18n copy so the app no longer says every generated result comes from Grok.

### Phase 3: Image Workflow

- Add copy-first image prompt controls.
- Add optional xAI Imagine API generation.
- Add local image saving for temporary URLs.
- Add optional OpenAI Image API generation if credentials are configured.

### Phase 4: Provider Expansion

- Add OpenAI-compatible custom provider configuration.
- Consider Ollama/local model support if useful.
- Add provider health checks to the sidebar.

## Design Decisions

- When both Claude CLI and Grok CLI are available, default writing tasks to Claude CLI and curator tasks to Grok CLI.
- Store generated images under `generated_images/` and add that directory to `.gitignore` during implementation.
- Treat local CLI providers as local-only. Hide or disable them in hosted Streamlit deployments where the CLIs and user OAuth state are unavailable.
