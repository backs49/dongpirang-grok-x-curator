# 동피랑 Grok X 추천기 — Design Spec

## Context

X(Twitter)의 추천 알고리즘(x-algorithm)은 오픈소스로 공개되어 있지만, 일반 사용자가 이 원리를 활용해 포스트를 최적화하기는 어렵다. Grok API를 활용하면 x-algorithm의 Phoenix Scorer, multi-action prediction 등 핵심 원리를 자연어로 분석하고 최적화 제안을 할 수 있다.

**목표**: x-algorithm 원리를 기반으로 Grok API가 포스트를 분석/최적화/생성하는 한국어 Streamlit 웹 앱을 만든다.

**배포**: Streamlit Community Cloud

## Architecture

### 파일 구조

```
dongpirang-grok-x-curator/
├── app.py                # 메인 Streamlit UI
├── grok_client.py        # Grok API 클라이언트 (OpenAI SDK 래핑)
├── xalgo_prompts.py      # x-algorithm 기반 system prompt 3종
├── utils.py              # URL 생성, JSON 파싱 헬퍼
├── requirements.txt      # streamlit, openai
├── .streamlit/
│   └── config.toml       # 테마 설정
└── tests/
    ├── test_grok_client.py
    ├── test_utils.py
    └── test_xalgo_prompts.py
```

### 앱 흐름

```
[앱 시작]
  → st.set_page_config(page_title="동피랑 Grok X 추천기", layout="wide", page_icon="🔥")
  → Sidebar:
      - API 키 입력 (st.text_input, type="password")
      - 모델 선택 (st.selectbox: grok-4.1-fast-reasoning, grok-4.20-reasoning)
      - @mangodaon 팔로우 버튼
  → API 키 없으면 → st.warning("API 키를 입력해주세요") + st.stop()
  → GrokClient 인스턴스 생성 (session_state 캐싱)
  → st.tabs(["포스트 최적화", "아이디어 생성", "피드 큐레이터"])
```

## Components

### 1. grok_client.py — GrokClient

```python
class GrokClient:
    def __init__(self, api_key: str, model: str):
        self.client = openai.OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
        self.model = model

    def optimize_post(self, text: str, image_desc: str = "", hashtags: str = "") -> dict:
        """포스트 최적화 분석. JSON 반환."""

    def generate_ideas(self, keywords: str) -> list[dict]:
        """키워드 기반 포스트 아이디어 5개 생성."""

    def curate_feed(self, interests: str) -> list[dict]:
        """live_search tool calling으로 실시간 추천 포스트 3개."""
```

**API 호출 패턴**:
- `response_format={"type": "json_object"}`로 structured output
- `curate_feed`만 `tools` 파라미터로 live_search 활용
- 에러 처리: API 오류 시 사용자 친화적 메시지 반환

### 2. xalgo_prompts.py — System Prompts

3개의 상수 문자열:

**OPTIMIZER_SYSTEM_PROMPT**: x-algorithm의 핵심 원리를 모두 포함
- Phoenix Scorer: 15+ engagement type 동시 예측 (like, reply, repost, quote, click, share, dwell time, follow 등)
- Multi-action weighted scoring: `Final Score = Σ(weight_i × P(action_i))`
- Author diversity: 반복 저자 감쇠 `multiplier = (1-floor) × decay^position + floor`
- Out-of-network discovery: 팔로우 안 한 계정도 추천 가능
- Filter bypass 전략: pre-scoring/post-selection 필터 통과 조건
- Candidate isolation: 포스트 독립 평가 원칙
- 출력 포맷: `{score, engagement_level, reasons, suggestions, optimized_post}`

**IDEAS_SYSTEM_PROMPT**: x-algorithm 최적화된 5개 아이디어 생성
- 각 아이디어에 예상 engagement_level, 최적 게시 시간, 핵심 전략 포함

**CURATOR_SYSTEM_PROMPT**: live_search 도구 활용 실시간 큐레이션
- 관심사와 매칭되는 현재 트렌딩 포스트 검색 지시

### 3. utils.py — 유틸리티

```python
def generate_tweet_intent_url(text: str) -> str:
    """X 공유 intent URL 생성."""

def generate_follow_url(username: str) -> str:
    """X 팔로우 intent URL 생성."""

def parse_grok_json(response_text: str) -> dict:
    """Grok 응답에서 JSON 안전 파싱."""

def append_viral_tag(text: str, tag: str) -> str:
    """바이럴 태그라인 추가."""
```

### 4. app.py — 메인 UI

**Sidebar**:
- `st.text_input("🔑 Grok API Key", type="password", help="console.x.ai에서 발급")`
- `st.selectbox("모델 선택", ["grok-4.1-fast-reasoning", "grok-4.20-reasoning"])`
- API 키 → `st.session_state.api_key`
- 하단: `@mangodaon 팔로우` 링크 버튼

**Tab 1: 포스트 최적화**:
- 입력: `st.text_area("포스트 내용")`, `st.text_input("이미지 설명 (선택)")`, `st.text_input("해시태그 (선택)")`
- 버튼: `st.button("🔍 x-algorithm 분석")`
- 로딩: `st.spinner("Grok이 x-algorithm 분석 중...")`
- 결과:
  - `st.metric("점수", score)` + engagement_level 뱃지
  - `st.expander("분석 이유")` → reasons 리스트
  - `st.expander("개선 제안")` → suggestions 리스트
  - `st.code(optimized_post)` → 최적화된 포스트
- 바이럴:
  - `st.checkbox("최적화된 포스트에 '동피랑 Grok X 추천기로 최적화됨 🔥 @mangodaon' 자동 추가")`
  - `st.button("X에 공유하기")` → 클립보드 복사 또는 intent URL

**Tab 2: 아이디어 생성**:
- 입력: `st.text_input("관심사/키워드")`
- 버튼: `st.button("💡 아이디어 생성")`
- 결과: 5개 카드 형태로 표시 (st.columns + st.container)

**Tab 3: 피드 큐레이터**:
- 입력: `st.text_input("관심사")`
- 버튼: `st.button("🔍 실시간 추천")`
- 결과: 3개 추천 포스트 카드

**Footer**:
- 앱 소개 + `@mangodaon` 팔로우 버튼
- Streamlit Cloud 배포 URL (상수로 관리, 배포 후 업데이트)

## Viral Growth Features

1. **체크박스 태그라인**: Tab 1 결과에서 `동피랑 Grok X 추천기로 최적화됨 🔥 @mangodaon` 자동 추가 옵션
2. **X 공유 버튼**: `https://twitter.com/intent/tweet?text={encoded_text}` 형식
3. **팔로우 버튼**: `https://twitter.com/intent/follow?screen_name=mangodaon`
4. **홍보 포스트 템플릿**: 미리 작성된 앱 홍보 문구 + 앱 링크 포함

## Error Handling

- API 키 미입력: `st.warning` + `st.stop()`
- API 호출 실패: `st.error("Grok API 오류: {message}")` — 재시도 유도
- JSON 파싱 실패: `parse_grok_json`에서 fallback 처리
- live_search tool 미지원 시: 에러 메시지 + "Grok에게 직접 물어보기" fallback

## Testing Strategy

- `test_utils.py`: URL 생성, JSON 파싱, 태그 추가 순수 함수 테스트
- `test_xalgo_prompts.py`: 프롬프트 상수 존재 여부, 필수 키워드 포함 확인
- `test_grok_client.py`: GrokClient 초기화, mock API 호출 테스트
- Streamlit 앱 자체는 수동 테스트 (로컬 실행)

## Verification

1. `pip install -r requirements.txt`
2. `streamlit run app.py`
3. Grok API 키 입력 후 각 탭 기능 테스트
4. 바이럴 버튼들이 올바른 URL 생성하는지 확인
5. 모바일 브라우저에서 레이아웃 확인
