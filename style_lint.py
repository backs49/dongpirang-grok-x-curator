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


def lint(text: str, *, allow_polite: bool = False, lang: str = "ko") -> LintResult:
    """텍스트에서 AI 상투 패턴을 찾는다.

    allow_polite: 침착맨체·하오체처럼 모드가 존댓말 어미를 명시적으로
    요구할 때 True — 평어체 이탈 검사만 끈다(한국어 전용).
    lang: 출력 언어. AI 티는 언어마다 달라서 언어별 표를 쓴다.
    """
    if lang == "en":
        return _lint_en(text)
    if lang == "ja":
        return _lint_ja(text, allow_polite=allow_polite)
    return _lint_ko(text, allow_polite=allow_polite)


def _count_hits(text: str, result: LintResult, s1, s2) -> None:
    for label, pattern in s1:
        if pattern.search(text):
            result.s1_hits.append(label)
    for label, pattern, allowed in s2:
        if len(pattern.findall(text)) > allowed:
            result.s2_hits.append(label)


def _lint_ko(text: str, *, allow_polite: bool) -> LintResult:
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


# 영어 — humanizer(SKILL.md 26패턴)·sepia(style-pass) 에서 짧은 1인칭 X 포스트에
# 해당하는 것만. 캐주얼 담화 표지("honestly", "actually")는 사람다운 요소라
# 문두 단독 "Honestly?" 만 잡는다.
_EN_S1_RAW: tuple[tuple[str, str], ...] = (
    ("chatbot residue", r"(?i)\b(?:i hope (?:this|that) helps|great question|you'?re absolutely right|let me know if|feel free to)\b"),
    ("'not X, it's Y'", r"(?i)\bnot\s+(?:just|only|merely|simply)\s+[^.!?]{1,60}[,;]\s*(?:but|it'?s)\b"),
    ("'in today's fast-paced world'", r"(?i)\bin (?:today'?s|this|an?) (?:fast[- ]paced|ever[- ]changing|ever[- ]evolving|rapidly (?:changing|evolving)|digital) (?:world|age|landscape|era)\b"),
    ("'let that sink in'", r"(?i)\b(?:let that sink in|read that again)\b"),
    ("throat-clearing opener", r"(?i)(?:^|[.!?]\s+)(?:here'?s the thing|the thing is[,:]|real talk|let'?s be honest|honestly\?)|\b(?:let'?s dive in|without further ado)\b"),
    ("AI vocabulary (delve, tapestry...)", r"(?i)\b(?:delv(?:e|es|ed|ing)|tapestry|testament to|underscor(?:e|es|ed|ing)|pivotal|multifaceted|realm|beacon)\b"),
    ("marketing hype (game-changer...)", r"(?i)\b(?:game[- ]?chang\w*|seamless\w*|unleash\w*|supercharg\w*)\b"),
    ("moral/future closer", r"(?i)\b(?:the future (?:looks|is) bright|exciting times ahead|in conclusion|to sum up|key takeaway)\b"),
    ("false depth ('at its core')", r"(?i)\b(?:at its core|the real question is|what really matters|the heart of the matter)\b"),
    ("-ing commentary tail", r",\s+(?:highlighting|underscoring|showcasing|reflecting|fostering|ensuring)\b"),
    ("staccato fragments ('No X. No Y. No Z.')", r"(?:\bNo \w+\.\s+){2}No \w+\."),
    ("em/en dash", r"[—–]|\s--\s"),
    ("AI emoji", r"[✨🚀💡]"),
    ("markdown bold (**)", r"\*\*"),
)
EN_S1_PATTERNS = tuple((label, re.compile(pat)) for label, pat in _EN_S1_RAW)

_EN_S2_RAW: tuple[tuple[str, str, int], ...] = (
    ("'isn't just' contrast", r"(?i)\bisn'?t\s+(?:just|only|merely)\b", 1),
    ("soft hype words (crucial, vibrant...)", r"(?i)\b(?:crucial|vibrant|intricate|foster\w*|navigat\w*|landscape|journey|elevat\w*|harness\w*|robust|thrilled)\b", 1),
    ("strawman ('don't get me wrong')", r"(?i)\b(?:don'?t get me wrong|to be clear|i'?m not saying)\b", 1),
    ("'serves as / stands as / boasts'", r"(?i)\b(?:serves as|stands as|boasts)\b", 0),
    ("filter verbs ('I realized')", r"(?i)\bI (?:realized|noticed|felt)\b", 1),
    ("engagement-bait ending", r"(?i)(?:thoughts|agree|anyone else)\?\s*\Z", 0),
    ("'at the end of the day'", r"(?i)\bat the end of the day\b", 0),
)
EN_S2_PATTERNS = tuple((label, re.compile(pat), allowed) for label, pat, allowed in _EN_S2_RAW)

_EN_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")


def _same_opener_run(text: str, run: int = 3) -> bool:
    """문장 첫 단어가 run 번 연속 같은지 ("I tried... I found... I realized...")."""
    firsts = [
        m.group().split()[0].lower()
        for m in _EN_SENTENCE_RE.finditer(text)
        if m.group().split()
    ]
    return any(len(set(firsts[i : i + run])) == 1 for i in range(len(firsts) - run + 1))


def _lint_en(text: str) -> LintResult:
    result = LintResult()
    _count_hits(text, result, EN_S1_PATTERNS, EN_S2_PATTERNS)
    if _same_opener_run(text):
        result.s2_hits.append("same sentence opener 3x in a row")
    if len(_EMOJI_RE.findall(text)) >= 2:
        result.s2_hits.append("2+ emoji")
    return result


# 일본어 — textlint-rule-preset-ai-writing(no-ai-hype-expressions,
# ai-tech-writing-guideline, no-ai-colon-continuation)의 리터럴을 옮기고
# 블로그형 AI 상투구를 더했다. 기술문서 전용 규칙(適切な·効率的な, 수동태,
# 용어 일관성)은 짧은 구어 포스트에서 오탐만 늘려서 뺐다.
_JA_S1_RAW: tuple[tuple[str, str], ...] = (
    ("ブログ定型句（いかがでしたか等）", r"いかがでしたか|について(?:解説|ご紹介|まとめ)(?:します|しました|していきます)|ぜひ参考に|参考になれば幸いです"),
    ("ぼかし結び（と言えるでしょう等）", r"と言えるでしょう|ではないでしょうか"),
    ("教訓まとめ（することが重要）", r"することが(?:重要|大切|大事)(?:です|だ)"),
    ("結論定型（結論として・まとめると）", r"結論(?:として|から言うと)|まとめると"),
    ("誇張語（ゲームチェンジャー等）", r"ゲームチェンジャー|パラダイムシフト|可能性を解き放つ|潜在能力を引き出す|スーパーチャージ|業界を再定義|新たな基準を設定|フロンティアを開拓|根本的に変革|民主化する|魔法のように|驚嘆させ"),
    ("序数列挙（第一に）", r"第一に"),
    ("見出し【】", r"(?:\A|\n)\s*【[^】]*】"),
    ("ハッシュタグ", r"[#＃][^\s#＃]+"),
    ("導入コロン（結論：）", r"(?:\A|\n)[^\n：:\d]{1,8}[：:]"),
    ("ダッシュ（—）", r"[—–]"),
    ("AI絵文字（✨🚀💡）", r"[✨🚀💡]"),
    ("マークダウン太字（**）", r"\*\*"),
    ("箇条書き", r"(?m)^\s*[-*+・]\s"),
)
JA_S1_PATTERNS = tuple((label, re.compile(pat)) for label, pat in _JA_S1_RAW)

_JA_S2_RAW: tuple[tuple[str, str, int], ...] = (
    ("誇張語（革命的・究極の等）", r"革命的な|世界初の|究極の|完璧な|最先端の|次世代の|未来を変える|奇跡的な|驚異的な|不可避の", 1),
    ("口語でも出る強調（完全に・最高の）", r"完全に|最高の|大幅に", 2),
    ("まさに・革新的・画期的", r"まさに|革新的|画期的", 1),
    ("文中コロン", r"[：:](?!\d)", 1),  # 時刻 14:30 は除外
    ("「また、」反復", r"また、", 1),
    ("冗長表現（することができる）", r"することができ(?:る|ます)|する必要があ(?:る|ります)|言うまでもなく", 1),
)
JA_S2_PATTERNS = tuple((label, re.compile(pat), allowed) for label, pat, allowed in _JA_S2_RAW)

_JA_POLITE_RE = re.compile(r"です[。！？\n]|ます[。！？\n]|でした[。！？\n]|ました[。！？\n]")
_JA_SENTENCE_END_RE = re.compile(r"(..)[。！？!?]")


def _lint_ja(text: str, *, allow_polite: bool) -> LintResult:
    result = LintResult()
    _count_hits(text, result, JA_S1_PATTERNS, JA_S2_PATTERNS)
    # 같은 문말 3연속 — 한국어의 "같은 어미 4연속"을 짧은 일본어 글에 맞춰 3으로
    ends = _JA_SENTENCE_END_RE.findall(text)
    if any(ends[i] == ends[i + 1] == ends[i + 2] for i in range(len(ends) - 2)):
        result.s2_hits.append("同じ文末が3連続")
    if not allow_polite and len(_JA_POLITE_RE.findall(text)) >= 2:
        result.s2_hits.append("です・ます調（常体からの逸脱）")
    if len(_EMOJI_RE.findall(text)) >= 2:
        result.s2_hits.append("絵文字2つ以上")
    return result
