"""tab_ideas 순수 헬퍼 로직 테스트 (Streamlit 위젯 미실행)."""

from __future__ import annotations

from tabs.tab_ideas import _idea_caption_bits, _resolved_image_style


class TestCaptionBits:
    def test_mode_and_charcount(self):
        idea = {"mode": "진지/분석", "content": "가나다라마바사"}
        bits = _idea_caption_bits(idea, post_length=0)
        assert any("진지/분석" in b for b in bits)
        assert any("7" in b for b in bits)

    def test_length_warning_when_off_target(self):
        idea = {"mode": "", "content": "짧다"}
        bits = _idea_caption_bits(idea, post_length=300)
        assert any("±10%" in b or "벗어남" in b for b in bits)

    def test_no_warning_within_tolerance(self):
        idea = {"mode": "", "content": "가" * 300}
        bits = _idea_caption_bits(idea, post_length=300)
        assert not any("벗어남" in b for b in bits)


class TestResolvedImageStyle:
    def test_explicit_style_wins(self):
        assert _resolved_image_style("comic", {"suggested_style": "editorial"}, 0) == "comic"

    def test_auto_uses_suggestion(self):
        assert _resolved_image_style("auto", {"suggested_style": "editorial"}, 0) == "editorial"

    def test_auto_without_suggestion_rotates(self):
        import image_modes

        assert _resolved_image_style("auto", {}, 1) == image_modes.SUGGESTABLE[1]

    def test_none_style_treated_as_auto(self):
        # st.pills 는 선택 해제 시 None 을 돌려준다
        import image_modes

        assert _resolved_image_style(None, {}, 0) == image_modes.SUGGESTABLE[0]
