"""이미지 프롬프트 조립 + 구 API 제거 확인 (3:4 표준)."""

from __future__ import annotations

import image_client
from image_modes import build_image_prompt


class TestImagePromptAssembly:
    def test_scene_and_style_combined(self):
        result = build_image_prompt("A cozy desk scene", "comic")
        assert "A cozy desk scene" in result
        assert "webcomic" in result
        assert "3:4" in result

    def test_old_copy_prompt_removed(self):
        assert not hasattr(image_client, "build_copy_prompt")
        assert not hasattr(image_client, "_IMAGE_RULES")
        assert not hasattr(image_client, "_MASCOT_RULES")
