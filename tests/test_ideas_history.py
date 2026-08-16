"""아이디어 생성 이력 영속화 테스트."""

from __future__ import annotations

import json

import ideas_history


def _patch_path(monkeypatch, tmp_path):
    path = tmp_path / "ideas_history.jsonl"
    monkeypatch.setattr(ideas_history, "HISTORY_PATH", path)
    return path


def test_append_and_load_roundtrip(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    result = {"ideas": [{"title": "t1", "content": "c1"}]}

    ideas_history.append_history("AI 사이드프로젝트", 300, result)
    ideas_history.append_history("출퇴근", 0, {"ideas": []})

    entries = ideas_history.load_history()
    assert len(entries) == 2
    # 최신순
    assert entries[0]["keywords"] == "출퇴근"
    assert entries[1]["keywords"] == "AI 사이드프로젝트"
    assert entries[1]["length"] == 300
    assert entries[1]["result"] == result
    assert entries[0]["at"]


def test_load_skips_corrupt_lines(monkeypatch, tmp_path):
    path = _patch_path(monkeypatch, tmp_path)
    good = {"at": "2026-07-19", "keywords": "k", "length": 0, "result": {"ideas": []}}
    path.write_text(
        "not json\n"
        + json.dumps(good, ensure_ascii=False)
        + "\n"
        + json.dumps({"result": "not-a-dict"})
        + "\n",
        encoding="utf-8",
    )
    entries = ideas_history.load_history()
    assert len(entries) == 1
    assert entries[0]["keywords"] == "k"


def test_load_empty_when_no_file(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    assert ideas_history.load_history() == []


def test_append_stores_mode_engine_version(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    ideas_history.append_history(
        "키워드", 0, {"ideas": []},
        mode="serious", engine="Grok CLI", prompt_version="2.0",
    )
    entry = ideas_history.load_history()[0]
    assert entry["mode"] == "serious"
    assert entry["engine"] == "Grok CLI"
    assert entry["prompt_version"] == "2.0"


def test_append_defaults_keep_backward_compat(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    ideas_history.append_history("키워드", 0, {"ideas": []})
    entry = ideas_history.load_history()[0]
    assert entry["mode"] == ""
    assert entry["engine"] == ""


def test_load_old_entries_without_new_fields(monkeypatch, tmp_path):
    path = _patch_path(monkeypatch, tmp_path)
    old = {"at": "2026-07-19", "keywords": "k", "length": 0, "result": {"ideas": []}}
    path.write_text(json.dumps(old, ensure_ascii=False) + "\n", encoding="utf-8")
    entries = ideas_history.load_history()
    assert len(entries) == 1
    assert entries[0].get("mode", "") == ""


def test_grounded_history_roundtrip_preserves_request_and_sources(monkeypatch, tmp_path):
    _patch_path(monkeypatch, tmp_path)
    result = {"ideas": [{"content": "본문", "sources": [{"url": "https://who.int/a"}]}]}

    ideas_history.append_history(
        "수면",
        280,
        result,
        content_type="grounded_tip",
        tip_category="health",
        references="WHO link",
    )

    entry = ideas_history.load_history()[0]
    assert (entry["content_type"], entry["tip_category"], entry["references"]) == (
        "grounded_tip",
        "health",
        "WHO link",
    )
    assert entry["result"] == result


def test_old_history_defaults_to_normal_ideas(monkeypatch, tmp_path):
    path = _patch_path(monkeypatch, tmp_path)
    old = {"at": "2026-07-19", "keywords": "k", "length": 0, "result": {"ideas": []}}
    path.write_text(json.dumps(old, ensure_ascii=False) + "\n", encoding="utf-8")

    entry = ideas_history.load_history()[0]
    assert entry["content_type"] == "ideas"
    assert entry["tip_category"] == ""
    assert entry["references"] == ""


def test_history_i18n_keys_cover_all_languages():
    from i18n import _T, LANGUAGES

    for key in ("hist_expander", "hist_empty", "hist_count_caption",
                "hist_restore_btn", "hist_edit_btn", "media_hist_expander",
                "media_hist_empty", "media_hist_count",
                "ideas_content_type_label", "ideas_content_type_ideas",
                "ideas_content_type_grounded_tip", "ideas_tip_category_label",
                "ideas_tip_category_daily", "ideas_tip_category_health",
                "ideas_tip_category_finance", "ideas_tip_category_it_builder",
                "ideas_references_label", "ideas_references_help",
                "ideas_grok_research_note", "ideas_health_finance_notice",
                "ideas_experimental_modes", "ideas_sources", "ideas_verified_at",
                "ideas_error_insufficient_sources", "ideas_error_unsafe_personalized_request",
                "ideas_error_unverified_evidence", "ideas_error_grounded_tips_require_grok_cli"):
        assert set(_T[key]) >= set(LANGUAGES), f"missing translations for {key}"
