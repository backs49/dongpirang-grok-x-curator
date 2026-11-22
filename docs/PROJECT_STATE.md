# Project State (main)

기준 브랜치 main의 통합 상태. 상태 표기는 `진행 / 검증 / 승인`([프로토콜 4절](CONTINUITY_PROTOCOL.md)).
마지막 실측: 2026-11-22. 숫자는 그날 확인한 값이며, 재개할 때는 아래 "점검 방법"으로 다시 잰다.

## 목표와 현재 단계

- 목표: X 팔로워 성장 → 크리에이터 수익화(90일 유기 노출 500만, 팔로워 500, Premium). `CHAT`
- 단계: 인프라(로드맵 0~4c)는 완성돼 운영 중이다. 병목은 코드가 아니라 **초안 승인**이다. 상태를 물으면 launchd 가동 여부보다 발행 건수와 승인 대기 일수를 먼저 본다.

## 기능별 상태

| 기능 | 상태 | 근거 |
|---|---|---|
| NiceGUI 워크스페이스(:8081, Serve :10000) | RELEASED / PASS / NOT_REQUIRED | 2026-11-22 HTTP 200, `tailscale serve status` (`TEST`) |
| 레거시 Streamlit(:8501, Serve :10001) | RELEASED / PASS / NOT_REQUIRED | 2026-11-22 HTTP 200 (`TEST`) |
| 테스트 스위트 | — / PASS / — | `venv/bin/python -m pytest -q` → 704 passed, 2026-11-22 (`TEST`) |
| 야간 초안 배치(23:00) | RELEASED / PASS / NOT_REQUIRED | draft_log 11-20·11-21 tip 초안 각 1건 생성 (`TEST`) |
| 답글 씨앗(D-008, D-009) | RELEASED / INCONCLUSIVE / PENDING | 분리 후 11-20·11-21 `reply_seeds_added: 0`은 조건 맞는 답글이 없어서였다(결함 아님). 실제로 씨앗이 들어간 밤은 아직 없다 (`TEST`, [조사](tasks/archive/2026-11-22-reply-seeds-zero.md)) |
| 자동 발행 워커(live) | RELEASED / PASS / NOT_REQUIRED | publish_log 11-22 run_summary `live: true, posted: 0` (`TEST`) |
| 실제 발행 실적 | BLOCKED (승인 대기) | 워커 경유 마지막 발행 2026-07-08. queue.json: published 4, rejected 10, draft 0 — 11-22 대기 2건 반려 (`TEST`) |
| agy CLI 엔진(사이드바, Gemini 4 Neon, D-012) | RELEASED / PASS / APPROVED | 722 passed, 평가에서 Neon 채택·야간 배치 기준 미충족 ([task](tasks/archive/2026-11-22-agy-cli-provider.md)) (`TEST`) |
| 4d 주간 피드백 루프 | PLANNED (보류, D-004) | 발행 데이터 없음 |

## 알려진 결함과 위험

1. **야간 tip 초안이 입력에 없던 경험을 지어낸다.** 11-20·11-21 초안 2건은 11-22 반려했다. 요체는 결함이 아니다(보이스 카드대로, Owner 확인). 내 말투 블록 보강(11-22 채택)으로 측정상 날조가 약 86%→45%로 줄었다. 사람다움은 소폭 하락. 실제 야간 초안에서 남는지 지켜본다 ([task](tasks/archive/2026-11-22-tip-fabrication.md), `TEST`).
2. **답글 씨앗 0건은 소재 부족이다.** 11-14 이후 답글이 3건뿐이었다. 창은 3일로 늘렸지만(D-011) 답글 활동이 늘지 않으면 씨앗은 계속 0건이다. 11-18 답글은 워터마크가 이미 지나 소급되지 않는다 (`TEST`).
3. **Codex CLI 배치 타임아웃 원인 미확인**(D-007). 배치는 Claude CLI로 돌고 있어 당장 영향은 없다.
4. **draft_log.jsonl의 2026-11-20 이전 집계는 믿지 않는다.** 테스트가 운영 로그에 쓰던 흔적 2,312줄을 11-20에 제거했다(d189a9b에서 픽스처로 차단).
5. 이전 계획 문서(`docs/superpowers/plans/`, gitignored)의 후속 카드 중 미확인 항목: 편집·반려 레이스(아카이브 드리프트, 슬롯 좀비), 스테일 publishing 판정의 시간 게이트 없음. 모두 저확률로 분류됐었다(`DOC` 로컬 전용, `UNVERIFIED`).

## 현재 우선순위

1. 다음 야간 tip 초안에 지어낸 경험이 남는지 확인
2. 답글 활동 재개(Owner) 후 첫 씨앗이 초안까지 가는지 draft_log의 `reply_seed_added`로 확인
3. Owner 확인 대기: AGENTS.md에 "`docs/` 상태 문서 한정 커밋 사전 승인" 문구를 넣을지, DECISIONS의 `PENDING`(D-004, D-005, D-009). 연속성 프로토콜 설치는 끝났다([archive](tasks/archive/2026-11-22-continuity-protocol.md), DONE / PASS / PENDING)

## 진행 중인 task 파일

이 저장소는 main에 직접 커밋하므로 task 파일 이름은 브랜치가 아니라 작업 식별자(`YYYY-MM-DD-<주제>`)를 쓴다. `docs/tasks/`에서 `archive/`를 뺀 파일이 진행 중인 작업이다.

- 없음

## 점검 방법

- 발행 실적: `content_queue/publish_log.jsonl`(`event: published`)
- 생성·스킵·리마인드: `content_queue/draft_log.jsonl`
- 대기 초안·소재: `content_queue/queue.json`
- 앱·터널: `lsof -iTCP:8081 -iTCP:8501 -sTCP:LISTEN`, `tailscale serve status`(자기 자신에서 `*.ts.net` curl은 hairpin으로 실패한다)
- launchd 로그(`/tmp/dongpirang-*.log`)는 재부팅 때 지워지므로 저장소 안 jsonl이 정본이다.
