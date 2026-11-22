# Task: 연속성 프로토콜 설치 (claude-mem 대체)

상태: `IN_PROGRESS / NOT_RUN / PENDING` — 문서 작성 완료, 커밋·새 세션 재개 테스트 대기
근거 지시: [../decisions/2026-11-22-continuity-protocol.md](../decisions/2026-11-22-continuity-protocol.md) · 결정 D-010

## 다음 작업

1. (Owner) 미커밋 문서 커밋 승인 여부 결정 — 제안 메시지: `docs: 연속성 프로토콜 설치, AGENTS.md를 운영 규칙과 ARCHITECTURE로 분리`
2. (Owner) 커밋 후 새 Claude Code 세션에서 `/memory`로 CLAUDE.md → AGENTS.md 로드 확인, "이어서 진행해" 재개 테스트(F)
3. (Owner 승인 후) claude-mem 삭제: Claude Code 플러그인 → Codex config/캐시 → Grok 훅 → launchd `com.gongmox.claude-mem-hooks` → 워커 종료 → `~/.claude-mem`

## 범위

- 허용: 문서 수정·생성(AGENTS.md, CLAUDE.md, docs/*, .gitignore의 CLAUDE.local.md)
- 금지: 제품 코드, 테스트, 의존성, 스크립트, hooks, launchd 변경. 커밋·push는 별도 승인.
- 기준 커밋: d189a9b (main)

## 결과

- `AGENTS.md`: 146줄 → 운영 규칙만 남겨 80줄 이내로 재작성. 안전 규칙·venv·포트·테스트 명령은 인라인 유지.
- `docs/ARCHITECTURE.md`: AGENTS.md의 Important Files, Error Conventions, Provider Notes, Image Workflow, Publish Pipeline, Remote Access 절을 원문 그대로 이동.
- `docs/DECISIONS.md`: D-001~D-010. 2026-11-22 이전 결정은 승인 원문이 없어 `기존 규칙` 또는 `PENDING`.
- `docs/PROJECT_STATE.md`, `docs/CONTINUITY_PROTOCOL.md`(원문), `docs/decisions/2026-11-22-continuity-protocol.md`, `CLAUDE.md`(`@AGENTS.md`), `.gitignore`에 `CLAUDE.local.md`.
- 저장소 밖: claude-mem DB의 decision·bugfix 3,214건을 `~/claude-mem-archive/`에 추출(DB는 읽기 전용, 무변경).

## 검증

| 항목 | 결과 | 근거 |
|---|---|---|
| 테스트 스위트(문서만 바꿨지만 기준선) | PASS | `venv/bin/python -m pytest -q` 703 passed |
| AGENTS.md 원문 보존 | PASS(예외 명시) | 원본 비공백 줄을 새 AGENTS.md+ARCHITECTURE.md와 줄 단위 대조. 그대로 없는 줄: 첫 줄 "Codex should use this file…"(새 소개문으로 대체), 절 제목 `## Local Setup`·`## Test Commands`, 명령 3개와 설명 문구(Commands 절에 인라인으로 재작성), 포트 맵 줄(샌드박스 문장을 이어 붙여 변경). 나머지는 원문 그대로 |
| 금지 규칙 AGENTS.md 잔류(E) | PASS | 원본의 never/do not/must not/only 줄을 대조. 실시간 X 검색 주장 규칙 2줄, 발행 워커 live 조건, 키 비노출, tailscale reset 금지, 관리자 전용 알림, venv 위치는 AGENTS.md에 인라인. 나머지(Provider 호출 세부, 이미지 폴백 등)는 ARCHITECTURE.md로 이동하고 AGENTS.md에서 절 링크 |
| AGENTS.md 경로 고정 여부 | PASS | `*.py *.sh *.plist *.toml *.yml`와 README.md에서 AGENTS.md 참조 없음(grep) |
| 앱 글쓰기 호출(새 AGENTS.md·CLAUDE.md 적용 상태) | Claude CLI PASS / Grok CLI INCONCLUSIVE | 2026-11-22 `GrokClient.optimize_post` 직접 호출(큐·로그 미기록). Claude 1/1 정상 JSON, 운영 규칙 문구 유출 없음. Grok 4/5 정상, 1회 `JSON 파싱 실패`(재현 안 됨, 변경 전 실패율 기준선 없음). 야간 배치는 Claude CLI라 영향 없음 |
| CLAUDE.md import 실제 로드(A) | NOT_RUN | 현재 세션에서 확인 불가. 새 세션 `/memory`로 확인 필요 |
| 새 세션 재개(F) | NOT_RUN | 커밋 후 Owner 수행 |

## 승인 대기

- 문서 커밋(위 메시지)
- AGENTS.md에 "`docs/` 상태 문서 한정 커밋 사전 승인" 문구를 넣을지
- DECISIONS의 `PENDING` 항목(D-004, D-005, D-009) 확인
- claude-mem 삭제 진행
