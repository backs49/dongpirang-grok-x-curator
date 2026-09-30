<p align="center">
  <img src="assets/pink-paw.svg" width="72" alt="핑크 발자국" />
</p>

<h1 align="center">동피랑고양이 Grok 𝕏</h1>

<p align="center">
  <b>X(트위터) 공개 알고리즘(x-algorithm) 분석 기반 포스트 제작·발행 도구</b><br/>
  주제 한 줄에서 완성 포스트, 이미지, 예약 발행까지. AI가 쓴 티를 지우는 데 집중한다.
</p>

<p align="center">
  🐾 <a href="https://x.com/mangodaon">@mangodaon</a>
</p>

---

X가 공개한 추천 알고리즘(x-algorithm)의 핵심 원리(Phoenix Scorer, Multi-Action Prediction, Author Diversity 감쇠)를 시스템 프롬프트로 정리해 LLM에 주입하고, 그 기준으로 포스트를 만들고 채점하고 다듬는 개인용 도구다. 한국어 / English / 日本語 3개 언어를 지원한다.

앱은 두 개다.

- **NiceGUI 모바일 워크스페이스** (`nicegui_app.py`, 주 진입점): 만들기 → 다듬기 → 발행 세 탭으로 줄인 휴대폰용 화면
- **Streamlit 도구 모음** (`app.py`, 레거시): 분석·실험용 10개 탭

## 모바일 워크스페이스 (NiceGUI)

| 탭 | 기능 |
|----|------|
| **만들기** | 주제 한 줄로 방향 카드 3장을 먼저 받고, 하나를 고르면 그때 완성 글 한 편을 쓴다. 싼 단계(카드)와 비싼 단계(완성 글)를 나눠 호출 비용을 아낀다. **근거 기반 팁** 모드는 카드 선택 뒤 Grok CLI의 웹 검색·페이지 가져오기로 사실을 조사하고, 실제로 확인한 출처 URL만 붙여 쓴다(일상·건강·금융·IT 빌더 4개 분야, 건강·금융은 위험 표현 차단) |
| **다듬기** | 이미 써 둔 글을 붙여넣으면 x-algorithm 기준 점수·이유·제안과 함께 다듬은 글을 돌려준다 |
| **발행** | 발행 큐를 필터로 나눠 보고, 초안을 다음 발행 슬롯에 예약하고, 지난 글을 새 초안으로 되살린다 |

- **끊겨도 안전:** 요청은 분리된 워커 프로세스가 처리하고 결과는 잡 저장소에 영속화한다. 브라우저는 잡 ID만 들고 있어서 재접속하거나 화면이 다시 그려져도 요청이 두 번 나가지 않는다. 자동 재시도는 없다.
- **중복 가드:** 같은 요청이 15분 안에 대기 중이면 새 잡 대신 기존 잡을 돌려준다(탭 간 중복 과금 방지).
- **에디터:** 완성 글은 자동저장되는 에디터로 넘어간다. X 작성 화면 열기, 수동 발행 기록을 지원한다.

## Streamlit 도구 모음 (10개 탭)

| 탭 | 기능 |
|----|------|
| 📝 **포스트 최적화** | 0~100점 채점, 행동별 확률 × 가중치 분해표, 점수 이유 5가지, 개선 제안 5가지, 최적화 리라이트 |
| 💡 **아이디어 생성** | 관심 키워드로 완성형 포스트 5편. 글쓰기 모드 자동 믹스, 글자수 지정, 이미지 장면 브리프·영상 모션 동봉 |
| 🔍 **피드 큐레이터** | 최근 7일 실제 X 포스트를 검색해 관심사 맞춤 추천(X 검색 도구가 있는 Grok CLI·xAI API 엔진 전용) |
| 🧵 **스레드 최적화** | Author Diversity 감쇠 공식(`multiplier = (1-floor)×decay^position+floor`) 관점에서 연속 트윗 분석 |
| 📅 **포스팅 스케줄러** | 하루 1~5개 포스트의 감쇠를 최소화하는 게시 시간표 설계 |
| ⚖️ **A/B 비교** | 두 초안을 같은 가중치 기준으로 비교 채점 |
| ⚠️ **리스크 체크** | 수익 중지·계정 정지·노출 제한 위험을 심각도·카테고리별로 진단 |
| 📬 **발행 큐** | 소재 인박스, 초안 승인·반려, 예약 발행 상태 관리 |
| 📊 **성과 분석** | X 애널리틱스 CSV를 올리면 성과 요약과 수익화 노출 목표 대비 진척을 분석 |
| 🔄 **언팔 추적** | **LLM 불필요.** X 데이터 아카이브의 `follower.js`(또는 CSV) 스냅샷을 비교해 언팔/신규 팔로워 추적 |

## AI 엔진

LLM 호출은 `providers/` 아래 프로바이더 하나로 추상화돼 있다. 구독형 CLI를 우선 쓴다.

| 엔진 | 용도 |
|------|------|
| **Grok CLI** (기본) | 텍스트 생성 전반, 피드 큐레이터·근거 기반 팁의 검색, 이미지·영상 생성(Grok Imagine) |
| **Claude CLI** | 텍스트 생성(Sonnet 고정, 카피라이팅에 최상위 모델은 과함) |
| **Codex CLI** | 텍스트 생성(gpt-6-luna, reasoning low), 이미지 생성 |
| **xAI API** | Streamlit 전용. BYOK 키로 `grok-4.3` 등 API 모델 선택. 키는 이미지·영상 API 백엔드에도 쓴다 |
| **Demo** | 키 없이 미리 준비된 예시 결과로 화면 둘러보기 |

## AI 티 제거

"AI가 쓴 것 같다"는 인상을 지우는 게 이 도구의 핵심 과제다. 세 겹으로 막는다.

1. **언어별 글쓰기 가이드** (`xalgo_prompts.py`): 출력 언어에 맞는 가이드 하나만 붙는다.
   - 한국어: 평어체, 결말 결산 공식·분열문·번역투 금지 ([im-not-ai](https://github.com/epoko77-ai/im-not-ai) 택소노미 기반)
   - 영어: "not X, it's Y", 교훈형 결말, delve·tapestry류 어휘 금지 ([humanizer](https://github.com/blader/humanizer), [sepia](https://github.com/Nanako0129/sepia) 기반)
   - 일본어: くだけた常体, 블로그 상투구·과장어·콜론 금지 ([textlint-rule-preset-ai-writing](https://github.com/textlint-ja/textlint-rule-preset-ai-writing) 기반)
2. **글쓰기 모드 카드** (`writing_modes.py`): 진지/분석, 유머, 풍자, 스토리텔링, 후킹, 빌더 노트, 김훈체, 하루키체, 헤밍웨이체, 침착맨체. 모드마다 리듬·어미 규칙과 예시 문장을 박아 "어설픈 평균치"를 피한다. 여기에 계정 주인의 실제 글을 few-shot으로 넣는 **보이스 카드**(`voice_card.py`)가 붙는다.
3. **정규식 린터** (`style_lint.py`): 생성 뒤 언어별 표로 상투 패턴을 검사한다. S1(한 번만 나와도 AI 확정)이 걸리면 그 글만 한 번 재작성하고, 재작성이 적발 수를 실제로 줄였을 때만 채택한다.

2026-09-29에 언어별 가이드를 넣은 전후를 블라인드 쌍대 판정(생성 Grok, 판정 Claude Sonnet, 언어별 15쌍)으로 측정했다. 한국어는 수정 후가 15쌍 중 12쌍에서 이겼고(p=0.018), 영어는 9쌍, 일본어는 7쌍이었다.

## 이미지·영상

아이디어마다 영어 장면 브리프(`image_prompt`)와 6초 영상 모션(`video_motion`)이 딸려 온다. 그림체는 브리프에 넣지 않고 생성 시점의 **스타일 모드 블록**(`image_modes.py`)이 정한다: 마스코트 3D, 만화/밈, 낙서 두들, 에디토리얼 실사, 시네마틱, 인포그래픽, 레트로 아니메. 시드·네거티브 프롬프트가 없는 Grok Imagine에서 피드의 시각적 일관성을 만드는 유일한 수단이 고정 스타일 블록이기 때문이다.

## 발행 파이프라인

로컬 JSON 큐(`content_queue.py`)를 앱과 배치 스크립트가 파일 락으로 공유한다.

- **야간 초안 생성** (`scripts/generate_drafts.py`, 매일 23시): 초안 재고가 목표 이상이면 아무것도 안 한다. 소재 인박스에 소재가 있으면 초안으로 바꾸고, 없을 때만 팁 초안 1개를 보충한다. 오래 방치된 승인 대기 초안은 관리자에게 리마인드한다.
- **예약 발행** (`scripts/publish_worker.py`, 평일 08·19시, 토 10시): 승인된 초안만 X API(OAuth 1.0a, `publisher.py`)로 발행한다. 멱등이고 기본은 dry-run이며, `--live` 또는 `X_PUBLISH_LIVE=1`일 때만 실제로 올린다. 맥이 잠들어 놓친 슬롯은 다음 빈 슬롯으로 재배정한다.
- **워치독** (`scripts/tunnel_watch.sh`, 매시): 두 앱이 죽어 있으면 살리고, Tailscale Serve로 테일넷 안에만 연다(`:10000` → 워크스페이스, `:10001` → 레거시). 실패가 이어지면 텔레그램으로 한 번만 알리고, 복구되면 다시 알린다.

셋 다 `scripts/*.plist`의 launchd 작업으로 돈다.

## 키 처리 (프라이버시)

저장소에는 어떤 API 키도 없다.

- **xAI API 키** (Streamlit): 사이드바 password 입력으로만 받고 세션 동안만 쓴다. 서버나 브라우저에 저장하지 않는다. streamlit-analytics2가 모든 text_input을 수집하는 특성에 대비해 키 입력란은 추적에서 뺀 원본 위젯으로 그리고, 집계 저장 직전에 키 항목을 한 번 더 지운다(`app.py`).
- **X 발행 키**: `.env`의 소비자 키·액세스 토큰으로만 읽고, 로그와 예외 메시지에 노출하지 않는다.
- **워크스페이스**: 루프백(127.0.0.1)에만 바인딩한다. 외부 노출은 테일넷이 맡는다. 사용자 스토리지에는 언어·테마·엔진 선택처럼 새어 나가도 무해한 값만 둔다.

## 시작하기

```bash
git clone https://github.com/backs49/dongpirang-grok-x-curator.git
cd dongpirang-grok-x-curator

python -m venv venv
venv/bin/pip install -r requirements.txt

# 모바일 워크스페이스 (http://127.0.0.1:8081)
NICEGUI_PORT=8081 venv/bin/python nicegui_app.py

# Streamlit 도구 모음 (http://localhost:8501)
venv/bin/streamlit run app.py
```

CLI 엔진을 쓰려면 `grok`, `claude`, `codex` 중 하나가 PATH에 있고 로그인돼 있어야 한다. 셋 다 없으면 Streamlit의 xAI API(BYOK)나 Demo 모드로 둘러볼 수 있다. 언팔 추적은 LLM 없이 동작한다.

## 테스트

pytest 기반 테스트 619개, 44개 파일. 프로바이더는 전부 가짜로 대체해서 실제 API·CLI 호출은 없다.

```bash
venv/bin/python -m pytest -q
```

## 기술 스택

| 구성 요소 | 역할 |
|-----------|------|
| NiceGUI 3.15 | 모바일 워크스페이스 |
| Streamlit 1.50 | 도구 모음 UI, streamlit-analytics2로 익명 사용 집계 |
| openai SDK ≥ 1.66 | xAI API 클라이언트 (`base_url=https://api.x.ai/v1`) |
| requests-oauthlib | X API 발행 (OAuth 1.0a) |
| launchd + Tailscale Serve | 배치 스케줄링, 테일넷 전용 노출 |
| Python 3.14 | 런타임 |

## 라이선스

**CC BY-NC-ND 4.0** — © 2026 **동피랑고양이** ([@mangodaon](https://x.com/mangodaon))

- **개인적·비상업적 용도**로만 자유롭게 사용 가능합니다
- 상업적 이용, 유료 서비스 제공, 재판매, 코드 수정 후 재배포는 **명백히 금지**됩니다
- 원작자 표시 없이 사용하거나 상업적으로 활용할 경우 법적 조치를 취할 수 있습니다

자세한 내용은 [LICENSE](LICENSE) 참조.

---

<p align="center">
  이 도구는 엑친들과 함께 성장하기 위해 만들어졌습니다. 🐾<br/>
  상업적 목적으로 이용하고 싶으시면 반드시 <a href="https://x.com/mangodaon">@mangodaon</a>에게 DM 주세요.
</p>
