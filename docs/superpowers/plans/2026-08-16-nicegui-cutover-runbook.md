# NiceGUI 워크스페이스 컷오버 런북 (Task 10)

브랜치 `worktree-nicegui-workspace`(HEAD 854ea77, 566 테스트 통과)를 main에 머지한
직후부터의 활성화 절차. **이 머신에서 main 머지 = 사실상 활성화 시작**이다:
launchd가 매시간 새 tunnel_watch.sh를 실행하고, Streamlit은 app.py 변경을
핫리로드한다. 따라서 머지와 아래 절차는 한 세션에서 연속으로 실행한다.

## ⚠ 순서가 안전을 결정한다 (최종 리뷰 Important #1)

머지 후 app.py에는 비밀번호 게이트가 없다. 그런데 기존 Funnel(:10000 → 8501)은
**퍼블릭**이므로, funnel을 끄기 전에 Streamlit이 새 코드로 재시작되면 게이트 없는
레거시 앱이 최대 1시간 동안 인터넷에 노출된다. 반드시 이 순서를 지킨다:

1. **머지 전**: 라이브 venv 준비 — `venv/bin/python -m pip install -r requirements.txt`
   (nicegui 3.15.0, pytest-asyncio 추가; streamlit 핀 불변).
2. **main 머지** (fast-forward 또는 merge commit).
3. **즉시 funnel 차단**: `/opt/homebrew/bin/tailscale funnel --https=10000 off`
   (또는 새 tunnel_watch.sh를 수동으로 1회 실행 — 앱 기동이 실패해도
   funnel-off는 실행된다).
4. **검증**: `tailscale serve status --json`에서 :10000의 AllowFunnel 항목이
   사라졌고, **:443과 :8443(ai-trader)은 그대로**인지 확인.
   절대 `serve reset` / `funnel reset` 금지 — 포트 단위 명령만.
5. 새 watchdog 실행(3에서 수동 실행 안 했다면):
   `bash scripts/tunnel_watch.sh` — NiceGUI(8081)·Streamlit(8501) 기동,
   serve :10000→8081, :10001→8501 구성, logs/workspace.url·legacy.url 기록.
   참고: :10001이 처음 잡히기 전 첫 실행은 exit 1로 끝날 수 있다(다음 실행에서
   자가 회복) — 첫 실행의 종료 코드는 헬스 신호가 아니다.
6. `launchctl kickstart -k "gui/$(id -u)/com.dongpirang.tunnel"`로 정식 기동.
7. 뒷정리:
   - `rm logs/funnel.url` (더 이상 쓰지 않는 파일; generate_drafts는 이제
     workspace.url을 읽는다)
   - `.env`에서 `APP_ACCESS_PASSWORD` 제거(이제 어디서도 읽지 않음)
   - AGENTS.md 133–136행의 Funnel/비밀번호 서술을 Serve/이중 앱 구조로 갱신
8. **모바일 인수 테스트** (Tailscale 연결된 폰):
   1. `https://<host>.ts.net:10000` — 비밀번호 없이 열리는지
   2. 주제 입력 → 방향 3개 → 브라우저 백그라운드 → 복귀 시 같은 잡이 재개되고
      중복 제출이 없는지
   3. 방향 선택 → 완성 포스트 → 편집 → X 작성 화면 → 복귀 후 게시했음 →
      Publish 이력에 표시되는지
   4. 두 번째 포스트를 큐 저장 → 승인 → Scheduled에 보이는지
   5. `:10001`에서 레거시 Streamlit 도구가 그대로 동작하는지

수용 기준은 설계 문서(2026-08-16-nicegui-mobile-workspace-design.md)의 1–5.

## 백로그 (최종 리뷰 선별, 가치 순)

**2026-08-17 전량 완료** — 계획 docs/superpowers/plans/2026-08-17-nicegui-backlog.md.

1. ~~workspace_jobs.json 완료/실패 잡 프루닝~~ (TTL 7일·terminal 최대 200)
2. ~~i18n을 Streamlit 의존 없는 모듈로 분리~~ (get_lang() 지연 임포트로 동일 효과)
3. ~~grounded 근거 URL·Polish 점수/이유를 UI에 표출~~
4. ~~design.py ↔ theme.py 팔레트 드리프트 테스트~~
5. ~~pytest 9 + pytest-asyncio 1.x 업그레이드~~ (filterwarnings=error, 경고 0)
6. ~~Serve 구성 실패 시 Telegram 경보~~ (실패 집합 상태파일로 중복 억제)
7. ~~멀티 탭 동시 제출 가드~~ (create_job 멱등화: pending 동일요청 15분 창)
8. ~~문구 통일·평어체화~~ ("근거 기반 팁" 정본, ideas_error_* 4건)

### 후속 소항목 (최종 리뷰 발견, 비차단)

- PENDING/TERMINAL 상태 튜플이 workspace_jobs.py와 job_view.py에 값 복제로
  존재 — 동기화 테스트 추가하면 좋다.
- 워커가 죽어 queued로 남은 잡은 프루닝 면제라 영구 누적 — 스토어가 커지면
  stale-queued 청소 규칙 추가.
