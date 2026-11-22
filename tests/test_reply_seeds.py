"""답글 씨앗 선별 테스트."""

from datetime import datetime, timezone

import grok_client
import reply_seeds
import stance_archive

NOW = datetime(2026, 10, 30, 23, 0, tzinfo=timezone.utc)


def _row(rid, text, *, created="2026-10-30T10:00:00.000Z", parent="9", impressions=10):
    row = {"id": rid, "text": text, "created_at": created,
           "public_metrics": {"impression_count": impressions}}
    if parent:
        row["referenced_tweets"] = [{"type": "replied_to", "id": parent}]
    return row


def _pick(rows, after_id=None, limit=2):
    return reply_seeds.pick_seeds(rows, after_id=after_id, now=NOW, limit=limit, generated="")


def test_picks_substantive_replies_and_strips_mentions():
    rows = [
        _row("10", "@yulmu 그나저나 엑스를 벗어나 주변을 둘러보면 AI는 아직도 초기 시장입니다 ㅋㅋ https://t.co/x"),
        _row("11", "@a 저 하늘 끝까지 🚀"),  # 너무 짧다
    ]
    seeds = _pick(rows)
    assert [s["reply_id"] for s in seeds] == ["10"]
    assert seeds[0]["text"] == "그나저나 엑스를 벗어나 주변을 둘러보면 AI는 아직도 초기 시장입니다 ㅋㅋ"
    assert seeds[0]["parent_id"] == "9"


def test_skips_social_private_originals_old_and_seen():
    rows = [
        _row("20", "@a 삼가 고인의 명복을 빕니다 마음이 너무 아픕니다 정말로"),
        _row("21", "@a 찰떡이가 오늘 처음으로 걸음마를 했는데 너무 신기하네요"),
        _row("22", "원글이라서 빠져야 하는 충분히 긴 문장입니다 정말로요", parent=None),
        _row("23", "@a 사흘보다 오래된 답글이라 식은 얘기라서 빠집니다 정말", created="2026-10-27T10:00:00.000Z"),
        _row("5", "@a 이미 본 답글이라 워터마크 뒤로 빠져야 하는 문장입니다"),
    ]
    assert _pick(rows, after_id="9") == []


def test_window_keeps_replies_up_to_three_days_old():
    # 2026-11-18 답글이 2일 창을 1.5시간 차로 놓친 뒤 3일로 늘렸다(D-011).
    rows = [
        _row("40", "@a 이틀 반 전에 단 답글인데 아직 식지 않은 얘기라서 남습니다", created="2026-10-28T11:00:00.000Z"),
        _row("41", "@a 사흘이 넘은 답글이라 이제는 식은 얘기라서 빠져야 합니다", created="2026-10-27T22:00:00.000Z"),
    ]
    assert [s["reply_id"] for s in _pick(rows)] == ["40"]


def test_ranks_by_length_and_impressions_with_limit():
    rows = [
        _row("30", "@a 회사에서 보여주니 다들 AI아니냐고 안믿네요ㅋㅋㅋ", impressions=5000),
        _row("31", "@a 현재까지 울트라 사용자 반응을 봐서는 뻥벤치인것 같네요 ㅎㅎ", impressions=1),
        _row("32", "@a 진짜 이런 소식은 왜 아무말이 없는지 이해가 어렵네요", impressions=1),
    ]
    assert [s["reply_id"] for s in _pick(rows, limit=2)] == ["30", "31"]


def test_newest_id():
    assert reply_seeds.newest_id([{"id": "9"}, {"id": "12"}, {"id": "x"}]) == "12"
    assert reply_seeds.newest_id([]) is None


class _Capture:
    def __init__(self, response):
        self.response = response
        self.system = self.user = ""

    def generate_json(self, system, user, **kw):
        self.system, self.user = system, user
        return self.response


def test_draft_from_reply_prompt_and_result(monkeypatch, tmp_path):
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", tmp_path / "none.json")
    cap = _Capture({"skip": False, "post": "엑스 밖은 아직 AI 초기 시장이더라고요 ㅋㅋ"})
    result = grok_client.GrokClient(provider=cap).draft_from_reply("AI는 아직도 초기 시장", "털린 사람 얘기")
    assert result == {"post": "엑스 밖은 아직 AI 초기 시장이더라고요 ㅋㅋ", "pillar": "curation", "image_prompt": ""}
    assert "답글" in cap.system and "skip" in cap.system
    assert "원글:\n털린 사람 얘기" in cap.user and "AI는 아직도 초기 시장" in cap.user


def test_draft_from_reply_skip_and_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", tmp_path / "none.json")
    skip = grok_client.GrokClient(provider=_Capture({"skip": True, "reason": "맞장구뿐"}))
    assert skip.draft_from_reply("좋네요 정말 좋네요") == {"skip": True, "reason": "맞장구뿐"}
    assert grok_client.GrokClient(provider=_Capture({})).draft_from_reply("x") == {"error": "empty post"}
    assert grok_client.GrokClient(provider=_Capture({})).draft_from_reply("  ") == {"error": "reply_required"}


def test_stance_block_excludes_the_reply_itself(monkeypatch, tmp_path):
    import json
    path = tmp_path / "posts.json"
    path.write_text(json.dumps([{"text": "@a 테슬라 로드스터 발표 기대하게 되네요"},
                                {"text": "테슬라 로드스터 또 미뤄지면 어쩌나"}], ensure_ascii=False))
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", path)
    monkeypatch.setattr(stance_archive, "GENERATED_PATHS", ())
    block = stance_archive.build_stance_block("테슬라 로드스터 발표 기대하게 되네요",
                                              exclude="테슬라 로드스터 발표 기대하게 되네요")
    assert "또 미뤄지면" in block and "발표 기대하게" not in block
