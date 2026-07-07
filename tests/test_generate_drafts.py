"""야간 초안 생성 배치 (4b) 로직 테스트."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from content_queue import add_draft, add_material, empty_queue, load_queue, save_queue

_spec = importlib.util.spec_from_file_location(
    "generate_drafts", Path(__file__).parent.parent / "scripts" / "generate_drafts.py"
)
generate_drafts = importlib.util.module_from_spec(_spec)
sys.modules["generate_drafts"] = generate_drafts
_spec.loader.exec_module(generate_drafts)


class _FakeGrok:
    def __init__(self):
        self.material_calls = []
        self.idea_calls = []

    def draft_from_material(self, text):
        self.material_calls.append(text)
        return {
            "post": f"[초안] {text}",
            "pillar": "build_in_public",
            "image_prompt": "desk, no text",
        }

    def generate_ideas(self, keywords, length=0):
        self.idea_calls.append(keywords)
        return {
            "ideas": [
                {"title": "팁", "content": "팁 포스트 본문", "image_prompt": "tips, no text"},
            ]
        }


def _run(tmp_path, data, grok=None):
    path = tmp_path / "queue.json"
    save_queue(path, data)
    grok = grok or _FakeGrok()
    summary = generate_drafts.run(grok=grok, queue_path=path)
    return summary, load_queue(path), grok


class TestGenerateDrafts:
    def test_materials_become_drafts(self, tmp_path):
        data = empty_queue()
        add_material(data, "소재 A")
        add_material(data, "소재 B")

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 2
        assert len(saved["drafts"]) == 2
        assert all(d["status"] == "draft" for d in saved["drafts"])
        # 소재는 사용 처리됨
        assert all(m["used"] for m in saved["materials"])

    def test_materials_capped_per_night(self, tmp_path):
        data = empty_queue()
        for i in range(5):
            add_material(data, f"소재 {i}")

        summary, saved, _ = _run(tmp_path, data)

        assert summary["from_materials"] == generate_drafts.MAX_MATERIALS_PER_NIGHT
        unused = [m for m in saved["materials"] if not m["used"]]
        assert len(unused) == 5 - generate_drafts.MAX_MATERIALS_PER_NIGHT

    def test_tip_fallback_when_no_materials_and_low_stock(self, tmp_path):
        data = empty_queue()

        summary, saved, grok = _run(tmp_path, data)

        assert summary["from_materials"] == 0
        assert summary["tip_drafts"] == 1
        assert saved["drafts"][0]["pillar"] == "tip"
        assert grok.idea_calls  # generate_ideas 사용

    def test_skips_entirely_when_stock_sufficient(self, tmp_path):
        data = empty_queue()
        for i in range(generate_drafts.STOCK_TARGET):
            add_draft(data, text=f"재고 {i}", pillar="tip")
        add_material(data, "소재")  # 소재가 있어도 재고 충분하면 스킵

        summary, saved, grok = _run(tmp_path, data)

        assert summary == {"from_materials": 0, "tip_drafts": 0, "skipped": True}
        assert not grok.material_calls
        # 소재는 소모되지 않고 남는다
        assert not saved["materials"][0]["used"]

    def test_generation_error_leaves_material_unused(self, tmp_path):
        class _ErrorGrok(_FakeGrok):
            def draft_from_material(self, text):
                return {"error": "engine down"}

        data = empty_queue()
        add_material(data, "소재 A")

        summary, saved, _ = _run(tmp_path, data, grok=_ErrorGrok())

        assert summary["from_materials"] == 0
        assert saved["drafts"] == []
        assert not saved["materials"][0]["used"]

    def test_custom_tip_keywords_from_settings(self, tmp_path):
        data = empty_queue()
        data["settings"] = {"tip_keywords": "고양이 만화, 통영 여행"}

        _, _, grok = _run(tmp_path, data)

        assert grok.idea_calls == ["고양이 만화, 통영 여행"]
