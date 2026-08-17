# NiceGUI 워크스페이스 백로그 구현 계획 (2026-08-17)

컷오버 런북(2026-08-16-nicegui-cutover-runbook.md)의 백로그 8건을 가치 순으로 구현한다.
사전 조사로 확정한 사실만 담았다 — 각 태스크의 파일·행 번호는 main 85e97b5 기준.

## Global Constraints

- 새로 쓰는 한국어 UI 카피는 평어체(…다/…한다)로 쓴다. 요체(…요/…세요) 금지.
  기준 예시는 workspace_ui/copy.py의 기존 문구("주제 한 줄을 먼저 적는다.").
- `tailscale serve reset` / `funnel reset` 형태는 어떤 파일에도 절대 추가하지 않는다.
- 잡 스토어(workspace_jobs.json)에는 API 키·쿠키·프로바이더 객체를 절대 넣지 않는다.
- NiceGUI 이벤트 루프에서 블로킹 IO 금지 — 파일 잠금이 필요한 호출은 기존 패턴대로
  `run.io_bound` 뒤에서만 실행한다(제출 경로는 이미 그렇게 되어 있다).
- 테스트 실행: 워크트리 루트에서
  `/Users/manggo-chaltteog/antigravity-workspace/dongpirang-grok-x-curator/venv/bin/python -m pytest -q`
  (venv 심볼릭 링크가 워크트리에 걸려 있으므로 `venv/bin/python -m pytest -q`도 동일).
- 기존 구조 테스트를 깨지 않는다: tests/test_tailscale_serve_watch.py(워치독 구조),
  tests/test_tunnel_path.py(PATH 줄), tests/test_workspace_*.py(user_simulation 흐름).
  의도적으로 단언을 바꿔야 하면 그 이유를 커밋 메시지에 남긴다.
- 커밋은 태스크당 1개 이상, 메시지는 기존 컨벤션(feat:/fix:/test:/docs: + 한국어 요약).

## Task 1: 잡 스토어 프루닝 + 크로스 탭 중복 제출 가드

**파일:** workspace_jobs.py, tests/test_workspace_jobs.py

두 기능 모두 `_transaction()`(workspace_jobs.py:43-49) 안에서 동작하는 스토어 수준 변경이다.

**1a. 프루닝.** `create_job`(workspace_jobs.py:60-96)의 트랜잭션 안에서, 잡을 추가하기
전에 다음 규칙으로 오래된 잡을 정리하는 `_prune(jobs: list) -> list` 헬퍼를 추가한다:

- terminal 상태(`completed`/`failed`)이고 `updated_at`이 7일보다 오래된 잡을 제거한다.
- terminal 잡이 200개를 넘으면 `updated_at` 오래된 순으로 초과분을 제거한다.
- `queued`/`running` 잡은 나이와 무관하게 절대 제거하지 않는다.
- 상수로 `PRUNE_TTL_DAYS = 7`, `PRUNE_MAX_TERMINAL = 200`을 모듈 상단에 둔다.
- `updated_at` 파싱 실패(빈 값·형식 오류) 잡은 제거 대상으로 취급하지 않는다(보수적).

프루닝이 안전한 근거(조사 확정): UI는 사라진 잡 ID에 대해 `job_view.render_job`이
`job is None` → `job_missing` 라벨로 우아하게 처리한다(workspace_ui/job_view.py:79-81).

**1b. 크로스 탭 중복 제출 가드.** 현재 가드는 렌더 패스 지역 dict라 탭 하나 안의
더블클릭만 막는다(workspace_ui/create.py:173, polish.py:132 — 이 파일들은 수정하지
않는다). 스토어 수준에서 멱등 생성으로 보완한다:

- `create_job` 트랜잭션 안에서, 추가 전에 기존 잡 중 다음 조건을 모두 만족하는 잡이
  있으면 새 잡을 만들지 않고 **그 잡을 그대로 반환**한다:
  - 같은 `kind`, 같은 `engine`, 같은 `language`
  - `request`가 동일: `json.dumps(request, sort_keys=True, ensure_ascii=False)` 비교
  - 상태가 `queued`/`running`(= job_view.PENDING_STATUSES와 동일 집합)
  - `updated_at`이 최근 15분 이내(상수 `DEDUP_WINDOW_MINUTES = 15`) —
    워커가 죽어 영원히 queued로 남은 잡이 재제출을 영구히 막는 것을 방지
- UI는 반환된 job dict의 `id`를 저장할 뿐이므로 호출부 수정은 불필요하다.
  두 번째 탭이 같은 요청을 제출하면 같은 잡 ID를 받아 같은 잡을 지켜보게 된다.
- 실패(`failed`)·완료(`completed`) 잡은 대상이 아니므로 명시적 재시도(Retry)와
  동일 주제 재생성은 지금처럼 새 잡을 만든다.

**테스트(필수):** 프루닝 — TTL 초과 terminal 잡 제거, 200개 초과 시 오래된 것부터 제거,
pending 잡은 아무리 오래돼도 보존, updated_at 깨진 잡 보존. 중복 가드 — 동일 요청
pending 중 재호출 시 같은 id 반환·잡 개수 불변, request가 다르면 새 잡, 상태가
terminal이면 새 잡, 15분 지난 pending은 새 잡. 기존 create/claim/complete/fail
테스트가 모두 그대로 통과해야 한다.

## Task 2: i18n의 Streamlit 결합 제거 (지연 임포트)

**파일:** i18n.py, tests/test_runtime_smoke.py

조사 확정: i18n.py에서 streamlit을 만지는 곳은 단 하나, `get_lang()`(i18n.py:1765-1767)
이고, 최상단 `import streamlit as st`(i18n.py:3) 때문에 워커 스폰마다 스트림릿 임포트
비용(~130-170ms, 콜드 스타트에서는 그 이상)을 낸다. 워커 경로는 런타임에 `get_lang()`을
절대 호출하지 않는다(grok_client의 워커 호출부는 전부 명시적 language 전달).

**변경:** i18n.py:3의 `import streamlit as st`를 삭제하고 `get_lang()` 본문 안으로
옮긴다. 다른 파일·호출부 수정 없음.

```python
def get_lang() -> str:
    import streamlit as st  # 지연 임포트: 워커가 i18n을 임포트할 때 streamlit 비용을 내지 않게

    return st.session_state.get("lang", "ko")
```

**테스트(필수):** tests/test_runtime_smoke.py에 서브프로세스 기반 회귀 테스트를 추가한다 —
`venv/bin/python -c "import i18n, sys; raise SystemExit(1 if 'streamlit' in sys.modules else 0)"`
꼴로 (a) `import i18n` 후 sys.modules에 streamlit이 없다, (b) 워커 임포트 체인
(`import provider_selection`) 후에도 streamlit이 없다를 각각 검증한다. 서브프로세스는
`sys.executable`을 쓰고 cwd를 리포 루트로 고정한다.

## Task 3: 근거 URL·Polish 점수를 UI에 표출

**파일:** workspace_ui/polish.py, workspace_ui/editor.py, tests/test_workspace_polish.py,
tests/test_workspace_editor.py (필요시 workspace_ui/copy.py)

조사 확정: 데이터는 이미 잡 결과에 전부 저장돼 있고 UI가 안 읽을 뿐이다.

**3a. Polish 점수·이유.** optimize 잡 결과는 `score`(int), `engagement_level`,
`reasons`(list[str]), `suggestions`(list[str]), `optimized_post`를 담는다
(xalgo_prompts.py:91-119의 스키마, demo_data.py:12-37의 OPTIMIZER_DEMO로 확인).
현재 `polish.py:99-102`는 `optimized_post`만 읽는다. `_render_result`
(polish.py:185-205)에 다음을 추가한다:

- 점수 배지: `score`가 int로 존재할 때만 표시. 라벨은 `copy("opt_score")` —
  copy()는 미보유 키를 i18n.translate로 위임하므로(workspace_ui/copy.py:497-499)
  기존 i18n 키 `opt_score`(i18n.py:579)가 그대로 쓰인다. `opt_reasons`(i18n.py:589)도 동일.
- 이유 목록: `reasons`가 비어 있지 않을 때만, 항목별 한 줄 라벨로 렌더.
- `suggestions`는 이번 범위에서 제외(모바일 화면 절약). 키가 없거나 형이 어긋나는
  결과(과거 잡·실험 모드)는 조용히 생략 — 예외를 내면 안 된다.

**3b. 근거(출처) URL.** grounded 잡 결과의 `post`에는 `sources`
(각 항목: title/url/publisher/published_at/excerpt — grounded_tips.py:91-108)와
`evidence_urls`가 이미 붙어 있다(grok_client.py:479-482). 현재 editor.py:324-325는
`post["content"]`만 읽는다. 편집기에서 잡 결과를 불러올 때 `post.get("sources")`가
있으면 편집 텍스트 영역 아래에 컴팩트한 출처 목록을 렌더한다:

- 제목 라벨은 `copy("ideas_sources")`(i18n.py:824, 레거시와 같은 문구).
- 각 출처는 `ui.link(title 또는 url, url)`로, `new_tab=True`.
- url 없는 항목은 건너뛴다. sources가 없으면(일반 포스트) 아무것도 렌더하지 않는다.
- 편집기는 Create/Polish/Publish 세 곳에서 key_prefix로 재사용되므로
  (editor.editor_storage_keys), 출처 렌더는 저장 키가 아니라 **넘겨받은 잡 결과**에서만
  읽는다. 저장 상태에 새 키를 추가하지 않는다.

**테스트(필수):** user_simulation으로 — optimize 완료 잡에서 점수·이유가 보인다,
score 없는 결과에서 배지가 없다(예외도 없다), grounded 완료 잡을 편집기로 열면 출처
링크가 보인다, 일반 포스트에서는 출처 섹션이 없다.

## Task 4: 팔레트 드리프트 테스트

**파일:** tests/test_theme_token_sync.py (신규)

조사 확정: design.py의 LIGHT_TOKENS/DARK_TOKENS(design.py:14-60)와
workspace_ui/theme.py 사이에 현재 18쌍이 verbatim 일치한다. 이를 고정하는 테스트만
추가한다(프로덕션 코드 수정 없음):

- 모듈 상수 비교: `theme.ACCENT["light"] == design.LIGHT_TOKENS["--accent"]`,
  `theme.ACCENT["dark"] == design.DARK_TOKENS["--accent"]`,
  `theme.SURFACE_DARK == design.DARK_TOKENS["--bg-elevated"]`,
  `theme.PAGE_DARK == design.DARK_TOKENS["--bg"]`.
- CSS 리터럴 비교: `theme.WORKSPACE_CSS`의 `:root{...}` 블록과
  `body.workspace-dark{...}` 블록에서 정규식 `--ws-<name>:\s*([^;]+);`으로 값을 뽑아
  명시적 매핑 dict(라이트: bg↔--ws-bg, bg-elevated↔--ws-surface,
  bg-sidebar↔--ws-sunken, text↔--ws-text, text-strong↔--ws-text-strong,
  text-muted↔--ws-text-muted, border↔--ws-border, accent↔--ws-accent,
  accent-soft↔--ws-accent-soft; 다크: 동일 매핑에서 --ws-nav-height 제외)과
  대조한다. 값 비교 전 공백을 정규화한다.
- `--ws-paw`(브랜드 전용)와 `--ws-nav-height`(레이아웃 전용), design.py의
  hover/alert/scrollbar/SHARED_TOKENS는 의도된 비대상임을 테스트 주석으로 남긴다.
- design.py 임포트는 streamlit 임포트를 유발하지만 임포트 시점에 st 호출은 없어
  안전하다(조사 확정).

## Task 5: 워치독 실패 시 Telegram 경보

**파일:** scripts/tunnel_watch.sh, tests/test_tailscale_serve_watch.py

조사 확정: 현재 로그만 남기는 실패 경로는 8곳이고, 유일한 알림 경로는 URL 변경 블록
(tunnel_watch.sh:189-198)이다. 제약: tests/test_tailscale_serve_watch.py가
`script.count("notify_admin.py") == 1`을 단언하므로, **알림을 셸 함수 하나로 감싸
리터럴 1회를 유지**한다.

**변경:**

1. `notify_admin()` 셸 함수를 추가한다 — 인자로 받은 메시지를
   `"$PYTHON" "$REPO/scripts/notify_admin.py" "$msg"`로 보내는 유일한 호출 지점.
   기존 URL 변경 블록의 직접 호출을 이 함수 호출로 교체한다(리터럴 총 1회 유지).
2. 실패 수집: 다음 경로에서 `FAILURES` 배열(또는 개행 문자열)에 실패 태그를 쌓는다 —
   `nicegui_start_failed`(:78), `streamlit_start_failed`(:95),
   `serve_config_failed_workspace`(:151), `serve_config_failed_legacy`(:157),
   `serve_endpoints_unresolved`(:173, exit 1 직전에 경보를 보낸 뒤 종료).
   AllowFunnel 블라인드 WARN(:111)과 일시적 URL 도달 실패 WARN(:180)은 경보 대상에서
   제외한다(오탐·플랩 소지).
3. 중복 억제: `logs/tunnel-alert.state`에 마지막으로 보낸 실패 태그 집합(정렬·개행 구분)
   을 기록한다. 이번 실행의 실패 집합이 파일 내용과 다를 때만 경보를 보내고 파일을
   갱신한다. 실패가 모두 사라진 전환(파일이 비어있지 않은데 이번 집합이 빈 경우)에는
   복구 알림 한 번을 보내고 파일을 비운다. 실패가 지속되면(집합 동일) 재경보하지 않는다.
4. 경보 메시지는 한국어 평어체로, 실패 태그 목록과 "자세한 로그는 logs/tunnel-watch.log"
   한 줄을 담는다. 알림 전송 실패는 기존 URL 알림과 동일하게 log만 남기고 진행한다.
5. 건드리면 안 되는 것: `export PATH=` 줄(tests/test_tunnel_path.py),
   funnel-off 가드 구조와 `disable_workspace_funnel` 호출 위치·횟수
   (test_funnel_off_sits_inside_the_public_port_guard,
   test_guarded_teardown_is_actually_invoked), reset 금지.

**테스트(필수):** test_tailscale_serve_watch.py에 추가 — notify_admin.py 리터럴이
여전히 정확히 1회다, `notify_admin()` 함수가 정의돼 있고 URL 블록과 실패 경로가 그
함수를 부른다(함수명 호출 2회 이상), `tunnel-alert.state` 라는 상태 파일명이 존재한다,
실패 태그 5종이 스크립트에 존재한다. 기존 단언 전부 통과.

## Task 6: 문구 통일 — "근거 기반 팁" 정본화 + ideas_error_* 평어체화

**파일:** workspace_ui/copy.py, i18n.py, 그리고 "사실 기반" 표기를 쓰는 주석·독스트링
(workspace_ui/create.py:5,117,245, workspace_ui/editor.py:142,
tests/test_workspace_create.py:314, tests/test_workspace_editor.py:151)

**6a. 정본 표기: "근거 기반 팁".** 근거 — 레거시 UI 라벨(i18n.py:770), 코드·테스트
다수(7곳), 그리고 "근거 URL"·"출처" 용어 계열과 일관된다. 변경:

- workspace_ui/copy.py:79 `create_type_grounded`의 ko를 "사실 기반 팁" → "근거 기반 팁".
  en/ja 값은 유지.
- copy.py 안에 "사실 기반" ko 문구가 더 있으면 함께 "근거 기반"으로 통일한다.
- 위에 나열한 주석·독스트링의 "사실 기반"을 "근거 기반"으로 바꾼다(코드 동작 무관).
- 라벨 문자열을 단언하는 테스트가 있으면 함께 갱신한다.

**6b. ideas_error_* 평어체화.** i18n.py:834-853의 4개 키 ko 문구를 평어체로 다시 쓴다.
이 문구들은 새 워크스페이스에서도 그대로 노출된다(job_view.py가 ideas_error_* 키로
폴백). 의미는 유지하고 어미만 바꾼다. 정확히 이 문구로 교체한다:

- `ideas_error_insufficient_sources`: "서로 다른 신뢰할 수 있는 출처를 두 곳 이상 확인하지 못했다. 주제를 조금 더 구체적으로 바꿔 다시 시도한다."
- `ideas_error_unsafe_personalized_request`: "건강·금융 팁은 일반 정보만 다룬다. 개인 증상·처방·복용량이나 보유 종목·매수·매도 판단은 요청할 수 없다."
- `ideas_error_unverified_evidence`: "생성 결과의 근거 URL을 확인할 수 없어 표시하지 않았다. 다시 생성하면 된다."
- `ideas_error_grounded_tips_require_grok_cli`: "근거 기반 팁에는 웹 조사가 가능한 Grok CLI가 필요하다. Grok CLI 로그인을 확인한다."

en/ja 값은 유지. 다른 요체 문구(~35곳, 레거시 탭 전용)는 이번 범위에서 건드리지
않는다 — 레거시 앱의 지배적 문체라 일괄 개편은 별도 작업.

**테스트:** 기존 테스트가 i18n 문자열을 원본과 비교하는 방식이면 자동으로 통과한다.
리터럴로 옛 문구를 박아둔 테스트가 있으면 새 문구로 갱신한다. 추가로
tests/test_i18n_provider_copy.py 계열에 ideas_error_* 4개 키의 ko가 요체 어미
("요.", "세요.")로 끝나지 않는다는 단언을 하나 추가한다.

## Task 7: pytest 9 + pytest-asyncio 1.x 업그레이드

**파일:** requirements.txt, pytest.ini

조사 확정: 현재 pytest 8.4.2 + pytest-asyncio 0.26.0, 경고 415건 전부가
pytest-asyncio 0.26 내부의 이벤트루프 정책 API 사용(Python 3.16에서 제거 예정) 탓이다.
`<1` 상한은 이 저장소가 스스로 건 핀이고(nicegui는 pytest 계열에 제약 없음), 리졸버
드라이런은 pytest 9.1.1 + pytest-asyncio 1.4.0으로 무충돌이다. 테스트 코드는
`asyncio_mode = auto`만 쓰므로(마커·event_loop 픽스처·loop_scope 사용 0건) 수정 불요.

**변경 순서:**

1. requirements.txt: `pytest-asyncio>=0.24,<1` → `pytest-asyncio>=1,<2`,
   새 줄로 `pytest>=9,<10` 추가(현재 미고정).
2. 워크트리가 공유하는 venv에 설치:
   `venv/bin/python -m pip install 'pytest>=9,<10' 'pytest-asyncio>=1,<2'`
   (라이브 앱은 pytest를 임포트하지 않으므로 가동 중 설치 안전).
3. 전체 스위트 실행. pytest-asyncio 경고 415건이 사라졌는지 확인.
4. pytest.ini에 `filterwarnings`를 추가하되 **표적만**: 먼저 `error` 한 줄만 넣고
   스위트를 돌려본다. 통과하면 그대로 두고, 특정 서드파티 경고가 남아 실패하면 그
   경고만 `ignore:<메시지 프리픽스>:<카테고리>:<모듈>` 형식으로 좁게 ignore를 추가하고
   각 줄에 이유 주석을 단다. 광역 `ignore::DeprecationWarning` 금지.
5. 전체 스위트 재실행으로 마무리(568개 전부 통과 + 경고 0 또는 표적 ignore만).

**주의:** 이 태스크는 공유 venv를 바꾸므로 **맨 마지막에** 실행한다. 이후 다른
태스크의 재검증도 새 pytest 위에서 돌아간다(전체 스위트 최종 실행이 그 역할).
