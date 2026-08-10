"""tab_ideas 순수 헬퍼 로직 테스트 (Streamlit 위젯 미실행)."""

from __future__ import annotations

import streamlit as st

from tabs.tab_ideas import (
    _clear_stale_media_state,
    _idea_caption_bits,
    _resolved_image_style,
)


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


class TestV2Flow:
    def test_v2_when_version_matches(self):
        import streamlit as st

        from tabs.tab_ideas import _use_v2_image_flow
        from xalgo_prompts import PROMPT_VERSION

        st.session_state["ideas_prompt_version"] = PROMPT_VERSION
        assert _use_v2_image_flow() is True

    def test_legacy_when_version_missing_or_old(self):
        import streamlit as st

        from tabs.tab_ideas import _use_v2_image_flow

        st.session_state["ideas_prompt_version"] = ""
        assert _use_v2_image_flow() is False


class TestClearStaleMediaState:
    def test_clears_widget_selection_keys_too(self, monkeypatch):
        # 이전 아이디어 세트에서 고른 이미지 스타일/영상 길이·해상도가
        # 다음 세트로 새어 들어가면 안 된다.
        fake_state = {
            "generated_image_0": b"jpg-bytes",
            "generated_video_0": b"mp4-bytes",
            "queued_0": True,
            "img_style_0": "comic",
            "vid_dur_0": 10,
            "vid_res_0": "1080p",
            "keywords_input": "should survive",
        }
        monkeypatch.setattr(st, "session_state", fake_state)

        _clear_stale_media_state()

        assert fake_state == {"keywords_input": "should survive"}
