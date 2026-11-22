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
| 테스트 스위트 | — / PASS / — | `venv/bin/python -m pytest -q` → 703 passed, 2026-11-22 (`TEST`) |
| 야간 초안 배치(23:00) | RELEASED / PASS / NOT_REQUIRED | draft_log 11-20·11-21 tip 초안 각 1건 생성 (`TEST`) |
| 답글 씨앗(D-008, D-009) | RELEASED / INCONCLUSIVE / PENDING | 분리 후 11-20·11-21 `reply_seeds_added: 0`. 원인 미확인 (`UNVERIFIED`) |
| 자동 발행 워커(live) | RELEASED / PASS / NOT_REQUIRED | publish_log 11-22 run_summary `live: true, posted: 0` (`TEST`) |
| 실제 발행 실적 | BLOCKED (승인 대기) | 워커 경유 마지막 발행 2026-07-08. queue.json: published 4, rejected 8, draft 2 (`TEST`) |
| 4d 주간 피드백 루프 | PLANNED (보류, D-004) | 발행 데이터 없음 |

## 알려진 결함과 위험

1. **승인 대기 초안 2건(11-20, 11-21)은 둘 다 tip 초안이고 문체가 Owner 기본값(평어체, `CHAT`)과 다르다.** 11-20은 요체·합쇼체("어렵더라고요", "미루게 됩니다"), 11-21은 평어체 본문에 요체 질문("나만 그런가요?")이 섞였다. 둘 다 입력에 없던 1인칭 경험을 쓴다. 승인 전에 확인해야 한다.
2. **답글 씨앗이 분리 후에도 0건.** `my_posts.json`은 11-22 07:20에 갱신됐다. 조건에 맞는 답글이 없었는지, 로직 문제인지 확인하지 않았다(`UNVERIFIED`).
3. **Codex CLI 배치 타임아웃 원인 미확인**(D-007). 배치는 Claude CLI로 돌고 있어 당장 영향은 없다.
4. **draft_log.jsonl의 2026-11-20 이전 집계는 믿지 않는다.** 테스트가 운영 로그에 쓰던 흔적 2,312줄을 11-20에 제거했다(d189a9b에서 픽스처로 차단).
5. 이전 계획 문서(`docs/superpowers/plans/`, gitignored)의 후속 카드 중 미확인 항목: 편집·반려 레이스(아카이브 드리프트, 슬롯 좀비), 스테일 publishing 판정의 시간 게이트 없음. 모두 저확률로 분류됐었다(`DOC` 로컬 전용, `UNVERIFIED`).

## 현재 우선순위

1. 대기 초안 2건 처리(승인 또는 반려) — Owner 행동
2. 답글 씨앗 0건 원인 확인
3. 연속성 프로토콜 정착 — [tasks/2026-11-22-continuity-protocol.md](tasks/2026-11-22-continuity-protocol.md)

## 진행 중인 task 파일

이 저장소는 main에 직접 커밋하므로 task 파일 이름은 브랜치가 아니라 작업 식별자(`YYYY-MM-DD-<주제>`)를 쓴다. `docs/tasks/`에서 `archive/`를 뺀 파일이 진행 중인 작업이다.

- [2026-11-22-continuity-protocol.md](tasks/2026-11-22-continuity-protocol.md) — IN_PROGRESS

## 점검 방법

- 발행 실적: `content_queue/publish_log.jsonl`(`event: published`)
- 생성·스킵·리마인드: `content_queue/draft_log.jsonl`
- 대기 초안·소재: `content_queue/queue.json`
- 앱·터널: `lsof -iTCP:8081 -iTCP:8501 -sTCP:LISTEN`, `tailscale serve status`(자기 자신에서 `*.ts.net` curl은 hairpin으로 실패한다)
- launchd 로그(`/tmp/dongpirang-*.log`)는 재부팅 때 지워지므로 저장소 안 jsonl이 정본이다.
