# Decisions

설계·운영 결정의 인덱스와 본문. 평소에는 인덱스만 읽고, 관련 결정만 본문을 연다.
변경할 때는 기존 항목을 고치지 않고 새 항목에 `Supersedes: D-NNN`을 적는다. 30건 또는 500줄을 넘으면 `docs/decisions/D-NNN.md`로 분리한다.

출처 표기: `CODE`, `TEST`, `DOC`(커밋된 문서), `APPROVAL`(승인 원문), `CHAT`(대화·에이전트 메모리에만 있음), `UNVERIFIED`.
승인 표기: `APPROVED`는 원문 근거가 있을 때만 쓴다. 2026-11-22 이전 결정은 승인 원문이 보존돼 있지 않아 `기존 규칙`으로 적는다.

## 유효 결정 인덱스

| ID | 일자 | 요약 | 승인 |
|---|---|---|---|
| D-001 | 2026-07 | 반자동 발행: 모든 생성물은 draft, 발행은 사람 승인 필수 | 기존 규칙 |
| D-002 | 2026-08-10 | 승인 정체 시 텔레그램 리마인더(배치 재고 판단보다 먼저) | 기존 규칙 |
| D-003 | 2026-08-17 | Funnel 폐기, tailnet 전용 Serve, 앱 비밀번호 게이트 제거 | 기존 규칙 |
| D-004 | 2026-08-10 | 4d 주간 피드백 루프 보류(분석할 발행 데이터가 쌓인 뒤) | PENDING (CHAT) |
| D-005 | 2026-09-29 | AI 티 제거 규칙은 측정 후에만 추가 | PENDING (CHAT) |
| D-006 | 2026-09-30 | 모델 티어 고정, 글쓰기 호출은 low effort | 기존 규칙 |
| D-007 | 2026-10-30 | 야간 배치 엔진 Claude → Codex 순서 | 기존 규칙 |
| D-008 | 2026-10-30 | 답글 씨앗: 본인 최근 답글을 원글 초안 소재로 | 기존 규칙 |
| D-009 | 2026-11-20 | 답글 씨앗 재고를 팁 재고와 분리(상한 2) | PENDING (CHAT) |
| D-010 | 2026-11-22 | 연속성 프로토콜 도입(claude-mem 대체) | APPROVED |

운영 지식(결정은 아니지만 재발 시 먼저 볼 것): venv는 저장소 안 `venv/` 고정(AGENTS.md), grok CLI 영상 400은 계정 `/privacy` opt-out이 원인(2026-08-11 opt-in 복구, `CHAT`).

---

## D-001 반자동 발행 승인 큐
- 일자: 2026-07 (발행 파이프라인 4단계) · 출처: `DOC` ARCHITECTURE.md Publish Pipeline, `CHAT` 메모리 x-growth-pipeline-status
- 결정: 배치·UI가 만드는 모든 초안은 `draft` 상태로 남고, 발행은 발행 큐 탭에서 사용자가 승인해야 한다. 풀오토 금지, 경험담 날조 금지(진정성 원칙).
- 영향: 승인이 멈추면 파이프라인 전체가 조용히 멈춘다 → D-002.
- 관련: `content_queue.py`, `scripts/publish_worker.py`, `scripts/generate_drafts.py`

## D-002 승인 정체 리마인더
- 일자: 2026-08-10 · 출처: `DOC` ARCHITECTURE.md Publish Pipeline
- 배경: 2026-07-08 이후 발행이 멈췄는데 배치는 매일 `skipped_stock_sufficient`만 남겨 33일간 아무도 몰랐다.
- 결정: 가장 오래된 `draft`가 `STALE_DRAFT_DAYS`를 넘으면 `scripts/notify_admin.py`로 관리자에게 알린다. 재고 판단보다 먼저 실행한다. 재전송은 `REMINDER_INTERVAL_DAYS`로 제한하고, 전송 실패는 기록하지 않아 다음 밤에 재시도한다. `approved`는 대기로 치지 않는다.
- 상태 저장: queue.json `reminders`(배치 소유)는 `settings`(사용자 편집)와 분리한다.

## D-003 Funnel 폐기, tailnet 전용 접근
- 일자: 2026-08-17 · 출처: `DOC` ARCHITECTURE.md Remote Access
- 결정: `https :10000 → 8081`(워크스페이스), `:10001 → 8501`(레거시)을 tailnet 전용 Serve로 둔다. 접근 통제가 tailnet 멤버십이므로 앱 비밀번호 게이트를 제거했다.
- 제약: 이 노드는 :443(다른 서비스), :8443(ai-trader)에 Funnel이 살아 있다. `tailscale serve reset`·`funnel reset` 금지, 포트별 명령만 쓴다.

## D-004 4d 주간 피드백 루프 보류
- 일자: 2026-08-10 · 출처: `CHAT` 메모리 x-growth-pipeline-status
- 결정: 성과 분석 루프는 발행이 재개돼 2~3주 데이터가 쌓인 뒤 만든다. 로드맵에 있다고 먼저 만들지 않는다.
- 승인: 원문 미보존 → `PENDING`, Owner 확인 필요.

## D-005 AI 티 제거 규칙의 추가 기준
- 일자: 2026-09-29~30 · 출처: `CHAT` 메모리 humanize-prompts-eval
- 근거: 블라인드 쌍대 판정에서 ko만 유의미(12/15, p=0.018), en 9/15, ja 7/15(효과 없음). 린터는 grok 출력에서 0건이라 안전망일 뿐이다.
- 결정: 프롬프트 규칙은 측정으로 효과를 확인한 뒤에만 추가한다. 레버는 프롬프트 규칙이고 엔진 교체 효과는 작다.
- 승인: `PENDING`, Owner 확인 필요.

## D-006 모델 티어 고정
- 일자: 2026-09-30 · 출처: `DOC` ARCHITECTURE.md Provider Notes
- 결정: Claude CLI `--model sonnet`, Codex CLI `-m gpt-6-luna`(분석 medium, 글쓰기 low), Codex 이미지 medium·모델 미지정, Grok CLI 모델 플래그 없음. 글쓰기 호출은 `GrokClient._write_json`으로 low effort.
- 근거: 2026-09-30 메모 초안 블라인드 평가에서 Luna low가 다른 Codex effort와 모든 effort의 Sol보다 높았다. 카피라이팅이라 최상위 추론이 필요 없다.
- 규칙: 품질 근거 없이 올리지 않는다.

## D-007 야간 배치 엔진 순서
- 일자: 2026-10-30 · 출처: `DOC` ARCHITECTURE.md Publish Pipeline
- 결정: `generate_drafts.py`는 Claude CLI → Codex CLI 순으로 쓴다. 2026-10-30 시험에서 Codex가 모든 호출에서 타임아웃이었다.
- 미해결: Codex 타임아웃 원인 `UNVERIFIED`.

## D-008 답글 씨앗
- 일자: 2026-10-30 (5a46bb6) · 출처: `DOC` ARCHITECTURE.md, `CODE` reply_seeds.py(저장소 루트)
- 배경: 2026-10 실제 활동은 답글 135, 원글 1. 답글에는 프롬프트 규칙으로 만들 수 없던 실제 입장이 담겨 있다.
- 결정: 최근 2일 본인 답글(조건 필터 후 최대 2개)과 원글을 소재로 `draft_from_reply`(최소 보이스 카드 프롬프트)를 돌린다. 모델이 `skip`하면 소재만 사용 처리한다.

## D-009 답글 씨앗 재고 분리
- 일자: 2026-11-20 (d189a9b) · 출처: `DOC` ARCHITECTURE.md, `CHAT` 메모리
- 배경: 11-04~19 팁 초안 4건이 `STOCK_TARGET`을 채워 답글 씨앗이 16일간 못 돌았다.
- 결정: 답글 출신 초안 대기가 `REPLY_STOCK_TARGET` 미만이면 전체 재고와 무관하게 돈다.
- 승인: `PENDING (CHAT)`. 분리는 Owner 지시였다고 메모리에 남아 있으나 원문이 보존되지 않았다. 상한값 2는 에이전트가 정했다. Owner 확인이 승인 기록이 된다.

## D-010 연속성 프로토콜 도입
- 일자: 2026-11-22 · 출처: `APPROVAL` [decisions/2026-11-22-continuity-protocol.md](decisions/2026-11-22-continuity-protocol.md)
- 배경: claude-mem 플러그인이 3.4G 데이터·백그라운드 LLM 요약·광고를 동반했고, 실제 가치는 프로젝트 상태와 결정 기록에 몰려 있었다.
- 결정: 프로젝트 기억은 커밋된 문서(AGENTS.md, docs/)와 Git으로 관리한다. 프로토콜 전문은 [CONTINUITY_PROTOCOL.md](CONTINUITY_PROTOCOL.md).
- 선택지: claude-mem 유지 / 연동 축소 / 프로토콜로 대체 → 대체. claude-mem의 decision·bugfix 기록은 저장소 밖 `~/claude-mem-archive/`에 추출해 두었다.
- 범위: 문서만. 커밋과 claude-mem 삭제는 별도 승인.
