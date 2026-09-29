"""AI티 검증기 테스트."""

from __future__ import annotations

from style_lint import lint


class TestS1Patterns:
    def test_clean_text_passes(self):
        text = "3개월 써보고 내린 결론. 코드 리뷰 시간이 절반으로 줄었다.\n대신 설계 논쟁이 두 배가 됐다."
        result = lint(text)
        assert result.clean
        assert result.s1_hits == []
        assert result.s2_hits == []

    def test_detects_cliche_endings(self):
        result = lint("꾸준함을 유지하는 것이 중요합니다.")
        assert not result.clean
        assert any("중요합니다" in h for h in result.s1_hits)

    def test_detects_listing_and_connectives(self):
        result = lint("첫째, 기록해라. 둘째, 공유해라. 이를 통해 성장한다.")
        labels = " ".join(result.s1_hits)
        assert "첫째" in labels
        assert "이를 통해" in labels

    def test_duljjae_without_comma_not_flagged(self):
        # "둘째가 태어났다" 처럼 서수사가 아닌 경우 콤마 앵커가 없으면
        # 오탐하지 않아야 한다.
        result = lint("둘째가 태어났다. 기뻤다.")
        assert result.s1_hits == []

    def test_first_and_second_ordinal_together_is_s1(self):
        result = lint("둘째, 오늘 유치원에 갔다. 첫째, 아침을 먹었다.")
        assert any("나열" in h for h in result.s1_hits)

    def test_detects_em_dash_and_ai_emoji(self):
        result = lint("오늘 배포했다 — 성공적이었다 🚀")
        labels = " ".join(result.s1_hits)
        assert "em-dash" in labels
        assert "이모지" in labels

    def test_detects_markdown_bold_and_leading_oneul(self):
        result = lint("오늘은 **중요한** 이야기를 하려 한다.")
        labels = " ".join(result.s1_hits)
        assert "볼드" in labels
        assert "오늘은" in labels

    def test_conclusion_and_hedging_words(self):
        result = lint("결론적으로 혁신적인 도구다. 게임체인저라 할 만하다.")
        s1_labels = " ".join(result.s1_hits)
        s2_labels = " ".join(result.s2_hits)
        assert "결론적으로" in s1_labels
        assert "게임체인저" in s1_labels
        # '혁신적'은 부정형("혁신적이지 않았다")도 정당한 용례라 S1 이 아니라
        # S2(1회는 허용, 반복 시에만 지적)로 낮췄다.
        assert "혁신적" not in s1_labels
        assert "혁신적" in s2_labels


class TestS2Patterns:
    def test_single_use_allowed(self):
        result = lint("정말 오랜만에 코드가 한 번에 돌았다. 기분이 이상했다.")
        assert result.s2_hits == []

    def test_repeated_emphasis_flagged(self):
        result = lint("정말 좋았다. 정말 놀라웠고 매우 매끄러웠다.")
        assert any("남발" in h for h in result.s2_hits)

    def test_polite_run_flagged_by_default(self):
        text = "오늘 배포했습니다. 잘 됐습니다. 내일도 합니다."
        result = lint(text)
        assert any("평어체" in h for h in result.s2_hits)

    def test_polite_run_allowed_when_mode_permits(self):
        text = "오늘 배포했습니다. 잘 됐습니다. 내일도 합니다."
        result = lint(text, allow_polite=True)
        assert not any("평어체" in h for h in result.s2_hits)

    def test_multiple_emoji_flagged(self):
        result = lint("배포 완료 😀 다들 고생했다 😀")
        assert any("이모지" in h for h in result.s2_hits)

    def test_hedging_repeat_flagged(self):
        result = lint("효과가 있는 것으로 보인다. 시장도 반응할 것으로 보인다.")
        assert any("헤징" in h for h in result.s2_hits)

    def test_second_ordinal_alone_is_s2_not_s1(self):
        result = lint("둘째, 오늘 유치원에 갔다.")
        assert not any("나열" in h for h in result.s1_hits)
        assert any("단독" in h for h in result.s2_hits)

    def test_negated_innovative_is_s2_not_s1(self):
        result = lint("혁신적이지 않았다.")
        assert not any("혁신적" in h for h in result.s1_hits)
        assert any("혁신적" in h for h in result.s2_hits)


class TestKoreanImNotAiPatterns:
    """im-not-ai 택소노미에서 들여온 한국어 패턴."""

    def test_s1_beyond_and_cleft(self):
        result = lint("단순한 도구를 넘어 동료다. 중요한 것은 속도다.")
        labels = " ".join(result.s1_hits)
        assert "넘어" in labels
        assert "분열문" in labels

    def test_s1_editorial_metaphor_and_epigram(self):
        result = lint("레거시가 팀을 잠식했다. 기다림은 포기의 다른 이름이다.")
        labels = " ".join(result.s1_hits)
        assert "사설 은유" in labels
        assert "다른 이름" in labels

    def test_s2_closing_formulas(self):
        result = lint("그게 우리가 문서를 쓰는 이유다. 이제 움직일 때다.")
        labels = " ".join(result.s2_hits)
        assert "이유다" in labels
        assert "할 때다" in labels

    def test_s2_translationese(self):
        result = lint("회사에서의 나는 권한을 가지고 있다.")
        labels = " ".join(result.s2_hits)
        assert "에서의" in labels
        assert "가지고 있다" in labels

    def test_single_contrast_and_single_gyeolguk_allowed(self):
        # "A가 아니라 B"·"결국"·연결어미 쉼표는 한 번은 정상 수사다.
        result = lint("버그가 아니라 설정이었다. 결국 캐시였지만, 찾는 데 하루 걸렸다.")
        assert result.s1_hits == []
        assert result.s2_hits == []

    def test_mid_sentence_munjeneun_not_flagged(self):
        result = lint("어제 배포에 문제는 없었다.")
        assert result.clean


class TestEnglishPatterns:
    """humanizer·sepia 기반 영어 표."""

    def test_clean_english_passes(self):
        text = (
            "Spent two hours on a flaky test yesterday. The cache TTL was 0 in staging. "
            "Nobody wrote that down anywhere, so I did."
        )
        assert lint(text, lang="en").clean

    def test_s1_contrast_vocab_and_closer(self):
        text = "It's not just a tool, it's a mindset. Let's delve in. The future looks bright."
        labels = " ".join(lint(text, lang="en").s1_hits)
        assert "not X" in labels
        assert "delve" in labels
        assert "closer" in labels

    def test_korean_table_not_applied_to_english(self):
        # 한국어 요체 검사·한국어 패턴은 영어에 돌지 않는다.
        assert lint("결론적으로 좋았습니다.", lang="en").s1_hits == []

    def test_honestly_mid_sentence_is_human(self):
        assert lint("I honestly thought the build would pass.", lang="en").clean

    def test_s2_same_opener_and_bait(self):
        text = "I tried the new CLI. I broke prod. I rolled back at 2am. Anyone else?"
        labels = " ".join(lint(text, lang="en").s2_hits)
        assert "opener" in labels
        assert "bait" in labels


class TestStyleGuideRouting:
    def test_guide_per_language(self):
        from xalgo_prompts import (
            NATURAL_STYLE_GUIDE,
            NATURAL_STYLE_GUIDE_EN,
            NATURAL_STYLE_GUIDE_JA,
            style_guide_for,
        )

        assert style_guide_for("ko") is NATURAL_STYLE_GUIDE
        assert style_guide_for("en") is NATURAL_STYLE_GUIDE_EN
        assert style_guide_for("ja") is NATURAL_STYLE_GUIDE_JA
        assert style_guide_for("xx") is NATURAL_STYLE_GUIDE

    def test_english_prompt_does_not_stack_korean_guide(self):
        from grok_client import GrokClient
        from xalgo_prompts import NATURAL_STYLE_GUIDE, NATURAL_STYLE_GUIDE_EN

        class Fake:
            def __init__(self):
                self.calls = []

            def generate_json(self, system_prompt, user_prompt, **kw):
                self.calls.append(system_prompt)
                return {"score": 1}

        fake = Fake()
        GrokClient(provider=fake).optimize_post("body", language="en")
        assert NATURAL_STYLE_GUIDE_EN in fake.calls[0]
        assert NATURAL_STYLE_GUIDE not in fake.calls[0]


class TestJapanesePatterns:
    """textlint-rule-preset-ai-writing 기반 일본어 표."""

    def test_clean_japanese_passes(self):
        text = "昨日、本番のキャッシュが全部飛んだ。原因はTTLの設定ミス。三時間溶けたけど、ログは残ってた。"
        assert lint(text, lang="ja").clean

    def test_s1_blog_cliches_and_hype(self):
        text = "今回はAIについて解説します。まさにゲームチェンジャーと言えるでしょう。いかがでしたか？"
        labels = " ".join(lint(text, lang="ja").s1_hits)
        assert "ブログ定型句" in labels
        assert "ぼかし結び" in labels
        assert "誇張語" in labels

    def test_intro_colon_and_heading(self):
        labels = " ".join(lint("結論：早く帰れ。\n【まとめ】以上。", lang="ja").s1_hits)
        assert "導入コロン" in labels
        assert "見出し" in labels

    def test_polite_run_and_same_ending(self):
        text = "今日は晴れです。散歩しました。楽しかったです。"
        assert any("です・ます" in h for h in lint(text, lang="ja").s2_hits)
        text2 = "眠いんだ。疲れたんだ。帰るんだ。"
        assert any("文末" in h for h in lint(text2, lang="ja").s2_hits)

    def test_casual_saikou_once_allowed(self):
        assert lint("仕事終わりのビールが最高のご褒美だった。", lang="ja").clean

    def test_clock_time_colon_not_flagged(self):
        assert lint("14:30にデプロイして、15:10に戻した。", lang="ja").clean


def test_generate_ideas_uses_explicit_language():
    """워커가 넘긴 language 로 가이드와 출력 언어 지시가 결정된다."""
    from grok_client import GrokClient
    from i18n import get_lang_instruction
    from xalgo_prompts import NATURAL_STYLE_GUIDE, NATURAL_STYLE_GUIDE_JA

    class Fake:
        def generate_json(self, system_prompt, user_prompt, **kw):
            self.system = system_prompt
            return {"error": "stop"}

    fake = Fake()
    GrokClient(provider=fake).generate_ideas("AI", language="ja")
    assert NATURAL_STYLE_GUIDE_JA in fake.system
    assert NATURAL_STYLE_GUIDE not in fake.system
    assert get_lang_instruction("ja") in fake.system


class TestKoreanSecondOrder:
    """상투어를 피한 모델이 대신 쓰는 2차 AI 티 (2026-09-29 실사례)."""

    def test_telegraphic_noun_endings(self):
        text = "영화를 봤다. 감독은 허진호. 개봉은 9월. 가설 칸은 접힘. 오늘은 여기까지 했다."
        assert any("명사 종결" in h for h in lint(text).s2_hits)

    def test_fact_dump(self):
        text = "누적 163만3616명, 점유 26.8%, 평점 8.3과 2.2. 1974년 8월 15일 일이다."
        assert any("숫자" in h for h in lint(text).s2_hits)

    def test_fade_out_closer_and_staged_scene(self):
        text = "영화가 끝났다. 저녁 바람이 목덜미로 들어왔다. 나는 한 박자 늦게 발을 뗐다."
        labels = " ".join(lint(text).s2_hits)
        assert "여운" in labels
        assert "배경 연출" in labels

    def test_short_fade_line(self):
        assert any("여운" in h for h in lint("앞줄이 숨을 내쉬었다. 박수는 없었다.").s2_hits)

    def test_plain_conversational_post_is_clean(self):
        text = (
            "이 영화 논란은 좀 지나치다고 본다. 창작이라도 실존 인물의 죽음을 다룰 때는 "
            "확인된 사실과 추측을 구분해 줘야 하는데, 그 선을 흐려 놓고 표현의 자유라고 하면 "
            "납득이 안 된다. 보고 나서 든 생각이 그거였다."
        )
        assert lint(text).clean


def test_en_and_ja_fact_dump_and_taigen():
    en = "Released 9/23. 1.63M viewers. Rated 8.3 vs 2.2. Set on 8/15/1974."
    assert any("fact dump" in h for h in lint(en, lang="en").s2_hits)
    ja = "映画を見た。監督は許秦豪。公開は9月。評価は二極化。争点は計画説。"
    assert any("体言止め" in h for h in lint(ja, lang="ja").s2_hits)
