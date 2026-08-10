"""이미지 스타일 모드 테스트."""

from __future__ import annotations

import image_modes as im


class TestModeCatalog:
    def test_seven_styles_defined(self):
        assert len(im.IMAGE_MODES) == 7
        assert "mascot" in im.IMAGE_MODES
        assert set(im.SUGGESTABLE) == set(im.IMAGE_MODES) - {"mascot"}

    def test_style_options_start_with_auto(self):
        opts = im.style_options()
        assert opts[0] == im.AUTO
        assert len(opts) == 8  # auto + 7 styles

    def test_every_style_has_label_and_block(self):
        for key, mode in im.IMAGE_MODES.items():
            assert mode["label"], key
            assert "STYLE" in mode["style_block"], key


class TestBuildImagePrompt:
    def test_common_rules_in_every_mode(self):
        for key in im.IMAGE_MODES:
            prompt = im.build_image_prompt("a cat typing on a laptop", key)
            assert "3:4" in prompt
            assert "no readable text" in prompt.lower() or "Do not include readable text" in prompt
            assert "a cat typing on a laptop" in prompt

    def test_no_45_ratio_anywhere(self):
        for key in im.IMAGE_MODES:
            assert "4:5" not in im.build_image_prompt("scene", key)

    def test_mascot_block_keeps_character_spec(self):
        prompt = im.build_image_prompt("scene", "mascot")
        assert "brown tabby cat" in prompt
        assert "MASCOT" in prompt

    def test_editorial_has_anti_slop_language(self):
        prompt = im.build_image_prompt("scene", "editorial")
        assert "film grain" in prompt
        assert "off-center" in prompt

    def test_post_body_is_not_embedded(self):
        # 장면 브리프만 받는 시그니처 — 포스트 원문이 끼어들 자리가 없다
        prompt = im.build_image_prompt("lone analyst at glowing monitors", "cinematic")
        assert "Post context" not in prompt


class TestResolveAutoStyle:
    def test_valid_suggestion_used(self):
        assert im.resolve_auto_style("comic", 0) == "comic"

    def test_mascot_suggestion_rejected(self):
        # LLM 이 mascot 을 제안해도 자동 모드에선 순환 배정으로 대체
        assert im.resolve_auto_style("mascot", 0) == im.SUGGESTABLE[0]

    def test_invalid_suggestion_rotates_by_index(self):
        assert im.resolve_auto_style(None, 0) == im.SUGGESTABLE[0]
        assert im.resolve_auto_style("nonsense", 2) == im.SUGGESTABLE[2]
        assert im.resolve_auto_style(None, 6) == im.SUGGESTABLE[0]
