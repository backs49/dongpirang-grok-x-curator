# AGENTS.md

Codex should use this file as the durable project guidance for this repository.

## Project Overview

This is a Streamlit app for X post optimization and curation. It started as a Grok/xAI API-key based app and now supports a local provider mode. Sidebar engine order is `ENGINE_OPTIONS` in `provider_selection.py`, and the **first entry is the default**:

- **Grok CLI (default)** for local Grok Build workflows and Grok-specific curation; also the default image and video backend.
- Claude CLI for local subscription-backed writing and analysis.
- Codex CLI for local subscription-backed generation, including `$imagegen` images.
- xAI API for direct Grok API usage, X Search, and the image/video APIs.
- Demo mode when no provider is configured.

The app is Korean-first, with English and Japanese i18n support in `i18n.py`.

## Important Files

- `app.py`: Streamlit entrypoint, sidebar, provider selection, tab wiring.
- `provider_selection.py`: maps sidebar engine choices to provider-backed `GrokClient` instances.
- `grok_client.py`: compatibility facade preserving existing tab method names.
- `providers/`: provider implementations.
  - `base.py`: provider protocol, `ProviderStatus`, `ProviderError`, JSON extraction.
  - `cli.py`: shared subprocess wrapper for local CLI text providers.
  - Text: `claude_cli.py`, `grok_cli.py`, `codex_cli.py`, `xai_api.py`.
  - Media: `grok_cli_media.py` (image + video), `codex_cli_image.py`, `xai_image.py`, `xai_video.py`.
  - Text providers return error dicts; media providers raise `ProviderError`. See Error Conventions.
- `image_client.py`: `ImageClient`/`VideoClient` facades, backend selection, X-spec post-processing, `gen_log.jsonl`.
- `publisher.py`: OAuth 1.0a X publishing client.
- `content_queue.py`: JSON-file draft/material queue with publish slots.
- `ideas_history.py`: JSONL persistence for idea generation results (survives browser session loss).
- `design.py`: token-based CSS variable system, light/dark themes.
- `utils.py`: analytics CSV parsing, follower comparison, shared helpers.
- `tabs/`: Streamlit tab renderers.
- `scripts/`: launchd-driven batch jobs (publish worker, nightly drafts, tunnel watchdog, admin notifier).
- `xalgo_prompts.py`: system prompts and expected JSON output contracts.
- `i18n.py`: UI copy and language instructions.
- `demo_data.py`: preset demo outputs for API-key-free use.
- `assets/`: brand assets — mascot reference images used to keep generated images on-character.
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

## Error Conventions

Two conventions coexist. Match whichever the layer you are editing already uses — do not convert one to the other as a drive-by change.

- **Text generation** (`providers/cli.py`, `providers/xai_api.py` → `grok_client.py` → tabs): failures come back as `{"error": "..."}` dicts. Tab renderers check `if "error" in result` and call `st.error`. These paths do not raise, and the tabs do not wrap them in try/except.
- **Media generation and publishing** (`providers/grok_cli_media.py`, `codex_cli_image.py`, `xai_image.py`, `xai_video.py`, `publisher.py`): failures raise `ProviderError` from `providers/base.py`. The only handlers that terminate it are `tabs/tab_ideas.py` (image and video generation) and `scripts/publish_worker.py`. Handlers inside the providers themselves are re-raise guards, not terminal.

`image_client.py` does not catch `ProviderError` — it passes straight through the `ImageClient`/`VideoClient` facade to the caller. Any new caller must handle it. `tabs/tab_publish_queue.py` has no `ProviderError` handling because it never calls `publisher.post_text`; it only consumes the dict convention from `grok.draft_from_material`.

## Local Setup

The virtual environment lives at **`venv/` inside the repository** (already present on this machine; gitignored by its own auto-generated `venv/.gitignore`). The global Python does not have project dependencies installed. Run every command in this file from the repository root.

```bash
python3 -m venv venv
venv/bin/python -m pip install -U pip
venv/bin/python -m pip install -r requirements.txt pytest
```

Do **not** relocate the venv to `/tmp` or `/private/tmp` — macOS clears those on reboot, and all three launchd jobs hard-code the repo-local interpreter (`scripts/tunnel_watch.sh` sets `PYTHON="$REPO/venv/bin/python"`; the drafts and publish plists name it outright). A venv anywhere else leaves the batch jobs pointing at a missing binary.

## Test Commands

Run the full suite:

```bash
venv/bin/python -m pytest -q
```

Compile smoke check for app/provider edits:

```bash
venv/bin/python -m py_compile app.py provider_selection.py grok_client.py image_client.py providers/*.py tabs/*.py i18n.py
```

Run the app locally:

```bash
venv/bin/python -m streamlit run app.py --server.headless true --server.port 8503
```

Port map on this machine: **8501 is this app** (held by the launchd-managed instance that `scripts/tunnel_watch.sh` keeps alive), 8502 is the ai-trader dashboard. Use a free port such as 8503 for ad-hoc runs so you do not fight the managed instance.

If the sandbox blocks local port binding, rerun with appropriate approval.

## Provider Notes

- `ClaudeCliProvider` should use `claude -p` with no tools and no session persistence where possible.
- `GrokCliProvider` should use `grok -p` with plain output and no unnecessary tools.
- `CodexCliProvider` should use `codex exec` with `--ephemeral`, a read-only sandbox, and `--output-last-message` to read the final answer cleanly (stdout carries progress logs).
- `XaiApiProvider` should remain OpenAI SDK compatible with `base_url="https://api.x.ai/v1"`. `grok_client.py` instantiates it as the default provider when none is injected.
- Model tiers are pinned deliberately — this is copywriting, not frontier reasoning. `ClaudeCliProvider` pins `--model sonnet` (`DEFAULT_CLAUDE_MODEL`), `CodexCliProvider` and `CodexCliImageProvider` pin `model_reasoning_effort="medium"`, and `GrokCliProvider` passes no model flag because the Grok CLI exposes only one model. Do not raise these without a quality reason.
- Curator real-time X search should only be claimed when using a Grok-capable provider.
- Claude-only curator fallback may generate search keywords and reply drafts, but must not claim live X search.

## Image Workflow

The image feature has two layers:

- Copy-first fallback: `image_client.build_copy_prompt` builds a paste-ready image prompt, shown in `tabs/tab_ideas.py` alongside the raw `image_prompt`.
- Direct generation: `image_client.build_image_client` tries the engine picked in the sidebar first (**default Grok CLI**), then falls back Grok CLI → Codex CLI → xAI API. The CLI paths are subscription-backed (`providers/grok_cli_media.py` uses Grok Build CLI's Imagine `image_gen` tool; `providers/codex_cli_image.py` uses Codex CLI's built-in `$imagegen`), so neither bills a separate API. `providers/xai_image.py` (`images.generate` with `b64_json`) is the last resort and needs an xAI key. With no backend at all, the tab shows only the copy prompt.
- Video: `image_client.build_video_client` prefers the local Grok CLI (`GrokCliVideoProvider`, Imagine video tool; `image_to_video` when a source image is supplied), and falls back to `providers/xai_video.py` (async `POST /videos/generations` + polling; downloads the temporary mp4 URL immediately) when an xAI key is set. The ideas tab offers image-to-video from a generated image.
- Generated PNGs/MP4s are written to `generated_images/` (gitignored), with prompt and engine metadata appended to `generated_images/gen_log.jsonl` so past generations stay traceable after the UI session ends.
- Fixed brand mascot: `image_client.MASCOT_PATH` (`assets/mascot_dongpi.jpg`) anchors character consistency. `build_copy_prompt(..., mascot=True)` swaps in `_MASCOT_RULES`, and `ImageClient.generate(prompt, reference=...)` forwards the reference **only** to providers declaring `supports_reference` (currently Grok CLI). Other backends silently drop it, so mascot fidelity is engine-dependent; `gen_log.jsonl` records `mascot_ref` per generation.

Codex CLI image generation is a verified official path (`codex exec` + `$imagegen`, gpt-image-2). Still do not scrape or automate the ChatGPT/Claude/Grok web UIs, and do not treat chat subscriptions as raw API keys.

## Publish Pipeline (stage 4)

- `content_queue.py`: JSON-file queue (`content_queue/queue.json`, gitignored) shared by the 발행 큐 tab and batch scripts. Slots: weekdays 08:00/19:00, Sat 10:00, Sunday off.
- `publisher.py`: OAuth 1.0a client for `POST /2/tweets`. Keys live in `.env` (gitignored) as X_API_KEY / X_API_KEY_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET. Never print or log key values.
- `scripts/publish_worker.py`: idempotent worker run by launchd at slot times. Dry-run by default; `--live` (or X_PUBLISH_LIVE=1) actually posts. Missed slots (>90min overdue) are reassigned, never force-posted.
- `scripts/com.dongpirang.publish.plist`: launchd template. Install only after a manual `--live` test succeeds:
  `cp scripts/com.dongpirang.publish.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.dongpirang.publish.plist`
- `scripts/generate_drafts.py`: nightly draft batch (launchd 23:00 via `scripts/com.dongpirang.drafts.plist`). Skips when draft+approved stock ≥ 4; converts up to 3 unused materials into drafts; only when the inbox is empty does it add one tip draft from `settings.tip_keywords` in queue.json (default AI/솔로개발 keywords). Uses local CLI engines (Codex → Claude), so generation is free. All output stays in 'draft' status — publishing always requires user approval in the 발행 큐 tab.
- Stalled-approval reminder (same script, runs **before** the stock check so the skip path is still covered): when the oldest `draft`-status item has waited past `STALE_DRAFT_DAYS`, it telegrams the admin via `scripts/notify_admin.py` and stamps `reminders.stale_drafts_at` in queue.json. Re-sends are throttled to `REMINDER_INTERVAL_DAYS`; a failed send is deliberately **not** stamped so the next night retries. Only `draft` counts as waiting — `approved` items publish themselves on their slot, so they are not a human bottleneck. This exists because the approval gate used to fail silently: publishing stopped 2026-07-08 and nothing surfaced it for 33 days while the batch logged `skipped_stock_sufficient` every night. Keep queue.json's `reminders` (batch-owned operational state) separate from `settings` (user-edited).

## Remote Access Tunnel

- `scripts/tunnel_watch.sh` (launchd `com.dongpirang.tunnel`, hourly + at load): self-heals streamlit on :8501 (:8502 belongs to ai-trader), then ensures a **Tailscale Funnel** on `https :10000 → localhost:8501`, recording the URL in `logs/funnel.url` and notifying via `scripts/notify_admin.py`. Sleep window 00–07 KST skips checks.
- Funnel replaced the Cloudflare quick tunnel because quick-tunnel URLs changed on every restart. Funnel only allows ports 443/8443/10000; 443 is another service and 8443 is ai-trader, which is why this app uses 10000. Do not switch back to cloudflared.
- `scripts/notify_admin.py` sends Telegram messages to the single admin `TELEGRAM_CHAT_ID` in `.env` ONLY. Never add guest fan-out here (ai-trader's notify_telegram.py has guests — do not reuse it for tunnel URLs).
- `app.py` has an access-password gate (`APP_ACCESS_PASSWORD` in `.env`) because the tunnel exposes local CLI engines publicly. Keep the gate's text_input untracked by analytics.

## Git Hygiene

- The repo may contain untracked `.DS_Store` files. Do not remove or stage them unless the user asks.
- `docs/superpowers/` is gitignored; use `git add -f` only for approved spec/plan files that must be committed.
- Prefer small commits by task.
- Do not reset or revert user changes without explicit instruction.

