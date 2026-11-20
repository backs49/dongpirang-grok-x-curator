"""tab_publish_queue 순수 헬퍼 로직 테스트 (Streamlit 위젯 미실행).

publish_worker 가 도입한 "publishing"/"error" 상태가 큐 탭에서 사람 눈에
보이는지(9e663b8 리마인더 작업과 같은 조용한 실패 방지)를 검증한다.
"""

from __future__ import annotations

from content_queue import add_draft, empty_queue

from tabs.tab_publish_queue import (
    _STATUS_BADGE,
    _can_approve,
    _draft_for_material,
    _is_claim_locked,
    _visible_drafts,
)


def _queue_with_statuses(*statuses: str) -> dict:
    data = empty_queue()
    for status in statuses:
        d = add_draft(data, text=f"글 ({status})", pillar="tip")
        d["status"] = status
    return data


class TestVisibleDrafts:
    def test_includes_publishing_and_error(self):
        data = _queue_with_statuses("draft", "approved", "publishing", "error")
        visible = _visible_drafts(data)
        assert {d["status"] for d in visible} == {
            "draft",
            "approved",
            "publishing",
            "error",
        }

    def test_excludes_published_and_rejected(self):
        data = _queue_with_statuses("published", "rejected")
        assert _visible_drafts(data) == []


class TestStatusBadges:
    def test_publishing_and_error_have_badges(self):
        assert _STATUS_BADGE.get("publishing")
        assert _STATUS_BADGE.get("error")


class TestCanApprove:
    def test_draft_can_approve(self):
        assert _can_approve("draft") is True

    def test_error_can_approve_as_manual_retry(self):
        assert _can_approve("error") is True

    def test_publishing_cannot_approve(self):
        assert _can_approve("publishing") is False

    def test_approved_cannot_approve_again(self):
        assert _can_approve("approved") is False


class TestClaimLocked:
    def test_publishing_is_locked(self):
        assert _is_claim_locked("publishing") is True

    def test_other_statuses_not_locked(self):
        for status in ("draft", "approved", "error", "published", "rejected"):
            assert _is_claim_locked(status) is False


class _RoutingGrok:
    def __init__(self):
        self.calls = []

    def draft_from_material(self, text):
        self.calls.append(("material", text))
        return {"post": "소재 글", "pillar": "build_in_public", "image_prompt": ""}

    def draft_from_reply(self, text, parent=""):
        self.calls.append(("reply", text, parent))
        return {"post": "답글 글", "pillar": "curation", "image_prompt": ""}


class TestDraftRouting:
    """인박스의 '초안 만들기'도 밤 배치와 같은 경로를 탄다.

    답글 씨앗 소재를 draft_from_material 로 보내면 답글용 프롬프트
    (REPLY_SEED_SYSTEM_PROMPT)와 원글 맥락 없이 옛 소재 프롬프트로 써진다.
    """

    def test_reply_material_uses_reply_prompt_with_parent(self):
        grok = _RoutingGrok()
        material = {"id": "m1", "text": "답글", "origin": "reply", "parent_text": "원글"}

        result = _draft_for_material(grok, material)

        assert grok.calls == [("reply", "답글", "원글")]
        assert result["post"] == "답글 글"

    def test_reply_material_without_parent_text(self):
        grok = _RoutingGrok()

        _draft_for_material(grok, {"id": "m1", "text": "답글", "origin": "reply"})

        assert grok.calls == [("reply", "답글", "")]

    def test_plain_material_uses_material_prompt(self):
        grok = _RoutingGrok()

        _draft_for_material(grok, {"id": "m2", "text": "직접 넣은 소재"})

        assert grok.calls == [("material", "직접 넣은 소재")]
