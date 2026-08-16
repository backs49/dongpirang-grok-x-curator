"""글쓰기 모드 카드.

모드는 형용사가 아니라 카드다: 리듬·어미 규칙 + 태도 + 실제 예시 문장 +
모드별 추가 금지. 이름만 주면 LLM 이 어설픈 평균치를 내기 때문에
모든 카드에 예시 문장을 박는다. 예시는 문체 감각 전달용이며 프롬프트에서
소재 복제를 금지한다.

모드 라벨(한글)은 LLM 이 JSON "mode" 필드로 에코하는 값과 일치해야
하므로 i18n 하지 않는다.
"""

from __future__ import annotations

AUTO_MIX = "auto_mix"

# 자동 믹스에서 아이디어 1~5에 순서대로 못박아 배정하는 톤 5종.
# "다양하게 써라"가 아니라 배정표로 다양성을 구조적으로 강제한다.
TONE_ROTATION = ("serious", "humor", "story", "hook", "builder_note")

# 기본 모드는 자동 믹스에 어울리는 안정적인 카드, 실험실 모드는 직접 선택용
# 카드다. 실험실 카드도 일반 생성과 근거 기반 팁 모두에서 선택할 수 있다.
BASE_MODE_KEYS = (
    "serious",
    "humor",
    "story",
    "hook",
    "builder_note",
    "kimhoon",
    "haruki",
    "hemingway",
    "chimchakman",
)
EXPERIMENTAL_MODE_KEYS = ("satire", "haoche", "hankang")

WRITING_MODES: dict[str, dict] = {
    "serious": {
        "label": "진지/분석",
        "category": "tone",
        "allow_polite": False,
        "pillar": "tip",
        "rules": (
            "- 담백한 평어체 -다 단문. 데이터와 경험에 기반한 단정으로 말한다.\n"
            "- 숫자나 고유명사를 최소 1개 포함한다.\n"
            "- 감탄·과장 없이. 마지막 문장은 단정 또는 여운."
        ),
        "examples": [
            "3개월 써보고 내린 결론. 코드 리뷰 시간이 절반으로 줄었다. 대신 설계 논쟁이 두 배가 됐다.",
            "17년 동안 장애 회고를 쓰며 배운 것. 원인은 늘 코드보다 사람 사이에 있었다.",
        ],
        "extra_bans": ["과장 어휘(압도적, 미쳤다)", "느낌표 2개 이상"],
    },
    "humor": {
        "label": "유머",
        "category": "tone",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 웃기려고 애쓰지 않는 담담한 자조가 핵심. 오버 금지.\n"
            "- ㅋㅋ 는 최대 한 번, 어색하면 빼도 된다.\n"
            "- 웃음 포인트는 상황의 아이러니에서 나와야지 말장난에서 나오면 안 된다."
        ),
        "examples": [
            "AI한테 코드 짜달라고 했다가 세 시간째 남의 코드 리뷰 중이다. 내가 AI 코드 리뷰어로 이직한 기분 ㅋㅋ",
            "재택의 최대 적은 회사가 아니라 냉장고였다. 오늘 세 번째 왕복.",
        ],
        "extra_bans": ["말장난·아재개그", "느낌표 남발"],
    },
    "satire": {
        "label": "풍자",
        "category": "tone",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 반어를 정확히 1개 심는다. 겉으로는 칭찬, 속으로는 촌철살인.\n"
            "- 특정 개인·집단을 직접 비난하지 않는다. 현상을 비꼰다.\n"
            "- 냉소로 끝내지 말고 담담한 사실로 끝낸다."
        ),
        "examples": [
            "회의를 줄이자는 회의를 두 시간 했다. 생산성이 이렇게 오른다.",
            "우리 회사도 드디어 AI 전담 조직이 생겼다. 하는 일은 AI 금지 가이드라인 만들기다.",
        ],
        "extra_bans": ["직접 욕설·비하", "정치 소재"],
    },
    "story": {
        "label": "스토리텔링",
        "category": "tone",
        "allow_polite": False,
        "pillar": "retrospective",
        "rules": (
            "- 1인칭 과거형. 장면 하나만 잡고 그 안에서 끝낸다.\n"
            "- 상황 → 전개 → 여운. 교훈을 직접 말하는 순간 실패다.\n"
            "- 시간·장소·감각 디테일 1개 이상."
        ),
        "examples": [
            "새벽 2시에 배포 버튼 앞에서 10분을 망설였다. 눌렀고, 조용했다. 그 조용함이 제일 무서웠다.",
            "면접에서 15년 전 내가 짠 코드를 만났다. 주석에 내 이름이 있었다. 칭찬은 못 들었다.",
        ],
        "extra_bans": ["교훈 문장('결국 ~이 중요하다')", "장면 2개 이상"],
    },
    "hook": {
        "label": "어그로/후킹",
        "category": "tone",
        "allow_polite": False,
        "pillar": "tip",
        "rules": (
            "- 첫 문장은 의외의 단정 또는 구체 숫자. 스크롤이 멈춰야 한다.\n"
            "- 읽는 사람이 한 마디 반박하거나 자기 경험을 얹고 싶어지는 지점(인용각)을 하나 남긴다.\n"
            "- 물음표 남발 금지. 낚시 제목처럼 굴되 본문은 실속으로 채운다."
        ),
        "examples": [
            "17년차가 단언한다. 주니어 때 배운 습관 중 지금도 쓰는 건 커밋 메시지 제대로 쓰기 하나다.",
            "코드 리뷰에서 승인 버튼을 3초 안에 누르는 팀은 코드 리뷰를 안 하는 팀이다.",
        ],
        "extra_bans": ["'~하시나요?' 질문 마무리", "근거 없는 단정"],
    },
    "builder_note": {
        "label": "빌더 노트",
        "category": "tone",
        "allow_polite": False,
        "pillar": "build_in_public",
        "rules": (
            "- 만들고 시험한 장면에서 시작한다. 과장보다 실제 작업의 마찰을 적는다.\\n"
            "- 바꾼 것·막힌 제약·측정한 결과 중 하나를 구체적으로 넣는다.\\n"
            "- 성공담으로 포장하지 말고, 다음 실험을 남기거나 조용히 끝낸다."
        ),
        "examples": [
            "알림 버튼을 하나 덜어냈다. 클릭 수는 줄었는데 저장 완료 문의도 같이 사라졌다. 오늘은 그걸로 충분하다.",
            "검색 결과를 먼저 보여주고 설명은 접었다. 오래된 휴대폰에서는 0.8초 빨라졌다. 내일은 빈 결과 화면을 고친다.",
        ],
        "extra_bans": ["성공 신화", "근거 없는 성장 수치", "훈계조 결론"],
    },
    "kimhoon": {
        "label": "김훈체",
        "category": "author",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 초단문 -다체. 문장은 짧을수록 좋다.\n"
            "- 감정 형용사를 쓰지 않는다. 사물과 몸의 동작으로만 말한다.\n"
            "- 수식어를 걷어내고 명사와 동사만 남긴다."
        ),
        "examples": [
            "서버가 죽었다. 새벽이었다. 몸이 먼저 노트북을 열었다.",
            "커피가 식었다. 코드는 돌지 않았다. 밖에서 첫차 소리가 났다.",
        ],
        "extra_bans": ["감정 형용사(슬펐다, 기뻤다)", "긴 문장", "이모지"],
    },
    "haruki": {
        "label": "하루키체",
        "category": "author",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 담담한 1인칭. '~같은' 직유를 정확히 1개만 넣는다 — 뜬금없지만 정확하게.\n"
            "- 일상 사물(맥주, 레코드, 고양이, 오래된 물건)을 경유해 말한다.\n"
            "- 결론을 내리지 않고 살짝 비켜서서 끝낸다."
        ),
        "examples": [
            "오래된 키보드를 버리지 못하고 있다. 잘 웃던 옛 동료 같은 물건이라서. 맥주를 마시며 새 키보드를 주문했다.",
            "레거시 코드를 읽는 일은 오래된 레코드를 트는 일과 비슷하다. 잡음까지 그 시절의 일부다.",
        ],
        "extra_bans": ["직유 2개 이상", "감탄사"],
    },
    "hemingway": {
        "label": "헤밍웨이체",
        "category": "author",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 짧은 평서문. 부사를 지운다. 형용사도 최소로.\n"
            "- 구체적인 물성(무게, 온도, 소리)으로 말한다.\n"
            "- 한 문장에 하나의 사실만. 번역투 없이 자연스러운 한국어 단문으로."
        ),
        "examples": [
            "코드는 짧았다. 버그는 없었다. 그거면 됐다.",
            "서버 랙은 차가웠다. 손은 빨랐다. 새벽 배포는 그렇게 끝났다.",
        ],
        "extra_bans": ["부사(정말, 매우, 아주)", "복문"],
    },
    "chimchakman": {
        "label": "침착맨체",
        "category": "author",
        "allow_polite": True,
        "pillar": "curation",
        "rules": (
            "- '~거든요', '~란 말이에요' 어미의 능청스러운 구어체.\n"
            "- 당연한 것을 '어쩌면 고정관념일지도 모른다'고 우기는 억지 논리 하나.\n"
            "- 자조 한 스푼으로 마무리. 진지한 척하다가 스스로 무너지는 리듬."
        ),
        "examples": [
            "다들 테스트 코드가 중요하다고 하거든요. 근데 그거 어쩌면 고정관념일 수도 있어요. 물론 저는 씁니다. 무서우니까요.",
            "출근을 해야 일을 한다는 건 편견이거든요. 재택도 일이 됩니다. 침대만 안 보이면요.",
        ],
        "extra_bans": ["공격적 어조", "진지한 결론"],
    },
    "haoche": {
        "label": "하오체",
        "category": "author",
        "allow_polite": True,
        "pillar": "curation",
        "rules": (
            "- '소인은 ~했소', '~하오', '~라오' 하오체. 사극 말투로 일상 기술을 논한다.\n"
            "- 시대착오적 격식과 현대 IT 소재의 부조화가 웃음 포인트.\n"
            "- 끝까지 캐릭터를 깨지 않는다."
        ),
        "examples": [
            "소인, 오늘도 레거시와 싸웠소. 이기지 못했소. 다만 물러서지도 않았소.",
            "GPU 값이 천정부지라 하오. 소인의 맥북은 오늘도 팬만 돌리오.",
        ],
        "extra_bans": ["현대 존댓말 혼입", "캐릭터 이탈"],
    },
    "hankang": {
        "label": "한강체",
        "category": "author",
        "allow_polite": False,
        "pillar": "curation",
        "rules": (
            "- 조용한 감각 장면 하나에서 시작한다. 빛, 온도, 소리, 손의 움직임을 구체적으로 적는다.\\n"
            "- 감정을 설명하기보다 빈자리와 사물을 따라간다. 문장은 느리되 장식하지 않는다.\\n"
            "- 뜻을 해설하지 않고, 조금 남겨 둔 채 끝낸다."
        ),
        "examples": [
            "모니터의 푸른 빛이 책상 가장자리까지만 왔다. 커서가 한참 같은 자리에 있었다. 창문 밖에서는 누군가 우산을 접었다.",
            "새 버전을 올린 뒤에도 팬은 계속 돌았다. 손바닥에 남은 열을 닦지 않았다. 로그는 아직 열려 있었다.",
        ],
        "extra_bans": ["감정의 직접 해설", "상징의 설명", "극적인 반전"],
    },
}


def base_mode_options() -> tuple[str, ...]:
    """기본 선택 영역에 표시할 안정적인 글쓰기 모드."""
    return BASE_MODE_KEYS


def experimental_mode_options() -> tuple[str, ...]:
    """자동 믹스에는 넣지 않되 직접 선택 가능한 실험실 모드."""
    return EXPERIMENTAL_MODE_KEYS


def mode_options() -> list[str]:
    """UI pills 순서: 자동 믹스 → 기본 모드 → 실험실 모드."""
    return [AUTO_MIX, *BASE_MODE_KEYS, *EXPERIMENTAL_MODE_KEYS]


def mode_label(key: str) -> str:
    if key == AUTO_MIX:
        return "자동 믹스"
    card = WRITING_MODES.get(key)
    return card["label"] if card else key


def label_to_key(label: str) -> str:
    # 자동 믹스 배정표가 "[진지/분석]" 처럼 대괄호로 라벨을 렌더링하고
    # LLM 이 대괄호를 그대로 에코하는 경우가 있어, 매칭 전에 앞뒤 공백과
    # 대괄호를 벗겨낸다.
    cleaned = label.strip().strip("[]").strip()
    for key, card in WRITING_MODES.items():
        if card["label"] == cleaned:
            return key
    return ""


def allow_polite(key: str) -> bool:
    card = WRITING_MODES.get(key)
    return bool(card and card["allow_polite"])


def pillar_for_mode(key: str) -> str:
    card = WRITING_MODES.get(key)
    return card["pillar"] if card else "curation"


def _card(key: str) -> str:
    m = WRITING_MODES[key]
    lines = [f"### [{m['label']}] 모드 카드", m["rules"]]
    lines.append("실제 예시 (문체의 감각만 흡수할 것 — 소재·문장·단어 복제 금지):")
    lines.extend(f"- {ex}" for ex in m["examples"])
    if m["extra_bans"]:
        lines.append("이 모드 추가 금지: " + ", ".join(m["extra_bans"]))
    return "\n".join(lines)


def build_mode_block(mode_key: str) -> str:
    """IDEAS 시스템 프롬프트 뒤에 붙일 모드 블록."""
    if mode_key == AUTO_MIX:
        table = "\n".join(
            f"- 아이디어 {i + 1}: [{WRITING_MODES[k]['label']}]"
            for i, k in enumerate(TONE_ROTATION)
        )
        cards = "\n\n".join(_card(k) for k in TONE_ROTATION)
        return (
            "\n\n# 글쓰기 모드 배정 (자동 믹스 — 반드시 지킬 것)\n"
            "5개 아이디어를 아래 배정표의 모드로 각각 작성한다. "
            '각 아이디어의 "mode" 필드에 배정된 모드 이름을 그대로 넣는다.\n'
            f"{table}\n\n{cards}\n"
        )
    m = WRITING_MODES[mode_key]
    return (
        f"\n\n# 글쓰기 모드: [{m['label']}] — 5개 아이디어 전부 이 모드로 작성\n"
        f'모든 아이디어의 "mode" 필드에 "{m["label"]}" 를 넣는다.\n\n'
        f"{_card(mode_key)}\n"
    )
