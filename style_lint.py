"""생성 텍스트의 AI티 검증기.

프롬프트 안의 금지 지시는 새지만 정규식 검사는 결정적이다.
S1(하나만 있어도 AI 확정으로 읽힘) / S2(1회는 허용, 반복되면 티)의
2단 심각도 구조. S1 검출 시 grok_client 가 해당 아이디어만 1회 재작성한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# (배지 라벨, 패턴) — 라벨은 UI 배지와 재작성 피드백에 그대로 노출된다.
_S1_RAW: tuple[tuple[str, str], ...] = (
    ("'~하는 것이 중요합니다'", r"것이 중요(합니다|하다)"),
    ("'~것이 필요합니다'", r"것이 필요(합니다|하다)"),
    ("'~할 필요가 있다'", r"할 필요가 있"),
    ("'시사하는 바'", r"시사하는 바"),
    ("'주목할 만'", r"주목할 만"),
    ("'결론적으로'", r"결론적으로"),
    ("문두 '또한,'", r"(?:\A|(?<=[.!?\n])\s?)또한,"),
    ("'이를 통해'", r"이를 통해"),
    ("'이처럼'", r"이처럼"),
    ("이중 피동 '되어진다'", r"되어진"),
    ("'~에 있어서'", r"에 있어서"),
    ("'게임체인저'", r"게임\s?체인저"),
    ("em-dash(—)", r"—"),
    ("AI 이모지(✨🚀💡)", r"[✨🚀💡]"),
    ("마크다운 볼드(**)", r"\*\*"),
    ("문두 '오늘은'", r"\A오늘은 "),
    # im-not-ai 택소노미에서 사람 글 0건·AI 전용으로 실측된 패턴
    ("'단순한 ~을 넘어'", r"단순(?:한|히)\s*\S+\s*(?:을|를)?\s*넘어"),
    ("분열문 '중요한 것은'", r"(?:필요한|중요한|더 심각한|뼈아픈) 것은"),
    ("경구 결산 '~의 다른 이름'", r"의 다른 이름이"),
    ("사설 은유(잠식·청사진·적신호)", r"잠식|청사진|적신호|경고등|신호탄"),
)
S1_PATTERNS: tuple[tuple[str, re.Pattern], ...] = tuple(
    (label, re.compile(pat)) for label, pat in _S1_RAW
)

# S2: (라벨, 패턴, 포스트당 허용 횟수) — 초과 시에만 지적. 전부 0으로
# 몰면 과교정으로 오히려 부자연스러워진다. '혁신적'은 allowed=0(한 번만
# 나와도 S2) — "혁신적이지 않았다"처럼 부정형으로 쓰는 정당한 용례가
# 있어서 S1(확정 AI티)로 몰기엔 과하다.
_S2_RAW: tuple[tuple[str, str, int], ...] = (
    ("'정말/매우' 남발", r"정말 |매우 ", 1),
    ("'핵심은' 반복", r"핵심은", 1),
    ("헤징 '~로 보인다' 반복", r"로 보인다|일 수 있습니다", 1),
    ("과장어 '혁신적'", r"혁신적", 0),
    # 결말 결산 공식 — AI 가 글을 매듭지을 때 새로 심는 경향이 실측됨
    ("결산 '~하는 이유다'", r"(?:는|[한인던]) 이유다", 0),
    ("결산 '~로 이어진다'", r"(?:으로|로) 이어진다|에 직결된다", 0),
    ("결말 공식 '~할 때다'", r"[가-힣]+ (?:때|시점)(?:이다|다)[.]?\s*\Z", 0),
    ("'결국' 반복", r"결국", 1),
    ("문두 '문제는/관건은'", r"(?:\A|(?<=[.!?\n])\s?)(?:문제는|관건은)\s", 0),
    ("평가 술어 '~은 분명하다'", r"(?:은|는) (?:명확|분명)하다", 0),
    ("'A가 아니라 B' 반복", r"(?:가|이)\s*아니라", 1),
    ("재정의 '더 이상 ~아니다'", r"더 이상 \S+ (?:않|아니)", 1),
    ("번역투 '~에서의'", r"(?:에서|으로부터|로부터)의\s", 0),
    ("번역투 '~을 가지고 있다'", r"(?:을|를) 가지고 있", 0),
    ("연결어미 뒤 쉼표", r"(?:지만|면서|는데|아서|어서|으며)\s*,", 1),
)
S2_PATTERNS: tuple[tuple[str, re.Pattern, int], ...] = tuple(
    (label, re.compile(pat), allowed) for label, pat, allowed in _S2_RAW
)

_POLITE_RE = re.compile(r"습니다|합니다|해요|예요|네요|하시나요")
_EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF☀-➿]")
_FIRST_ORDINAL_RE = re.compile(r"첫째,")
_SECOND_ORDINAL_RE = re.compile(r"둘째,")


@dataclass
class LintResult:
    s1_hits: list[str] = field(default_factory=list)
    s2_hits: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.s1_hits and not self.s2_hits


def lint(text: str, *, allow_polite: bool = False) -> LintResult:
    """텍스트에서 AI 상투 패턴을 찾는다.

    allow_polite: 침착맨체·하오체처럼 모드가 존댓말 어미를 명시적으로
    요구할 때 True — 평어체 이탈 검사만 끈다.
    """
    result = LintResult()
    for label, pattern in S1_PATTERNS:
        if pattern.search(text):
            result.s1_hits.append(label)
    # '첫째,'/'둘째,' 는 둘 다 나오면(나열) 확정 AI티(S1), 하나만 나오면
    # ("둘째가 아니라 둘째, 오늘은..." 같은 자연스러운 단독 사용도 있어서)
    # 참고 정도(S2)로 낮춘다.
    has_first = bool(_FIRST_ORDINAL_RE.search(text))
    has_second = bool(_SECOND_ORDINAL_RE.search(text))
    if has_first and has_second:
        result.s1_hits.append("'첫째/둘째' 나열")
    elif has_first or has_second:
        result.s2_hits.append("'첫째/둘째' 단독 사용")
    for label, pattern, allowed in S2_PATTERNS:
        if len(pattern.findall(text)) > allowed:
            result.s2_hits.append(label)
    if not allow_polite and len(_POLITE_RE.findall(text)) >= 3:
        result.s2_hits.append("요체/합니다체 연속 (평어체 이탈)")
    if len(_EMOJI_RE.findall(text)) >= 2:
        result.s2_hits.append("이모지 2개 이상")
    return result
