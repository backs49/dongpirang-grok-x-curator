# NiceGUI Mobile Workspace Design

## Goal

Replace the primary Streamlit experience with a mobile-first NiceGUI workspace
that remains useful after a mobile browser is backgrounded. A brief connection
loss may reconnect live UI updates; a longer loss must restore all meaningful
work from durable server-side state. The first release covers idea creation,
post optimization, and publishing. Existing secondary tools remain available
in the Streamlit legacy app during the migration.

## Scope and non-goals

### First NiceGUI release

- Mobile-first navigation: **Create**, **Polish**, and **Publish**.
- Cost-controlled idea flow: three compact directions, one selected direction,
  then one completed post.
- Existing post optimization, adapted to a durable background job.
- In-app editing, auto-saved drafts, X composer handoff, publishing queue, and
  published-history reuse.
- Tailscale-only access and recovery after an interrupted browser connection.

### Deferred to the legacy Streamlit app

- Feed curator, thread optimizer, scheduler, A/B comparison, risk check,
  performance tracker, unfollow tracker, image/video generation, and voice
  cards.
- These are preserved without behavioral changes while the core workspace is
  stabilized.

## Network and application topology

```text
Tailscale mobile client
  |-- existing Tailnet URL on port 10000 -> NiceGUI workspace (localhost:8080)
  '-- same Tailnet host on port 10001    -> Streamlit legacy tools (localhost:8501)

NiceGUI workspace
  |-- provider facade and prompts (reused)
  |-- durable generation jobs (directions, completed post, optimization)
  '-- content queue and publishing history (reused and extended)
```

- Replace the public Funnel with Tailscale Serve. Only permitted Tailnet users
  can reach either endpoint.
- Keep the current primary port (`10000`) for the NiceGUI workspace. The legacy
  app moves to port `10001` so no capability disappears during the staged
  migration.
- Remove the application password gate and the extra Streamlit cookie component.
  Tailnet membership is the access boundary.
- The server binds only to localhost; Tailscale Serve supplies TLS and access
  control.

## UX and state flow

### Create

1. The user enters one topic line and selects **Regular idea**, **Daily tip**,
   or **IT builder**. This has no LLM cost.
2. Advanced options are collapsed by default: length, writing mode, and source
   references.
3. **View three directions** creates a durable, token-limited direction job.
   Each card contains only a title, hook, angle, and core message.
4. Choosing a card and pressing **Write this direction** creates one durable
   completion job. Fact-grounded research for health and finance tips runs only
   at this stage.
5. The resulting post opens in the editor. Inputs are auto-saved as a draft.

### Polish

- The user pastes an existing X post, submits an optimization job, and receives
  an editable result. The job lives independently of the browser connection.

### Editor and publishing

- The editor has two equal actions: **Open X composer** and **Save to publishing
  queue**.
- Opening the X composer uses the existing intent-link behavior. It never marks
  a post published automatically.
- On return, the user explicitly marks a post **Published**. This creates a
  manual-publish history item without claiming a verified X post ID.
- Queue workers retain their existing API-based publishing behavior. Successful
  scheduled posts preserve the verified tweet ID and timestamp.
- Publish has filters for Draft, Scheduled/Processing, Failed, and Published.
  Any historical post can be duplicated into a fresh editable draft.

## Durable data model

### Jobs

Extend the current JSON-backed job store with explicit job kinds:

- `directions`: compact three-card output;
- `post`: one completed post from a selected direction;
- `optimize`: one optimization result.

Every job has a stable ID, input snapshot, provider name, status, timestamps,
result or safe error summary, and an idempotency guard. Reopening a page reads
the saved job; reconnects never silently create another provider request.

### Drafts and history

Continue using `content_queue/queue.json`, adding backward-compatible optional
fields such as origin, updated timestamp, selected direction metadata, manual
publish marker, and manual publish timestamp. Existing draft, approved,
publishing, error, and published records remain readable.

### Browser-scoped convenience state

NiceGUI signed user storage retains non-critical convenience state such as the
last visited area and unfinished input text. It is never the source of truth for
jobs, drafts, queue state, or published history. API keys are not persisted in
browser cookies.

## Reconnection and error behavior

- Brief Socket.IO interruption: NiceGUI reconnects and resumes UI updates.
- Long background suspension, page reload, or process recreation: reconstruct
  the page from the durable job and queue stores, showing the current status
  and saved draft rather than an empty session.
- A failure remains visible with an explicit Retry action. Retry creates a new
  request only after user confirmation; there is no implicit retry or duplicate
  billing after reconnect.
- In-progress posts are saved before navigation and on relevant input changes.
- All provider, queue, and publisher errors are sanitized so secrets do not
  reach the UI or logs.

## Visual direction

- Preserve the pink paw and Dongpirang identity, but present it as a focused
  personal writing workspace rather than a dense dashboard.
- Make the topic input and the next clear action dominant on mobile.
- Put engine, language, theme, and advanced generation controls in a compact
  settings surface instead of the primary task flow.
- Use clear status chips and explicit actions; avoid hidden automatic actions.

## Verification

- Unit tests for new job schemas, input validation, idempotency, and
  backward-compatible queue loading.
- Provider-facade contract tests for compact directions, final posts, and
  optimization jobs.
- Integration tests for reconnect recovery, draft autosave, X-composer handoff,
  manual history recording, scheduled history recording, and retry behavior.
- NiceGUI UI tests for the mobile navigation and the direction-to-editor flow.
- Deployment smoke checks for both local services and Tailscale Serve mappings.
- Manual mobile acceptance test: start a job, background the browser, return
  after a short and a long interruption, and verify no password prompt, no lost
  result, and no duplicate job.

## Acceptance criteria

1. On a Tailnet-connected phone, the primary URL opens without an application
   password.
2. A user can enter a topic, inspect three inexpensive directions, complete one
   selected post, edit it, and choose X composer or publishing queue.
3. Backgrounding or reopening the browser restores all active jobs and drafts
   without a duplicate LLM request.
4. Publishing shows both pending work and reusable history.
5. All deferred functions remain reachable through the legacy Streamlit URL.
