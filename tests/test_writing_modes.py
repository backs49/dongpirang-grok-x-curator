"""글쓰기 모드 카드 테스트."""

from __future__ import annotations

import writing_modes as wm


class TestModeCards:
    def test_twelve_modes_defined(self):
        assert len(wm.WRITING_MODES) == 12
        assert set(wm.TONE_ROTATION) <= set(wm.WRITING_MODES)

    def test_every_card_complete(self):
        for key, card in wm.WRITING_MODES.items():
            assert card["label"], key
            assert card["category"] in ("tone", "author"), key
            assert card["rules"].strip(), key
            assert len(card["examples"]) >= 2, key
            assert isinstance(card["allow_polite"], bool), key

    def test_mode_options_order(self):
        opts = wm.mode_options()
        assert opts[0] == wm.AUTO_MIX
        assert len(opts) == 13  # auto_mix + 12 modes

    def test_auto_mix_replaces_satire_with_builder_note(self):
        assert wm.TONE_ROTATION == ("serious", "humor", "story", "hook", "builder_note")
        block = wm.build_mode_block(wm.AUTO_MIX)
        assert "빌더 노트" in block
        assert "풍자" not in block

    def test_lab_modes_are_selectable_but_not_automatic(self):
        assert wm.experimental_mode_options() == ("satire", "haoche", "hankang")
        assert "hankang" in wm.mode_options()
        assert set(wm.experimental_mode_options()).isdisjoint(wm.TONE_ROTATION)

    def test_builder_and_hankang_cards_are_complete(self):
        for key in ("builder_note", "hankang"):
            assert len(wm.WRITING_MODES[key]["examples"]) >= 2
            assert wm.WRITING_MODES[key]["rules"].strip()

    def test_label_roundtrip(self):
        for key in wm.WRITING_MODES:
            assert wm.label_to_key(wm.mode_label(key)) == key
        assert wm.label_to_key("없는 라벨") == ""

    def test_label_to_key_tolerates_brackets_and_whitespace(self):
        # 자동 믹스 배정표는 "[진지/분석]" 처럼 대괄호로 라벨을 렌더링하고
        # LLM 이 mode 필드에 대괄호를 그대로 에코하는 경우가 있다.
        assert wm.label_to_key("[진지/분석]") == "serious"
        assert wm.label_to_key(" 유머 ") == "humor"

    def test_polite_modes(self):
        assert wm.allow_polite("chimchakman") is True
        assert wm.allow_polite("haoche") is True
        assert wm.allow_polite("serious") is False
        assert wm.allow_polite(wm.AUTO_MIX) is False

    def test_pillar_mapping(self):
        assert wm.pillar_for_mode("serious") == "tip"
        assert wm.pillar_for_mode("hook") == "tip"
        assert wm.pillar_for_mode("story") == "retrospective"
        assert wm.pillar_for_mode("humor") == "curation"
        assert wm.pillar_for_mode("kimhoon") == "curation"
        assert wm.pillar_for_mode("") == "curation"


class TestModeBlock:
    def test_auto_mix_block_assigns_five(self):
        block = wm.build_mode_block(wm.AUTO_MIX)
        for i in range(1, 6):
            assert f"아이디어 {i}" in block
        for key in wm.TONE_ROTATION:
            assert wm.mode_label(key) in block

    def test_single_mode_block(self):
        block = wm.build_mode_block("kimhoon")
        assert wm.mode_label("kimhoon") in block
        assert "예시" in block
        # 다른 모드 카드는 포함되지 않는다
        assert wm.mode_label("humor") not in block

    def test_block_includes_examples(self):
        block = wm.build_mode_block("haruki")
        for ex in wm.WRITING_MODES["haruki"]["examples"]:
            assert ex in block
