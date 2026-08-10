"""보이스 카드 저장/로드 테스트."""

from __future__ import annotations

import voice_card


def _patch_path(monkeypatch, tmp_path):
    path = tmp_path / "voice_card.json"
    monkeypatch.setattr(voice_card, "VOICE_CARD_PATH", path)
    return path


class TestRoundtrip:
    def test_save_and_load(self, monkeypatch, tmp_path):
        _patch_path(monkeypatch, tmp_path)
        voice_card.save_voice_card(["포스트 하나.", "포스트 둘."], analysis="담백한 평어체")
        card = voice_card.load_voice_card()
        assert card["examples"] == ["포스트 하나.", "포스트 둘."]
        assert card["analysis"] == "담백한 평어체"
        assert card["updated_at"]

    def test_load_missing_file(self, monkeypatch, tmp_path):
        _patch_path(monkeypatch, tmp_path)
        card = voice_card.load_voice_card()
        assert card == {"examples": [], "analysis": "", "updated_at": ""}

    def test_load_corrupt_file(self, monkeypatch, tmp_path):
        path = _patch_path(monkeypatch, tmp_path)
        path.write_text("not json", encoding="utf-8")
        card = voice_card.load_voice_card()
        assert card["examples"] == []

    def test_mutating_returned_list_does_not_pollute_state(self, monkeypatch, tmp_path):
        """회귀 테스트: 반환된 리스트를 변경해도 다음 호출은 여전히 빈 카드를 반환해야 한다."""
        _patch_path(monkeypatch, tmp_path)
        card1 = voice_card.load_voice_card()
        card1["examples"].append("leaked data")
        card2 = voice_card.load_voice_card()
        assert card2["examples"] == []


class TestSplitExamples:
    def test_split_on_dashes_and_blank_lines(self):
        raw = "첫 포스트.\n둘째 줄까지.\n---\n두 번째 포스트.\n\n\n세 번째 포스트."
        assert voice_card.split_examples(raw) == [
            "첫 포스트.\n둘째 줄까지.",
            "두 번째 포스트.",
            "세 번째 포스트.",
        ]

    def test_empty_input(self):
        assert voice_card.split_examples("   \n\n ") == []


class TestVoiceBlock:
    def test_empty_card_returns_empty_block(self, monkeypatch, tmp_path):
        _patch_path(monkeypatch, tmp_path)
        assert voice_card.build_voice_block() == ""

    def test_block_contains_examples_and_analysis(self, monkeypatch, tmp_path):
        _patch_path(monkeypatch, tmp_path)
        voice_card.save_voice_card(["예시 A", "예시 B", "예시 C", "예시 D"], analysis="분석 텍스트")
        block = voice_card.build_voice_block(max_examples=3)
        assert "분석 텍스트" in block
        assert "예시 A" in block and "예시 C" in block
        assert "예시 D" not in block  # max_examples 초과분 제외
