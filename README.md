<p align="center">
  <img src="assets/pink-paw.svg" width="72" alt="핑크 발자국" />
</p>

<h1 align="center">동피랑고양이 Grok 𝕏</h1>

<p align="center">
  <b>X(트위터) 공개 알고리즘(x-algorithm) 분석 기반 포스트 최적화 도구</b><br/>
  Grok(xAI) API로 포스트를 분석·개선하고, 아이디어 생성부터 리스크 체크까지 한 곳에서.
</p>

<p align="center">
  🐾 <a href="https://x.com/mangodaon">@mangodaon</a>
</p>

---

X가 공개한 추천 알고리즘(x-algorithm)의 핵심 원리 — Phoenix Scorer, Multi-Action Prediction, Author Diversity 감쇠 — 를 시스템 프롬프트로 정리해 Grok에게 주입하고, 사용자의 포스트를 그 기준으로 채점·개선하는 Streamlit 앱입니다. 한국어 / English / 日本語 3개 언어를 지원합니다.

## 주요 기능 (8개 탭)

| 탭 | 기능 |
|----|------|
| 📝 **포스트 최적화** | 포스트(+ 이미지 설명, 해시태그)를 x-algorithm 기준으로 0~100점 채점. Reply/Repost/Follow 등 행동별 확률 × 가중치 분해표, 점수 이유 5가지, 개선 제안 5가지, 최적화 리라이트까지 한 번에 제공 |
| 💡 **아이디어 생성** | 관심 키워드로 서로 다른 마무리 스타일의 완성형 포스트 아이디어 5개 생성. 글자수 지정(슬라이더/직접 입력) 가능, 아이디어마다 Grok Imagine·Gemini용 이미지 프롬프트 동봉 |
| 🔍 **피드 큐레이터** | Grok의 `x_search` 도구로 최근 7일간의 실제 X 포스트를 검색해 관심사 맞춤 추천. 추천 이유·참여 힌트·추천 답글 예시 제공 |
| 🧵 **스레드 최적화** | `---` 또는 빈 줄로 구분한 연속 트윗을 Author Diversity 감쇠 공식(`multiplier = (1-floor)×decay^position+floor`) 관점에서 분석·최적화 |
| 📅 **포스팅 스케줄러** | 하루 1~5개 포스트의 주제를 입력하면 감쇠를 최소화하는 최적 게시 시간표를 설계 |
| ⚖️ **A/B 비교** | 두 초안을 동일한 가중치 기준으로 비교 채점해 알고리즘적으로 유리한 쪽을 판별 |
| ⚠️ **리스크 체크** | 수익 중지·계정 정지·노출 제한(섀도밴) 위험을 심각도(🟢🟡🔴🚨)와 카테고리(수익화/정지/노출/반발)별로 진단 |
| 🔄 **언팔 추적** | **API 키 불필요.** X 공식 데이터 아카이브의 `follower.js`(또는 CSV)를 업로드해 스냅샷(최대 10개)으로 저장하고, 스냅샷끼리 비교해 언팔/신규 팔로워를 추적. JSON 백업·복원, CSV 내보내기 지원 |

## 동작 방식

```
사용자 입력 ──▶ tabs/tab_*.py (Streamlit UI)
                    │
                    ▼
              GrokClient (grok_client.py)
              openai SDK + base_url=https://api.x.ai/v1
                    │
        시스템 프롬프트 주입 (xalgo_prompts.py, 탭별 7종)
        + 언어 지시 (i18n.py)
                    │
                    ▼
        Grok 응답 (JSON 강제: response_format=json_object)
                    │
                    ▼
        parse_grok_json (utils.py) ──▶ 결과 렌더링
```

- **`xalgo_prompts.py` (575줄)** — X 공개 알고리즘 리포지토리에서 정리한 원리를 탭별 시스템 프롬프트 7종으로 인코딩: Phoenix Scorer(랭킹 엔진), Multi-Action Prediction(Reply ≈ ×13.5, Repost ≈ ×11.0, Like ≈ ×0.5 등 행동별 가중치), 가중 점수 공식, Author Diversity 감쇠, Out-of-Network Discovery, 필터 통과 전략
- **`grok_client.py`** — openai SDK를 xAI 엔드포인트로 돌려 사용. 대부분의 탭은 Chat Completions + JSON 강제 출력, 피드 큐레이터만 **Responses API + `x_search` 도구**로 실시간 X 검색(최근 7일 범위)을 수행. 일본어/영어 모드에서 답글 예시가 한국어로 새는 경우를 감지해 자동 재번역하는 안전망 포함
- **모델 선택** — `grok-4-1-fast-reasoning` / `grok-4.20-reasoning` 사이드바에서 전환
- **`i18n.py` (1,179줄)** — ko/en/ja 3개 언어 UI 문자열 + 출력 언어 강제 지시문. 시스템 프롬프트 뒤에 언어 지시를 덧붙여 응답 언어를 제어

## 기술 스택

| 구성 요소 | 역할 |
|-----------|------|
| [Streamlit](https://streamlit.io) 1.50 | 전체 UI (8개 탭, 사이드바, 라이트/다크 테마) |
| openai SDK ≥ 1.66 | xAI Grok API 클라이언트 (`base_url=https://api.x.ai/v1`) |
| extra-streamlit-components | API 키 브라우저 쿠키 저장 (CookieManager) |
| streamlit-analytics2 | 익명 사용 현황 집계 (API 키 위젯은 추적 제외) |
| `design.py` | 토큰 기반 CSS 변수 시스템 — 라이트/다크 테마, 핑크 발자국 브랜딩 |
| `i18n.py` | 한국어 / English / 日本語 3개 언어 |

## API 키 처리 (프라이버시)

이 저장소와 서버에는 **어떤 API 키도 포함되어 있지 않습니다.** 사용자가 [console.x.ai](https://console.x.ai)에서 발급받은 본인 키를 직접 입력하는 BYOK(Bring Your Own Key) 구조입니다.

- 키는 사이드바의 password 입력란으로만 받고, "기억하기"를 켜면 **사용자 브라우저 쿠키에만** 저장됩니다 — 서버에 저장되지 않습니다
- 사용량 분석(streamlit-analytics2)이 모든 text_input 값을 수집하는 특성에 대비해 **이중 방어**를 적용: API 키 입력란은 추적에서 제외한 원본 위젯으로 렌더링하고, 집계 데이터 저장 직전에 해당 키 항목을 한 번 더 제거합니다 (`app.py`)
- UI에도 명시: "입력한 키는 이 브라우저에만 저장돼요. 서버·분석 어디에도 남지 않아요."

## 데모 모드

API 키 없이 접속하면 포스트 최적화·아이디어 생성·피드 큐레이터·스레드 최적화 4개 핵심 탭에 **미리 준비된 예시 결과**(`demo_data.py`)가 자동으로 채워져, 키 발급 전에 결과 화면을 그대로 둘러볼 수 있습니다. 실제 키를 입력하면 데모 결과는 자동으로 정리됩니다. 언팔 추적 탭은 로컬 파일 분석이라 키 없이도 온전히 동작합니다.

## 시작하기

```bash
git clone https://github.com/backs49/dongpirang-grok-x-curator.git
cd dongpirang-grok-x-curator

pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속 후, 사이드바에 Grok API 키를 입력하면 모든 기능이 활성화됩니다. (키 없이도 데모 모드 + 언팔 추적은 사용 가능)

## 테스트

pytest 기반 단위 테스트 76개가 4개 파일로 나뉘어 있습니다:

| 파일 | 커버 범위 |
|------|-----------|
| `tests/test_grok_client.py` | GrokClient 초기화·API 호출 (mock 기반, 실제 API 호출 없음) |
| `tests/test_utils.py` | 트윗 인텐트 URL, JSON 파싱, 스레드 분리, 바이럴 태그 |
| `tests/test_unfollow.py` | `follower.js`/CSV 파싱, 팔로워 스냅샷 비교 |
| `tests/test_xalgo_prompts.py` | 시스템 프롬프트 7종의 핵심 원리·JSON 스키마 포함 여부 |

```bash
pip install pytest
pytest tests/
```

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
