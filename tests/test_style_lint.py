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
        labels = " ".join(result.s1_hits)
        assert "결론적으로" in labels
        assert "혁신적" in labels
        assert "게임체인저" in labels


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
