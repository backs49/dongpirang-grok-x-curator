# AGENTS.md

Shared operating rules for every coding agent (Claude Code, Codex, Grok). Detail lives in `docs/`; read only the section your task touches.

## Project Overview

Korean-first X post optimization and curation app (en/ja via `i18n.py`). Two front ends: NiceGUI mobile workspace (`nicegui_app.py`, :8081, primary) and legacy Streamlit (`app.py`, :8501). Engine order is `ENGINE_OPTIONS` in `provider_selection.py`; the **first entry is the default**: Grok CLI (also default image/video backend), Claude CLI, Codex CLI, xAI API, demo mode.

## Where to Read

- Editing `providers/`, `grok_client.py`, `image_client.py`, `publisher.py`, tabs, or scripts → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (files, error conventions, provider pins, image/video, publish pipeline, remote access).
- Why something is the way it is → [docs/DECISIONS.md](docs/DECISIONS.md) index first, then only the relevant entry.
- Current state, risks, active tasks → [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md). Work handoff → `docs/tasks/<task-id>.md`.

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
- Text generation returns `{"error": ...}` dicts; media generation and publishing raise `ProviderError`. Match the layer you edit; do not convert one to the other as a drive-by change (ARCHITECTURE.md › Error Conventions).
- Curator real-time X search should only be claimed when using a Grok-capable provider.
- Claude-only curator fallback may generate search keywords and reply drafts, but must not claim live X search.
- Local CLI providers keep their invocation invariants (`claude -p` no tools/no session persistence, `codex exec --ephemeral` read-only, `grok -p` plain output) — ARCHITECTURE.md › Provider Notes.
- Model tiers are pinned deliberately (D-006). Do not raise them without a quality reason.

## Safety Boundaries

- All generated posts stay `draft`; publishing always needs the owner's approval in the queue (D-001). `scripts/publish_worker.py` is dry-run unless `--live` (or `X_PUBLISH_LIVE=1`); install its launchd plist only after a manual `--live` test succeeds.
- X API keys live in `.env` (gitignored). Never print or log key values. The xAI key input is session-only and untracked.
- **Never run `tailscale serve reset` or `tailscale funnel reset`** — other services use Funnel on :443 and :8443. Per-port commands only (D-003).
- `scripts/notify_admin.py` messages the single admin `TELEGRAM_CHAT_ID` only. Never add guest fan-out.
- Use `venv/` inside the repo. Do **not** relocate the venv to `/tmp` or `/private/tmp` — launchd jobs hard-code the repo-local interpreter.

## Commands

Run from the repository root.

- Tests: `venv/bin/python -m pytest -q`
- Compile smoke: `venv/bin/python -m py_compile app.py provider_selection.py grok_client.py image_client.py providers/*.py tabs/*.py i18n.py`
- Ad-hoc app: `venv/bin/python -m streamlit run app.py --server.headless true --server.port 8503`

Port map on this machine: **8501 is this app** (held by the launchd-managed instance that `scripts/tunnel_watch.sh` keeps alive), 8502 is the ai-trader dashboard. Use a free port such as 8503 for ad-hoc runs so you do not fight the managed instance. If the sandbox blocks local port binding, rerun with appropriate approval.

## Continuity (development sessions only)

These rules apply to agent development sessions. They do **not** apply when the app itself calls a CLI to generate copy (those calls also run with this repo as cwd) — for those, ignore this section and answer only in the requested format.

- **Start:** `git status`, `git log --oneline -10`. Open the active task file listed in PROJECT_STATE (this repo commits on main, so task files are named `YYYY-MM-DD-<topic>`, not by branch). If the request carries a new instruction or approval, save it verbatim to `docs/decisions/` before working.
- **Update on events, not every tool call:** work unit done or test/review result → task file; design decision → new `D-NNN` in DECISIONS (never rewrite old ones; use `Supersedes:`); risk that affects main or merge/deploy confirmed → PROJECT_STATE; pausing or `/clear` → task file first.
- **Status** is three independent axes `progress / verification / approval` (e.g. `DONE / PASS / PENDING`). No `PASS` without a command and evidence; no `APPROVED` without a human approval record.
- **Finish:** report work done, verification, open issues, docs touched, next step and approvals needed. List uncommitted docs with a proposed message.
- Full protocol: [docs/CONTINUITY_PROTOCOL.md](docs/CONTINUITY_PROTOCOL.md).

## Git Hygiene

- Git commit, push, merge require the owner's approval (added 2026-11-22 with the continuity protocol).
- The repo may contain untracked `.DS_Store` files. Do not remove or stage them unless the user asks.
- `docs/superpowers/` is gitignored; use `git add -f` only for approved spec/plan files that must be committed.
- Prefer small commits by task.
- Do not reset or revert user changes without explicit instruction.
