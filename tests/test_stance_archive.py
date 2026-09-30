import json

import stance_archive
from grok_client import GrokClient
from style_lint import lint


def _archive(tmp_path, monkeypatch, rows, generated=()):
    path = tmp_path / "my_posts.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", path)
    gen = tmp_path / "ideas_history.jsonl"
    gen.write_text("\n".join(json.dumps({"result": {"content": g}}, ensure_ascii=False) for g in generated), encoding="utf-8")
    monkeypatch.setattr(stance_archive, "GENERATED_PATHS", (gen,))


def test_related_posts_strip_mentions_and_rank_by_topic(tmp_path, monkeypatch):
    _archive(tmp_path, monkeypatch, [
        {"text": "@someone 테슬라를 알아줄 날이 곧 오겠죠? 🥲"},
        {"text": "오늘 점심은 김치찌개였어요"},
    ])
    found = stance_archive.related_posts("테슬라는 언제 오를까", stance_archive.load_posts())
    assert found == ["테슬라를 알아줄 날이 곧 오겠죠? 🥲"]


def test_load_posts_drops_polished_and_tool_generated(tmp_path, monkeypatch):
    tool_post = "상대가 테슬라를 탄다는 걸 이미 안다. 그래도 전기차 이야기를 시작할 때 그 이름은 빼고"
    _archive(tmp_path, monkeypatch, [
        {"text": "테슬라 주가는 결국 오른다. 사람들은 늘 늦게 안다. 그게 시장이다."},
        {"text": tool_post},
        {"text": "테슬라 주주들을 부러워 할 날이 올겁니다. 🥹"},
    ], generated=[tool_post + " 한참 돌고 나서야 내가 묻는다."])
    assert stance_archive.load_posts() == ["테슬라 주주들을 부러워 할 날이 올겁니다. 🥹"]


def test_missing_archive_gives_empty_block(tmp_path, monkeypatch):
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", tmp_path / "none.json")
    assert stance_archive.build_stance_block("테슬라") == ""


def test_write_from_memo_injects_stance_block(tmp_path, monkeypatch):
    _archive(tmp_path, monkeypatch, [{"text": "테슬라를 알아줄 날이 곧 오겠죠? 🥲"}])

    class Capture:
        def generate_json(self, system, user, **kw):
            self.system = system
            return {"posts": [{"content": "언제 오르냐 테슬라.."}]}

    provider = Capture()
    GrokClient(provider=provider).write_from_memo("테슬라는 언제 오를까", language="ko")
    assert "전에 한 말" in provider.system
    assert "테슬라를 알아줄 날이 곧 오겠죠?" in provider.system
    assert "답을 정해 주지 않는다" in provider.system


def test_self_typing_lint():
    text = "나는 실적으로 찍혀야 오른다는 쪽이네요😅 숫자가 찍힌 다음에 보는 편입니다."
    assert "자기 성향 요약" in lint(text, allow_polite=True).s2_hits
    assert "자기 성향 요약" not in lint("편의점 들렀다 가는 편이 빨라요", allow_polite=True).s2_hits


def test_memo_badges_skip_s2_rules_the_owner_also_trips(tmp_path, monkeypatch):
    import voice_card

    card = tmp_path / "voice_card.json"
    own = "정직원 도전중입니다.\n\n2.9M 필요해요.\n\n팔로워 늘었어요.\n\n반등은 있을까요!?"
    card.write_text(json.dumps({"examples": [own], "analysis": ""}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(voice_card, "VOICE_CARD_PATH", card)
    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", tmp_path / "none.json")
    assert "짧은 문장 4연속" in lint(own, allow_polite=True).s2_hits

    class Fake:
        def generate_json(self, system, user, **kw):
            return {"posts": [{"content": "언제 오를까요.\n\n실적일까요.\n\n기다려요.\n\n진짜로요."}]}

    result = GrokClient(provider=Fake()).write_from_memo("테슬라", language="ko")
    assert "짧은 문장 4연속" not in result["posts"][0]["_lint"]["s2"]


def test_memo_uses_low_reasoning_effort_on_grok_only_for_that_call(tmp_path, monkeypatch):
    from providers.grok_cli import GrokCliProvider

    monkeypatch.setattr(stance_archive, "ARCHIVE_PATH", tmp_path / "none.json")
    provider = GrokCliProvider()
    seen = []

    def fake_run(cmd, *, timeout):
        seen.append(cmd)
        return 0, '{"posts": [{"content": "언제 오르나.."}]}', ""

    monkeypatch.setattr(provider, "_run", fake_run)
    GrokClient(provider=provider).write_from_memo("테슬라", language="ko")
    assert seen[0][-2:] == ["--effort", "low"]
    assert provider.reasoning_effort is None
    assert "--effort" not in provider._json_command("s", "u")
