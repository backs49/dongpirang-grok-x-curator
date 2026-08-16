# NiceGUI Mobile Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Deliver a Tailnet-only NiceGUI mobile workspace for cost-controlled idea creation, post optimization, editing, and publishing while retaining every non-core Streamlit tool on a legacy URL.

**Architecture:** Add a separate NiceGUI application on localhost port 8080, backed by new durable workspace jobs and the existing JSON publishing queue. Reuse the provider facade and prompt layer, but create compact direction and single-post contracts instead of the current five-full-post request. The watchdog runs NiceGUI and Streamlit side-by-side and maps them through private Tailscale Serve endpoints on ports 10000 and 10001.

**Tech Stack:** Python 3.14.5, NiceGUI 3.15.0, pytest + pytest-asyncio, existing JSON stores with fcntl locking, local Claude/Codex/Grok CLIs, Streamlit 1.50.0 legacy app, Tailscale Serve.

---

## File map

| File | Responsibility |
|---|---|
| i18n.py | Explicit-language translation helpers usable outside Streamlit. |
| xalgo_prompts.py, grok_client.py, grounded_tips.py | Compact directions and one selected completed post. |
| workspace_jobs.py | JSON-backed durable job store for directions, completion, and optimization. |
| workspace_job_runner.py, scripts/workspace_worker.py | Spawn and execute one durable workspace job outside the browser. |
| content_queue.py | Draft metadata, manual publish recording, duplication, and status filtering. |
| workspace_settings.py | Server-only NiceGUI storage secret; never write credentials to browser storage. |
| nicegui_app.py | Production NiceGUI entry point bound to localhost only. |
| workspace_ui/ | Focused shell, Create, Editor, Polish, Publish, copy, and styling modules. |
| scripts/tunnel_watch.sh | Run both local apps and configure private Tailscale Serve endpoints. |
| app.py, access_auth.py | Remove password-gate and iframe-cookie dependency from legacy Streamlit. |

Tasks 1–4 are pure backend work. Tasks 5–8 add UI. Task 9 is the deployment cutover and remains last.

### Task 1: Add a NiceGUI-compatible runtime and explicit-language i18n

**Files:**

- Modify: requirements.txt
- Create: pytest.ini
- Modify: i18n.py
- Create: tests/test_workspace_i18n.py

- [ ] **Step 1: Write failing pure i18n tests**

~~~python
from i18n import get_lang_instruction, normalize_language, translate


def test_translate_accepts_an_explicit_language_without_streamlit_state():
    assert translate("app_title", "en") == "Dongpirang Cat Grok 𝕏"
    assert translate("app_title", "ja") == "東ピラン猫 Grok 𝕏"


def test_invalid_language_uses_korean_and_language_instruction_is_explicit():
    assert normalize_language("fr") == "ko"
    assert "ENGLISH" in get_lang_instruction("en")
    assert "日本語" in get_lang_instruction("ja")
    assert get_lang_instruction("ko") == ""
~~~

- [ ] **Step 2: Run the new tests and confirm they fail**

Run: venv/bin/python -m pytest -q tests/test_workspace_i18n.py

Expected: FAIL with an import error for normalize_language or translate.

- [ ] **Step 3: Add the dependency, test configuration, and pure helpers**

Append these lines without changing the Streamlit pin:

~~~text
nicegui==3.15.0
pytest-asyncio>=0.24,<1
~~~

Create pytest.ini:

~~~ini
[pytest]
asyncio_mode = auto
~~~

In i18n.py, keep t() and every existing caller compatible. Add an explicit-language path and make existing helpers delegate to it:

~~~python
def normalize_language(language: str | None) -> str:
    return language if language in LANGUAGES else "ko"


def translate(key: str, language: str | None = None, **kwargs) -> str:
    values = _T.get(key)
    if values is None:
        return key
    return values[normalize_language(language)].format(**kwargs)


def t(key: str, **kwargs) -> str:
    return translate(key, get_lang(), **kwargs)


def get_lang_instruction(language: str | None = None) -> str:
    return LANG_INSTRUCTION[normalize_language(language or get_lang())]
~~~

Apply the same optional-language argument pattern to get_content_language_pair and get_output_language_name, preserving their no-argument Streamlit behavior.

- [ ] **Step 4: Verify the i18n layer and existing copy tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_i18n.py tests/test_i18n_provider_copy.py

Expected: PASS.

- [ ] **Step 5: Commit the independent runtime/i18n change**

~~~bash
git add requirements.txt pytest.ini i18n.py tests/test_workspace_i18n.py
git commit -m "feat: prepare NiceGUI runtime and explicit i18n"
~~~

### Task 2: Define compact directions and one-post provider contracts

**Files:**

- Modify: xalgo_prompts.py
- Modify: grok_client.py
- Modify: grounded_tips.py
- Create: tests/test_workspace_generation.py

- [ ] **Step 1: Write failing provider-contract tests**

~~~python
from grok_client import GrokClient


class FakeProvider:
    name = "Fake CLI"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate_json(self, system_prompt, user_prompt, **kwargs):
        self.calls.append((system_prompt, user_prompt))
        return next(self.responses)


def test_generate_directions_returns_exactly_three_compact_cards():
    provider = FakeProvider([{"directions": [
        {"title": "A", "hook": "h1", "angle": "a1", "core_message": "m1"},
        {"title": "B", "hook": "h2", "angle": "a2", "core_message": "m2"},
        {"title": "C", "hook": "h3", "angle": "a3", "core_message": "m3"},
    ]}])
    result = GrokClient(provider=provider).generate_directions(
        "사이드 프로젝트 배포 실수", mode="builder_note", language="ko"
    )
    assert result["directions"][1]["title"] == "B"
    assert "완성된 포스트" not in provider.calls[0][0]


def test_write_post_uses_only_the_selected_direction():
    provider = FakeProvider([{"post": {"title": "A", "content": "완성 글"}}])
    result = GrokClient(provider=provider).write_post(
        keywords="배포 실수",
        direction={"title": "A", "hook": "h", "angle": "a", "core_message": "m"},
        length=280,
        mode="builder_note",
        language="ko",
    )
    assert result["post"]["content"] == "완성 글"
    assert "배포 실수" in provider.calls[0][1]
    assert "core_message" in provider.calls[0][1]
~~~

Add tests that reject two or four direction cards, missing direction fields, and a completed post with blank content. Add a grounded-post test proving that health/finance research is called only by write_grounded_post, verifies sources with validate_generated_post, and returns one post with source metadata.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_generation.py

Expected: FAIL because generate_directions, write_post, and validate_generated_post do not exist.

- [ ] **Step 3: Add prompt schemas and strict normalizers**

Add these contracts to xalgo_prompts.py; use Korean production wording matching existing prompts and require JSON only:

~~~python
DIRECTIONS_SYSTEM_PROMPT = """Return exactly three compact directions.
JSON only: {"directions":[{"title":"short title","hook":"opening line","angle":"content angle","core_message":"core message"}]}.
Do not write a complete X post, image prompt, source URL, or call to action."""

POST_FROM_DIRECTION_SYSTEM_PROMPT = """Write one X post from the selected direction.
JSON only: {"post":{"title":"short title","content":"post body","strategy":"why it works","engagement_level":"High","best_time":"time window","target_actions":["reply"]}}.
Do not generate alternatives or image/video instructions."""
~~~

Add GROUNDED_POST_SYSTEM_PROMPT with the existing health/finance safety rules and one required evidence_urls list. In grounded_tips.py, add:

~~~python
def validate_generated_post(post: object, verified_urls: set[str]) -> dict:
    result = validate_generated_ideas([post], verified_urls)
    if "error" in result:
        return result
    return {"post": result["ideas"][0]}
~~~

In GrokClient, add generate_directions(keywords, mode, language), write_post(keywords, direction, length, mode, language), and write_grounded_post(keywords, direction, category, references, length, mode, language). Keep all existing five-idea methods untouched.

generate_directions makes one provider call and accepts exactly three dictionaries with non-empty title, hook, angle, and core_message. write_post normalizes one non-empty post.content. write_grounded_post retains GroundedTipRequest validation and Grok research, passes only a validated fact sheet plus the selected direction to the writer, validates evidence URLs, and attaches sources plus verified_at to the returned post.

- [ ] **Step 4: Verify new and existing generation behavior**

Run: venv/bin/python -m pytest -q tests/test_workspace_generation.py tests/test_grok_client.py tests/test_grounded_tips.py

Expected: PASS.

- [ ] **Step 5: Commit the contract change**

~~~bash
git add xalgo_prompts.py grok_client.py grounded_tips.py tests/test_workspace_generation.py
git commit -m "feat: add direction-first post generation"
~~~

### Task 3: Persist workspace jobs and run them outside the browser

**Files:**

- Create: workspace_jobs.py
- Create: workspace_job_runner.py
- Create: scripts/workspace_worker.py
- Create: tests/test_workspace_jobs.py
- Create: tests/test_workspace_worker.py
- Create: tests/test_workspace_job_runner.py

- [ ] **Step 1: Write failing job-store and worker tests**

~~~python
import workspace_jobs


class Ready:
    message = "ready"


class FakeGrok:
    def __init__(self, result):
        self.result = result
        self.optimize_calls = []

    def optimize_post(self, text):
        self.optimize_calls.append(text)
        return self.result


def test_claim_allows_one_worker_and_restores_terminal_result(tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job(
        "directions", {"keywords": "배포 실수", "mode": "builder_note"},
        engine="Grok CLI", language="ko", path=path,
    )
    assert workspace_jobs.claim_job(job["id"], path=path)["status"] == "running"
    assert workspace_jobs.claim_job(job["id"], path=path) is None
    workspace_jobs.complete_job(job["id"], {"directions": []}, path=path)
    assert workspace_jobs.get_job(job["id"], path=path)["status"] == "completed"


def test_worker_dispatches_only_the_requested_kind(monkeypatch, tmp_path):
    path = tmp_path / "workspace_jobs.json"
    job = workspace_jobs.create_job("optimize", {"text": "원문"}, engine="Codex CLI", language="ko", path=path)
    fake = FakeGrok({"optimized_post": "고친 글"})
    monkeypatch.setattr(workspace_worker, "build_provider", lambda *_: (fake, Ready()))
    assert workspace_worker.run(job["id"], jobs_path=path) == "completed"
    assert fake.optimize_calls == ["원문"]
~~~

Add runner tests that inspect the detached command ending in --job-id [job-id], verify start_new_session=True, and record spawn errors in the stored job. Add worker tests for directions, normal selected-post, grounded selected-post, unavailable providers, provider error dicts, and duplicate claims.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_jobs.py tests/test_workspace_worker.py tests/test_workspace_job_runner.py

Expected: FAIL because the workspace modules do not exist.

- [ ] **Step 3: Implement a credentials-free generic job store**

Use content_queue.queue_lock and content_queue.save_queue; do not copy locking code. Store jobs at content_queue/workspace_jobs.json. Define JOB_KINDS as directions, post, and optimize. Implement create_job(kind, request, engine, language, path), claim_job(job_id, path), complete_job(job_id, result, path), fail_job(job_id, error, path), and get_job(job_id, path).

Reject unknown kinds and blank requests before writing. A job contains a UUID, queued/running/completed/failed status, timestamps, kind, sanitized request snapshot, engine, language, result or safe error. Never write API keys, cookies, or a provider object. claim_job is the idempotency gate: only queued becomes running.

workspace_job_runner.submit_job creates first, then starts scripts/workspace_worker.py --job-id [job-id] with cwd=REPO_ROOT, start_new_session=True, and both streams sent to DEVNULL. It accepts a popen parameter for tests.

scripts/workspace_worker.py claims before building a provider, then dispatches exactly once:

~~~python
request = job["request"]
if job["kind"] == "directions":
    result = grok.generate_directions(
        request["keywords"], mode=request["mode"], language=job["language"]
    )
elif job["kind"] == "post" and request["content_type"] == "grounded_tip":
    result = grok.write_grounded_post(
        keywords=request["keywords"], direction=request["direction"],
        category=request["category"], references=request["references"],
        length=request["length"], mode=request["mode"], language=job["language"],
    )
elif job["kind"] == "post":
    result = grok.write_post(
        keywords=request["keywords"], direction=request["direction"],
        length=request["length"], mode=request["mode"], language=job["language"],
    )
else:
    result = grok.optimize_post(job["request"]["text"])
~~~

Build only Grok CLI, Claude CLI, Codex CLI, or Demo from saved data. Do not add a persistent xAI API-key field; the legacy app retains xAI API mode. Convert returned error dictionaries and unexpected exceptions into fail_job; never retry automatically.

- [ ] **Step 4: Verify durable-job behavior**

Run: venv/bin/python -m pytest -q tests/test_workspace_jobs.py tests/test_workspace_worker.py tests/test_workspace_job_runner.py tests/test_providers.py

Expected: PASS.

- [ ] **Step 5: Commit durable job execution**

~~~bash
git add workspace_jobs.py workspace_job_runner.py scripts/workspace_worker.py tests/test_workspace_jobs.py tests/test_workspace_worker.py tests/test_workspace_job_runner.py
git commit -m "feat: persist NiceGUI workspace jobs"
~~~

### Task 4: Extend queue records for autosave and reusable history

**Files:**

- Modify: content_queue.py
- Modify: tests/test_content_queue.py

- [ ] **Step 1: Write failing queue-metadata tests**

~~~python
def test_workspace_draft_can_be_updated_and_manually_marked_published():
    data = empty_queue()
    draft = upsert_workspace_draft(
        data, draft_id=None, text="초안", pillar="build_in_public",
        source_job_id="job-1", source_kind="post",
    )
    updated = upsert_workspace_draft(
        data, draft_id=draft["id"], text="수정한 초안", pillar="build_in_public",
        source_job_id="job-1", source_kind="post",
    )
    mark_manual_published(data, updated["id"])
    assert data["drafts"][0]["text"] == "수정한 초안"
    assert data["drafts"][0]["status"] == "published"
    assert data["drafts"][0]["manual_published"] is True
    assert "tweet_id" not in data["drafts"][0]


def test_duplicate_history_creates_a_new_editable_draft():
    data = empty_queue()
    old = add_draft(data, text="지난 글", pillar="tip")
    mark_manual_published(data, old["id"])
    copied = duplicate_draft(data, old["id"])
    assert copied["id"] != old["id"]
    assert copied["status"] == "draft"
    assert copied["text"] == "지난 글"
~~~

Also test legacy JSON records with none of the new fields, missing/invalid draft IDs, and drafts_for_statuses(data, {"published"}) returning API and manual history together.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_content_queue.py

Expected: FAIL with missing workspace draft helpers.

- [ ] **Step 3: Add backward-compatible queue helpers**

Keep add_draft, approve_draft, and the batch worker contract untouched. Add get_draft(data, draft_id), upsert_workspace_draft(data, draft_id, text, pillar, source_job_id, source_kind), mark_manual_published(data, draft_id, now), duplicate_draft(data, draft_id), and drafts_for_statuses(data, statuses).

New workspace drafts include origin="workspace", source_job_id, source_kind, and updated_at. upsert_workspace_draft strips text, returns None for blank text, and only updates a still-editable draft. mark_manual_published sets status="published", manual_published=True, published_at, and slot=None; it must not invent tweet_id. duplicate_draft calls the same new-draft path, never mutates the source, and copies text/pillar only. Existing load_queue uses setdefault for all optional fields required by callers, so old records remain valid.

- [ ] **Step 4: Verify queue and publisher regressions**

Run: venv/bin/python -m pytest -q tests/test_content_queue.py tests/test_publisher.py

Expected: PASS.

- [ ] **Step 5: Commit queue persistence**

~~~bash
git add content_queue.py tests/test_content_queue.py
git commit -m "feat: persist workspace drafts and publish history"
~~~

### Task 5: Create the localhost-only NiceGUI shell and settings surface

**Files:**

- Create: workspace_settings.py
- Create: nicegui_app.py
- Create: workspace_ui/__init__.py
- Create: workspace_ui/app.py
- Create: workspace_ui/theme.py
- Create: workspace_ui/copy.py
- Create: tests/test_workspace_settings.py
- Create: tests/test_workspace_shell.py

- [ ] **Step 1: Install the newly pinned NiceGUI test runtime**

Run: `venv/bin/python -m pip install -r requirements.txt`

Expected: NiceGUI 3.15.0 and pytest-asyncio install into the repository venv without changing other pinned packages.

- [ ] **Step 2: Write failing storage-secret and shell tests**

~~~python
from workspace_settings import load_or_create_storage_secret


def test_storage_secret_is_stable_and_owner_only(tmp_path):
    path = tmp_path / "nicegui_storage_secret"
    assert load_or_create_storage_secret(path) == load_or_create_storage_secret(path)
    assert path.stat().st_mode & 0o077 == 0
~~~

~~~python
from nicegui.testing import user_simulation
from workspace_ui.app import build_workspace


async def test_shell_shows_three_mobile_areas():
    async with user_simulation(build_workspace) as user:
        await user.open("/")
        await user.should_see("만들기")
        await user.should_see("다듬기")
        await user.should_see("발행")
~~~

- [ ] **Step 3: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_settings.py tests/test_workspace_shell.py

Expected: FAIL because the NiceGUI entry point and workspace modules are absent.

- [ ] **Step 4: Implement the app boundary and mobile shell**

workspace_settings.py creates a 32-byte random secret at content_queue/nicegui_storage_secret, writes it atomically with mode 0o600, and returns a URL-safe string. It must not read or alter .env.

nicegui_app.py must be safe to import in tests and start only under __main__:

~~~python
def run(port: int = 8080) -> None:
    ui.run(
        root=build_workspace,
        host="127.0.0.1",
        port=port,
        reload=False,
        storage_secret=load_or_create_storage_secret(),
        reconnect_timeout=15.0,
        message_history_length=1000,
    )


if __name__ == "__main__":
    run(int(os.environ.get("NICEGUI_PORT", "8080")))
~~~

workspace_ui.copy wraps i18n.translate with the language in app.storage.user and adds every new Korean, English, and Japanese workspace label in one mapping. workspace_ui.theme installs pink-paw, focused-workspace CSS with readable light/dark token variables and bottom-navigation padding.

build_workspace initializes only non-sensitive user values: language, theme, engine, last_area, and unfinished input text. It renders a compact header containing the paw, a settings dialog (language/theme/local CLI engine), a responsive main container, and a fixed footer made from ui.tabs and ui.tab_panels:

~~~python
with ui.footer().classes("workspace-bottom-nav"):
    with ui.tabs(value="create").classes("w-full justify-around") as areas:
        ui.tab("create", icon="edit_note", label=copy("create"))
        ui.tab("polish", icon="auto_fix_high", label=copy("polish"))
        ui.tab("publish", icon="send", label=copy("publish"))
~~~

Use only local CLI engines plus Demo in this settings surface. Show an explicit legacy-link notice for xAI API rather than collecting or persisting an API key. Reserve each tab panel for a renderer imported from Tasks 6–8.

- [ ] **Step 5: Verify the shell with NiceGUI's browser-free test harness**

Run: venv/bin/python -m pytest -q tests/test_workspace_settings.py tests/test_workspace_shell.py

Expected: PASS without Selenium or a network listener.

- [ ] **Step 6: Commit the shell**

~~~bash
git add workspace_settings.py nicegui_app.py workspace_ui tests/test_workspace_settings.py tests/test_workspace_shell.py
git commit -m "feat: add NiceGUI mobile workspace shell"
~~~

### Task 6: Build Create, directions, and the autosaving editor

**Files:**

- Create: workspace_ui/create.py
- Create: workspace_ui/editor.py
- Create: workspace_ui/job_view.py
- Create: tests/test_workspace_create.py
- Create: tests/test_workspace_editor.py

- [ ] **Step 1: Write failing workflow tests with injected submitters**

~~~python
def test_create_request_contains_no_full_post_until_direction_is_selected():
    captured = []
    submit_directions(
        {"keywords": "배포 실수", "mode": "builder_note"},
        submitter=lambda kind, request, **kwargs: captured.append((kind, request)) or {"id": "d1"},
    )
    assert captured == [("directions", {"keywords": "배포 실수", "mode": "builder_note"})]


def test_selecting_a_direction_submits_one_post_job():
    captured = []
    submit_selected_direction(
        keywords="배포 실수", direction={"title": "A", "hook": "h", "angle": "a", "core_message": "m"},
        length=280, mode="builder_note", language="ko", content_type="ideas",
        submitter=lambda kind, request, **kwargs: captured.append((kind, request)) or {"id": "p1"},
    )
    assert captured[0][0] == "post"
    assert captured[0][1]["direction"]["title"] == "A"
~~~

~~~python
def test_editor_autosave_and_manual_publish_keep_history(tmp_path):
    draft = save_editor_draft(None, "첫 문장", "tip", "post-1", queue_path=tmp_path / "queue.json")
    save_editor_draft(draft["id"], "수정한 문장", "tip", "post-1", queue_path=tmp_path / "queue.json")
    mark_editor_published(draft["id"], queue_path=tmp_path / "queue.json")
    saved = load_queue(tmp_path / "queue.json")["drafts"][0]
    assert (saved["text"], saved["manual_published"]) == ("수정한 문장", True)
~~~

Add user_simulation tests that open Create, see the one-line prompt, cannot submit an empty topic, see exactly three completed direction cards, select one card, and see editor actions. Do not start a real CLI in UI tests; monkeypatch the submitter and job reader.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_create.py tests/test_workspace_editor.py

Expected: FAIL because Create/editor helpers and renderers are absent.

- [ ] **Step 3: Implement the cost-controlled Create flow**

workspace_ui.create keeps a small request dictionary in signed NiceGUI user storage, but never treats it as source of truth after submission. Render:

~~~text
topic text area
content type toggle: 일반 아이디어 / 사실 기반 팁
fact-tip category chips: daily / health / finance / it_builder (shown only for facts)
collapsed options: length, writing mode, references
primary button: 방향 3개 보기
~~~

submit_directions validates a non-empty topic, calls workspace_job_runner.submit_job("directions", request, engine=engine, language=language), saves only the returned job ID as active_direction_job_id, and disables the button while that job is queued/running. workspace_ui.job_view polls workspace_jobs.get_job with ui.timer; on reconnect or page rebuild it reads the same saved ID and renders the stored terminal result. It never calls a provider or resubmits a job.

Direction cards display title, hook, angle, and core message only. Their selection invokes submit_selected_direction, which copies exactly the selected card plus current options into a post job. For grounded_tip, include category and references so Task 3 dispatches write_grounded_post; do not call research before this selection.

workspace_ui.editor exposes these pure helpers: save_editor_draft(draft_id, text, pillar, source_job_id, queue_path), mark_editor_published(draft_id, queue_path), and x_compose_url(text).

Save initial completion output immediately with upsert_workspace_draft. Save later text changes with the same draft ID. Render a text area, character count, X 작성 화면 열기 link with target=_blank, 발행 큐에 저장, and a separate 게시했음 confirmation. The X link alone must not change status. 게시했음 calls mark_manual_published; queue saving leaves a draft ready for Task 8 approval/scheduling.

- [ ] **Step 4: Verify Create/editor behavior and no duplicate request path**

Run: venv/bin/python -m pytest -q tests/test_workspace_create.py tests/test_workspace_editor.py tests/test_workspace_jobs.py tests/test_content_queue.py

Expected: PASS.

- [ ] **Step 5: Commit Create and editor**

~~~bash
git add workspace_ui/create.py workspace_ui/editor.py workspace_ui/job_view.py tests/test_workspace_create.py tests/test_workspace_editor.py
git commit -m "feat: add direction-first creation and editor"
~~~

### Task 7: Move post optimization onto the durable workspace path

**Files:**

- Create: workspace_ui/polish.py
- Create: tests/test_workspace_polish.py
- Modify: workspace_ui/app.py
- Modify: tests/test_workspace_shell.py

- [ ] **Step 1: Write failing optimization tests**

~~~python
def test_polish_submits_one_durable_optimize_job():
    calls = []
    job = submit_optimization(
        "원문 포스트", language="ko", engine="Claude CLI",
        submitter=lambda kind, request, **kwargs: calls.append((kind, request)) or {"id": "o1"},
    )
    assert job["id"] == "o1"
    assert calls == [("optimize", {"text": "원문 포스트"})]


def test_blank_post_is_not_submitted():
    def must_not_submit(*args, **kwargs):
        raise AssertionError("blank input must not create a job")

    assert submit_optimization("   ", language="ko", engine="Grok CLI", submitter=must_not_submit) is None
~~~

Add a UI simulation that submits valid text, sees a queued/running status, renders a completed optimized post from a stored fake job, and opens the shared editor with its own draft ID.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_polish.py

Expected: FAIL because workspace_ui.polish is absent.

- [ ] **Step 3: Implement Polish using the shared job view and editor**

submit_optimization strips input and creates workspace_job_runner.submit_job("optimize", {"text": text}, engine=engine, language=language). Store active_optimize_job_id independently from Create so opening another bottom-navigation area cannot replace a running job. Render the stored optimized_post, or the equivalent normalized worker value, as a button to open workspace_ui.editor; use source_kind="optimize" and the optimization job ID when creating its draft. Add Polish to the bottom tab panel in workspace_ui.app without changing Create/Publish identifiers.

- [ ] **Step 4: Verify the shared editor regression set**

Run: venv/bin/python -m pytest -q tests/test_workspace_polish.py tests/test_workspace_editor.py tests/test_workspace_worker.py

Expected: PASS.

- [ ] **Step 5: Commit durable optimization**

~~~bash
git add workspace_ui/polish.py workspace_ui/app.py tests/test_workspace_polish.py tests/test_workspace_shell.py
git commit -m "feat: add durable post optimization workspace"
~~~

### Task 8: Add the Publish workspace with queue and reusable history

**Files:**

- Create: workspace_ui/publish.py
- Create: tests/test_workspace_publish.py
- Modify: workspace_ui/app.py

- [ ] **Step 1: Write failing Publish behavior tests**

~~~python
def test_publish_filters_show_pending_and_manual_history(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        draft = upsert_workspace_draft(data, draft_id=None, text="초안", pillar="tip", source_job_id="j1", source_kind="post")
        mark_manual_published(data, draft["id"])
    assert len(load_publish_items("draft", queue_path=path)) == 0
    assert len(load_publish_items("published", queue_path=path)) == 1


def test_history_reuse_opens_a_new_draft(tmp_path):
    path = tmp_path / "queue.json"
    with queue_transaction(path) as data:
        old = upsert_workspace_draft(data, draft_id=None, text="지난 글", pillar="tip", source_job_id="j1", source_kind="post")
        mark_manual_published(data, old["id"])
    copied = reuse_history_item(old["id"], queue_path=path)
    assert copied["id"] != old["id"]
    assert copied["status"] == "draft"
~~~

Add UI simulations for changing Draft, Scheduled, Failed, and Published filters; approving a draft into the next slot; opening a historical item; and duplicating a historical item without mutating its source.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_workspace_publish.py

Expected: FAIL because the Publish renderer is absent.

- [ ] **Step 3: Implement Publish as a view over the existing queue**

Create PUBLISH_FILTERS with this exact mapping:

~~~python
PUBLISH_FILTERS = {
    "draft": {"draft"},
    "scheduled": {"approved", "publishing"},
    "failed": {"error", "rejected"},
    "published": {"published"},
}
~~~

Implement load_publish_items(filter_name, queue_path), schedule_draft(draft_id, queue_path), and reuse_history_item(draft_id, queue_path).

Use queue_transaction for every mutation. schedule_draft invokes existing approve_draft; it does not call X. Cards show slot, manual/API published distinction, timestamp, and the verified X URL only when tweet_id exists. History reuse calls duplicate_draft, then invokes the shared editor callback with the new draft. Rejected/error cards retain their error/retry status and are never silently removed.

- [ ] **Step 4: Verify queue, history, and UI behavior**

Run: venv/bin/python -m pytest -q tests/test_workspace_publish.py tests/test_content_queue.py tests/test_publisher.py

Expected: PASS.

- [ ] **Step 5: Commit Publish**

~~~bash
git add workspace_ui/publish.py workspace_ui/app.py tests/test_workspace_publish.py
git commit -m "feat: add NiceGUI publishing workspace"
~~~

### Task 9: Cut over to private Tailscale Serve and preserve the Streamlit legacy app

**Files:**

- Modify: scripts/tunnel_watch.sh
- Modify: app.py
- Delete: access_auth.py
- Delete: tests/test_access_auth.py
- Modify: requirements.txt
- Create: tests/test_tailscale_serve_watch.py
- Modify: tests/test_tunnel_path.py

- [ ] **Step 1: Write failing private-routing and legacy-auth tests**

~~~python
def test_watchdog_runs_both_local_apps_and_private_serve_ports():
    script = WATCH_SCRIPT.read_text(encoding="utf-8")
    assert "NICEGUI_PORT=8080" in script
    assert "LEGACY_APP_PORT=8501" in script
    assert 'serve --bg --https="$WORKSPACE_PORT" "http://127.0.0.1:$NICEGUI_PORT"' in script
    assert 'serve --bg --https="$LEGACY_PORT" "http://127.0.0.1:$LEGACY_APP_PORT"' in script
    assert '"$TS_BIN" funnel ' not in script


def test_legacy_streamlit_entry_has_no_password_gate_or_cookie_component():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "APP_ACCESS_PASSWORD" not in source
    assert "CookieManager" not in source
    assert "extra_streamlit_components" not in source
~~~

Keep launchd PATH tests and update only renamed watchdog variables; they must still prove every installed CLI is reachable.

- [ ] **Step 2: Confirm red tests**

Run: venv/bin/python -m pytest -q tests/test_tailscale_serve_watch.py tests/test_tunnel_path.py tests/test_access_auth.py

Expected: FAIL because the old Funnel/password/cookie design remains.

- [ ] **Step 3: Replace Funnel with a dual-service private watchdog**

Refactor scripts/tunnel_watch.sh without changing its launchd label or sleep-window policy. Use these variables:

~~~bash
NICEGUI_PORT=8080
LEGACY_APP_PORT=8501
WORKSPACE_PORT=10000
LEGACY_PORT=10001
~~~

ensure_nicegui starts venv/bin/python nicegui_app.py with NICEGUI_PORT, logs to logs/nicegui.log, and waits for http://127.0.0.1:8080/. ensure_legacy_app retains the existing Streamlit start command on port 8501 and waits for its local health URL.

Before enabling Serve, disable the old public endpoint once with current CLI syntax:

~~~bash
"$TS_BIN" funnel --https="$WORKSPACE_PORT" off >> "$WATCH_LOG" 2>&1 || true
~~~

Configure each private endpoint idempotently, then obtain its hostname from tailscale serve status or tailscale serve get-config --all rather than hard-coding a domain:

~~~bash
"$TS_BIN" serve --bg --https="$WORKSPACE_PORT" "http://127.0.0.1:$NICEGUI_PORT"
"$TS_BIN" serve --bg --https="$LEGACY_PORT" "http://127.0.0.1:$LEGACY_APP_PORT"
~~~

Write resolved URLs to logs/workspace.url and logs/legacy.url. When either changes, send one Telegram notification naming the NiceGUI workspace and legacy tools. Do not print .env values.

Remove only the Streamlit password-gate and extra_streamlit_components API-key persistence code from app.py. Replace saved-key initialization with saved_key = ""; retain a session-only API key input and remove remember-key checkbox/cookie operations. Delete access_auth.py, its test, and extra-streamlit-components from requirements. The Streamlit app stays feature-complete but becomes private through Serve.

- [ ] **Step 4: Verify source-level routing and affected tests**

Run: venv/bin/python -m pytest -q tests/test_tailscale_serve_watch.py tests/test_tunnel_path.py tests/test_i18n_provider_copy.py tests/test_providers.py

Expected: PASS.

- [ ] **Step 5: Commit the cutover code before altering live services**

~~~bash
git add scripts/tunnel_watch.sh app.py requirements.txt tests/test_tailscale_serve_watch.py tests/test_tunnel_path.py
git rm access_auth.py tests/test_access_auth.py
git commit -m "feat: serve NiceGUI privately over Tailscale"
~~~

### Task 10: Install, validate, and activate the dual application deployment

**Files:**

- Verify: every file from Tasks 1–9
- Verify: scripts/com.dongpirang.tunnel.plist

- [ ] **Step 1: Install pinned dependencies into the repository virtual environment**

Run: venv/bin/python -m pip install -r requirements.txt

Expected: NiceGUI 3.15.0 and pytest-asyncio install successfully under Python 3.14.5.

- [ ] **Step 2: Run static and full automated verification**

Run:

~~~bash
venv/bin/python -m py_compile nicegui_app.py workspace_settings.py workspace_jobs.py workspace_job_runner.py scripts/workspace_worker.py workspace_ui/*.py content_queue.py grok_client.py i18n.py
venv/bin/python -m pytest -q
~~~

Expected: both commands exit 0 with all existing and new tests passing.

- [ ] **Step 3: Prove both applications respond locally before exposure**

Run the two processes separately:

~~~bash
NICEGUI_PORT=8083 venv/bin/python nicegui_app.py
venv/bin/python -m streamlit run app.py --server.headless true --server.port 8503
~~~

Request http://127.0.0.1:8083/ and http://127.0.0.1:8503/ from separate terminals. Stop the ad-hoc processes after both return HTTP 200; do not use managed ports 8080/8501 for this check.

- [ ] **Step 4: Inspect Tailscale Serve syntax and activate the launchd watcher**

Run:

~~~bash
/opt/homebrew/bin/tailscale version
/opt/homebrew/bin/tailscale serve --help
launchctl kickstart -k "gui/$(id -u)/com.dongpirang.tunnel"
/opt/homebrew/bin/tailscale serve status
~~~

Expected: Serve reports a private workspace endpoint on :10000 to localhost :8080 and a private legacy endpoint on :10001 to localhost :8501. No Funnel endpoint remains on port 10000.

- [ ] **Step 5: Perform mobile acceptance testing on a Tailnet-connected phone**

1. Open the existing host URL on port 10000 with Tailscale active; confirm no application password appears.
2. Enter a topic, submit directions, background the browser, then return before completion; confirm the same stored job resumes without a second provider invocation.
3. Select a direction, complete one post, edit it, open X composer, return, and explicitly mark it published. Confirm it appears in Publish history.
4. Save a second post to the queue, schedule it, and confirm it appears under Scheduled.
5. Open the same host at port 10001 and confirm a deferred Streamlit tool still works.

Expected: every first-release acceptance criterion in the design document holds.

- [ ] **Step 6: Confirm no local-state files are staged**

Run: git status --short

Expected: clean worktree. Do not commit logs, content_queue, NiceGUI storage, generated media, virtual-environment files, or secrets.
