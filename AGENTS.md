# AGENTS.md

Codex should use this file as the durable project guidance for this repository.

## Project Overview

This is a Streamlit app for X post optimization and curation. It started as a Grok/xAI API-key based app and now supports a local provider mode:

- Claude CLI for local subscription-backed writing and analysis.
- Grok CLI for local Grok Build workflows and Grok-specific curation.
- xAI API for direct Grok API usage, X Search, and future image API support.
- Demo mode when no provider is configured.

The app is Korean-first, with English and Japanese i18n support in `i18n.py`.

## Important Files

- `app.py`: Streamlit entrypoint, sidebar, provider selection, tab wiring.
- `provider_selection.py`: maps sidebar engine choices to provider-backed `GrokClient` instances.
- `grok_client.py`: compatibility facade preserving existing tab method names.
- `providers/`: provider implementations.
  - `base.py`: provider protocol, status type, JSON extraction.
  - `cli.py`: shared subprocess wrapper for local CLI providers.
  - `claude_cli.py`: Claude CLI provider.
  - `grok_cli.py`: Grok CLI provider.
  - `xai_api.py`: direct xAI API provider.
- `tabs/`: Streamlit tab renderers.
- `xalgo_prompts.py`: system prompts and expected JSON output contracts.
- `i18n.py`: UI copy and language instructions.
- `demo_data.py`: preset demo outputs for API-key-free use.
- `tests/`: pytest suite.

## Development Rules

- Preserve existing output schemas consumed by tab renderers unless the task explicitly changes them.
- Keep provider-specific logic inside `providers/` or `provider_selection.py`; tab files should call high-level client methods only.
- Do not scrape or automate Claude, ChatGPT, or Grok web UIs.
- Do not treat ChatGPT/Claude subscriptions as direct API keys. Local subscription usage should go through verified local CLIs.
- Keep xAI API support intact.
- Do not remove demo mode.
- Do not expose API keys to analytics. `app.py` intentionally uses the untracked `st.text_input` reference for API-key input.
- Avoid broad UI rewrites unless the user asks for design work.
- Keep Korean copy natural and friendly; update English and Japanese keys when adding new UI labels.

## Local Setup

Use an isolated virtual environment. The global Python on this machine may not have project dependencies installed.

```bash
python3 -m venv /private/tmp/dongpirang-grok-x-curator-venv
/private/tmp/dongpirang-grok-x-curator-venv/bin/python -m pip install -U pip
/private/tmp/dongpirang-grok-x-curator-venv/bin/python -m pip install -r requirements.txt pytest
```

## Test Commands

Run the full suite:

```bash
/private/tmp/dongpirang-grok-x-curator-venv/bin/python -m pytest -q
```

Compile smoke check for app/provider edits:

```bash
/private/tmp/dongpirang-grok-x-curator-venv/bin/python -m py_compile app.py provider_selection.py grok_client.py image_client.py providers/*.py tabs/*.py i18n.py
```

Run the app locally:

```bash
/private/tmp/dongpirang-grok-x-curator-venv/bin/python -m streamlit run app.py --server.headless true --server.port 8502
```

If the sandbox blocks local port binding, rerun with appropriate approval.

## Provider Notes

- `ClaudeCliProvider` should use `claude -p` with no tools and no session persistence where possible.
- `GrokCliProvider` should use `grok -p` with plain output and no unnecessary tools.
- `CodexCliProvider` should use `codex exec` with `--ephemeral`, a read-only sandbox, and `--output-last-message` to read the final answer cleanly (stdout carries progress logs).
- `XaiApiProvider` should remain OpenAI SDK compatible with `base_url="https://api.x.ai/v1"`.
- Curator real-time X search should only be claimed when using a Grok-capable provider.
- Claude-only curator fallback may generate search keywords and reply drafts, but must not claim live X search.

## Image Workflow

The image feature has two layers:

- Copy-first fallback: `image_client.build_copy_prompt` builds a paste-ready image prompt, shown in `tabs/tab_ideas.py` alongside the raw `image_prompt`.
- Direct generation: `image_client.build_image_client` auto-selects a backend — local Codex CLI (`providers/codex_cli_image.py`, official built-in `$imagegen` skill, subscription-backed, verified locally 2026-07) first, then the xAI image API (`providers/xai_image.py`, `images.generate` with `b64_json`) when an xAI key is set. With neither, the tab shows only the copy prompt.
- Video: `image_client.build_video_client` wraps `providers/xai_video.py` (async `POST /videos/generations` + polling; downloads the temporary mp4 URL immediately). Video has no CLI path — it requires an xAI API key. The ideas tab offers image-to-video from a generated image.
- Generated PNGs/MP4s are written to `generated_images/` (gitignored).

Codex CLI image generation is a verified official path (`codex exec` + `$imagegen`, gpt-image-2). Still do not scrape or automate the ChatGPT/Claude/Grok web UIs, and do not treat chat subscriptions as raw API keys.

## Publish Pipeline (stage 4)

- `content_queue.py`: JSON-file queue (`content_queue/queue.json`, gitignored) shared by the 발행 큐 tab and batch scripts. Slots: weekdays 08:00/19:00, Sat 10:00, Sunday off.
- `publisher.py`: OAuth 1.0a client for `POST /2/tweets`. Keys live in `.env` (gitignored) as X_API_KEY / X_API_KEY_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET. Never print or log key values.
- `scripts/publish_worker.py`: idempotent worker run by launchd at slot times. Dry-run by default; `--live` (or X_PUBLISH_LIVE=1) actually posts. Missed slots (>90min overdue) are reassigned, never force-posted.
- `scripts/com.dongpirang.publish.plist`: launchd template. Install only after a manual `--live` test succeeds:
  `cp scripts/com.dongpirang.publish.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.dongpirang.publish.plist`

## Git Hygiene

- The repo may contain untracked `.DS_Store` files. Do not remove or stage them unless the user asks.
- `docs/superpowers/` is gitignored; use `git add -f` only for approved spec/plan files that must be committed.
- Prefer small commits by task.
- Do not reset or revert user changes without explicit instruction.

