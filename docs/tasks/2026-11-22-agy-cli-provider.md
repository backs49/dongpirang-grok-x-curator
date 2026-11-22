# Task: agy CLI(Gemini 4 Neon·Hydrogen) 글쓰기 엔진 추가

상태: `DONE / PASS / PENDING` — 구현·평가·최종 리뷰 수정 완료, 커밋 승인 대기
근거 지시: [../decisions/2026-11-22-commit-and-reply-seeds.md](../decisions/2026-11-22-commit-and-reply-seeds.md) (후속 원문 4)

## 왜

Owner: "agy neon이 글을 잘 쓴다고하더라. 그래서 agy CLI도 추가 해보려해." 평가에 Gemini 4 Hydrogen 포함.

## 사전 조사 (2026-11-22)

- `~/.local/bin/agy` 1.5.14. `agy models`에 gemini-4-neon-{low,medium,high,xhigh}, gemini-4-hydrogen-{low,medium,high,xhigh}.
- `agy -p … --model gemini-4-neon-low --output-format json` 정상: `{"status":"SUCCESS","response":…}`, 약 12초. Hydrogen low도 약 11초.
- 호출마다 입력 약 2만 토큰(에이전트 기본 프롬프트). 대화가 agy 쪽에 저장된다(`conversation_id`, 무저장 플래그 없음).
- Owner 선택: 접근 1(기존 CliProvider 방식). 쓰임새 A(사이드바 선택지), B(야간 배치)는 점수가 확실히 높을 때만.

## 도구 차단 실측 (2026-11-22, gemini-4-neon-low, 빈 폴더에서 실행)

| 설정 | 명령 실행 | 폴더 안 파일 읽기 | 폴더 밖 파일 읽기 | 웹 읽기 |
|---|---|---|---|---|
| 기본(`permission_mode: request-review`) | 실행됨 | 읽음 | 미시험 | 미시험 |
| `--settings` deny(이름, `*`, `도구(*)`) | 실행됨 | 읽음 | — | 막지 못함 |
| `--mode plan` | 거부 | 읽음 | — | — |
| `--mode plan --sandbox` | 거부(`denied_actions`) | 읽음(빈 폴더라 읽을 게 없음) | 거부 | 2회 모두 못 함(`NO_WEB`, 도구 호출 없음) |

- 기본 노출 도구 약 60개(브라우저, search_web, read_url_content, send_message, schedule, run_workflow, generate_image 등). `--settings`에 `disabledTools` 키는 없다(unknown setting).
- 앞서 example.com 제목을 맞힌 건 모델이 외운 값일 수 있어 근거에서 뺐다.
- plan 모드는 agy 자기 폴더(`~/.gemini/antigravity-cli/brain/<id>/`)에 계획 파일을 쓰는 일이 있다. 과제 대신 계획을 써 버린 응답도 1회 관찰됐다.
- 거부되면 `status: SUCCESS`에 빈 `response`가 온다 → 오류로 바꿔야 한다.
- 대화 간 기억 누수: 코드워드를 심고 다른 빈 폴더에서 물으니 `UNKNOWN`. 누수 없음(1회).
- 남는 차이(Owner 수용 여부 결정 필요): 도구 목록 자체는 노출됨, 대화 저장, 2만 토큰, brain 폴더 부수 파일.

## 다음 작업

- Owner: 위 남는 차이를 수용할지(→ 새 D 항목·ARCHITECTURE 메모) 또는 `agy acp`로 바꿀지 결정 → 설계 문서

## 평가 기준 (측정 전 고정, 2026-11-22)

- 대상: agy Neon low, agy Hydrogen low, Claude CLI(Sonnet, 현행). 모두 출시 호출 설정 그대로(`GrokClient` 경유, 글쓰기 low).
- 과제: 기본 팁 키워드 `generate_ideas`(내 말투) 5회, 실제 메모 3개로 메모 쓰기.
- 판정: Claude Sonnet, Gemini 4 Argon 두 판정자. 블라인드 쌍대, 같은 회차에 실제 원글 섞음. 지어낸 경험 비율, 실패율, 소요 시간 기록.
- 사이드바 모델: Neon·Hydrogen 중 두 판정자 합산 승률이 높은 쪽.
- B(야간 배치) 후보: 승자가 두 판정자 모두에서 Claude 상대 60% 이상 + 실패율 5% 이하 + 지어낸 경험이 Claude 이하. 충족해도 보고만.

## 진행 기록

- Task 1(AgyCliProvider, 테스트 11개)·Task 2(엔진 목록 양쪽, 안내 문구 ko/en/ja, AGENTS·ARCHITECTURE) 완료. 전체 `pytest -q` 719 passed. 미커밋.
- Task 3 생성 1차(2026-11-22 21:50, 8개 병렬): Neon 팁 5/5(약 47초), Hydrogen 팁 3/5(약 25초), Claude 팁 5/5·메모 3/3(약 80~110초). 도중부터 agy 호출 전부 `authentication required` → **agy 로그인이 풀렸다.** 그 전까지 직렬 호출은 저녁 내내 정상이었다. 병렬 호출이 토큰 갱신을 꼬이게 했을 가능성(`UNVERIFIED`). Owner 재로그인 필요(`! agy`). 재개 시 agy 호출은 직렬로 돌리고, 앱에서 agy 호출이 겹치는 경로(아이디어·워크스페이스 워커 동시 실행)가 있는지 확인할 것.

## 평가 결과 (2026-11-22, 팁 25편 + 메모 15편씩)

쌍대 비교 승률(대상 엔진 기준, 40쌍씩):

| 비교 | Claude 판정 | Gemini 판정 | 합산 |
|---|---|---|---|
| Neon vs Claude | 12/40 (30%) | 39/40 (98%) | 51/80 (64%) |
| Hydrogen vs Claude | 10/40 (25%) | 10/40 (25%) | 20/80 (25%) |
| Neon vs Hydrogen | 15/40 (38%) | 28/40 (70%) | 43/80 (54%) |

지어낸 경험(팁 25편): Neon 5·3, Hydrogen 11·3, Claude 13·13 (Claude 판정·Gemini 판정).
실패율: 직렬 호출 기준 agy 0/16(병렬 실행 중 로그인 풀림은 제외). 소요(병렬 부하 포함): Neon 팁 약 47초·메모 약 25초, Hydrogen 약 20초·13초, Claude 약 80~110초.

해석:
- 판정자 자기 편향이 크다. Neon vs Claude에서 Claude 판정자는 Claude를, Gemini 판정자는 Neon을 압도적으로 골랐다. 다만 Hydrogen은 Gemini 판정자도 Claude보다 낮게 봤다.
- 두 판정자가 일치한 신호는 **Neon의 지어낸 경험이 가장 적다**는 것(Claude의 1/3~1/4).
- 사이드바 모델: **Neon 확정**(Hydrogen 대비 합산 54%, 지어낸 경험 더 적음). `DEFAULT_AGY_MODEL = "gemini-4-neon-low"` 유지.
- B 기준: **미충족.** 두 판정자 모두에서 60% 이상이어야 하는데 Claude 판정에서 30%. 지어낸 경험·실패율 조건은 충족. 야간 배치 변경 제안 없음.
- 추가 조치: 병렬 호출 중 로그인이 풀린 뒤 프로세스 간 파일 잠금을 넣었다(`AGY_LOCK_PATH`).

## 최종 리뷰 (opus 리뷰어 1회, With fixes)

- 고침: 잠금 대기를 timeout 안으로 제한(넘으면 "다른 agy 호출이 끝나지 않아…" 오류), effort는 모델 id 접미사(-low)만 쓰고 `--effort`는 넘기지 않음(분석 호출도 low), agy 자체 시간 제한은 프로세스 타임아웃보다 10초 짧게. 각각 실패 테스트 먼저 확인. 전체 721 passed, 실제 호출 1회 정상.
- 미룬 것(Minor): 손자 프로세스 정리, 문자열 아닌 response 방어, 잠금 경로 TMPDIR 의존, 로그인 풀림 시 재로그인 안내 문구, 직렬화 테스트를 프로세스 간으로.

## 다음 작업

- Owner 커밋 승인. push는 별도.
