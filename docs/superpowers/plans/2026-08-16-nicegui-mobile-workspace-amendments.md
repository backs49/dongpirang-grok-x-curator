# NiceGUI Mobile Workspace Plan — Verification Amendments

Verified 2026-08-16 against the live codebase, tailscale 1.98.8, and an empirical
NiceGUI 3.15.0 install under CPython 3.14.5. No blockers. The base plan
(`2026-08-16-nicegui-mobile-workspace.md`) stands; the deltas below override the
corresponding plan text.

## Confirmed-good foundations (no change needed)

- `nicegui.testing.user_simulation` exists in 3.15.0 exactly as the plan uses it:
  `async with user_simulation(root) as user: await user.open("/")`. No conftest or
  plugin needed. `pytest.ini` with `asyncio_mode = auto` is REQUIRED.
- `ui.run(root=...)` is valid (first positional param, added in 3.0);
  `storage_secret`, `reconnect_timeout`, `message_history_length` all exist.
- `ui.footer/tabs/tab/tab_panels/timer` all exist; `ui.tabs(value="create")` with a
  plain string works at runtime (annotation says Tab, ignore the type checker).
- `app.storage.user` raises RuntimeError without `storage_secret`; inside
  `user_simulation` a secret is auto-injected.
- All i18n symbols, `GrokClient(provider=...)`, `optimize_post`,
  `validate_generated_ideas`, `GroundedTipRequest`, `queue_lock`, `save_queue`,
  `queue_transaction`, `empty_queue`, `approve_draft` match the plan.
- `workspace_jobs`/`runner`/`worker` design faithfully mirrors the existing
  `idea_jobs.py` / `idea_job_runner.py` / `scripts/idea_worker.py` pattern —
  follow those files as the reference implementation.
- Port 10001 is free in tailscale serve config. Per-port `funnel --https=10000 off`
  and `serve --bg --https=PORT target` syntax verified on 1.98.8.
- `extra_streamlit_components` is imported only by app.py; `access_auth` only by
  app.py and its test. Deletions are safe.
- app_title en/ja strings match the plan's test literals verbatim (final char is
  U+1D54F 𝕏).

## Task 1 amendments (i18n)

- `translate()` must keep current `t()` semantics: format **only when kwargs are
  non-empty** (many _T strings contain literal `{n}`/`{err}` placeholders that
  would KeyError under unconditional `.format()`), and keep the per-language
  fallback `values.get(lang, values.get("ko", key))`.
- Also give `optimize_post` an optional `language` kwarg (default preserves
  current behavior) so Task 3's worker can honor the stored job language —
  otherwise optimize jobs silently run in Korean (get_lang_instruction reads
  session state which is always "ko" in a detached worker).

## Task 3 amendments (jobs/worker)

- Worker dispatch: use `request.get("content_type")`, never
  `request["content_type"]` — normal post jobs don't carry the key and the
  KeyError would be swallowed into fail_job.
- **Demo engine**: `build_provider("Demo")` returns `(None, status)` so a Demo job
  can never run through a provider. The worker must special-case
  `engine == "Demo"` and produce deterministic canned results (derive from
  demo_data.py) for all three kinds, with tests. Do not invent a Demo provider.
- Pass `language=job["language"]` when the worker calls `optimize_post`.

## Task 4 amendments (queue)

- `load_queue` only setdefaults top-level `materials`/`drafts`; it does NOT
  normalize per-draft fields. New helpers must read optional fields with
  `.get()` (or extend load_queue to setdefault the new per-draft fields).
- While editing content_queue.py, update the module docstring to document all six
  statuses (draft/approved/publishing/error/published/rejected) and the new
  workspace fields (origin, source_job_id, source_kind, updated_at,
  manual_published, published_at).
- `tweet_id` is written by `scripts/publish_worker.py`, not publisher.py; it is
  the marker distinguishing API publishes from manual ones.

## Tasks 5–8 amendments (UI tests)

- Use Pattern A everywhere: `async with user_simulation(root)` with any extra
  `@ui.page` registrations INSIDE the context body (user_simulation wipes global
  page routes on entry). Reserve the `user` fixture (main_file-driven) for
  end-to-end tests of the real entry point, if any.
- Task 8 failed filter: only `status == "error"` cards get the retry/schedule
  affordance (mirroring `_can_approve` in tabs/tab_publish_queue.py); `rejected`
  cards are display-only and must not re-enter the slot queue.

## Task 9 amendments (Tailscale cutover) — CRITICAL SAFETY

- **Never run `tailscale serve reset` or `tailscale funnel reset` on this
  machine.** The node also serves :443 → 8790 and :8443 → ai-trader 8502; a reset
  wipes all three port configs. Only per-port commands are permitted.
- The plan's Step 1 test (`'"$TS_BIN" funnel ' not in script`) contradicts its
  Step 3 funnel-off line. Resolution: assert `'funnel --bg' not in script`
  (no funnel ENABLE remains) instead.
- The funnel-off must be guarded or it tears down the serve handler every hourly
  run (funnel off removes the whole web-serve handler once serve exists →
  hourly outage). Guard: consult `tailscale serve status --json` and run
  `funnel --https=10000 off` only when an AllowFunnel entry for `:10000` exists.
- Hostname discovery: `serve get-config` is for VIP services and won't yield the
  node hostname on 1.98.8. Use `tailscale serve status` (text or --json Web
  keys) or `tailscale status --json | jq -r .Self.DNSName`.
- `tests/test_tunnel_path.py` needs NO edits — it only checks the
  `export PATH="..."` line, which must be preserved verbatim in the refactored
  script. Keep it in the regression run.
- Current watchdog facts to preserve: launchd label `com.dongpirang.tunnel`
  (plist has no PATH key — the script's export line is the only PATH source),
  hourly StartInterval, sleep window skipping 00:00–06:59 KST, Telegram
  notification via `scripts/notify_admin.py` only on URL change. The old
  notification text mentions the app password — rewrite it at cutover.
- Task 10 Step 4 verification must also confirm `:443` and `:8443` remain
  unchanged with AllowFunnel true, and that no AllowFunnel entry exists
  for `:10000`.
