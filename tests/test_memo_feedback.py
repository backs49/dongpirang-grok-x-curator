import memo_feedback


def _job():
    return {
        "id": "j1", "engine": "Claude CLI", "request": {"memo": "테슬라 언제 오르나"},
        "result": {"posts": [{"content": "테슬라 언제 오르나요..ㅠ"}, {"content": "실적 나와야 오르려나 ㅋ"}]},
    }


def test_record_and_summarize(tmp_path):
    path = tmp_path / "fb.jsonl"
    rec = memo_feedback.record_publish(_job(), 1, "실적 나와야 오르려나 ㅋㅋ 존버", path=path)
    assert rec["chosen"] == "실적 나와야 오르려나 ㅋ"
    assert rec["memo"] == "테슬라 언제 오르나"
    memo_feedback.record_publish(_job(), 0, "테슬라 언제 오르나요..ㅠ", path=path)

    summary = memo_feedback.summarize(memo_feedback.load_records(path))
    assert summary["count"] == 2
    assert summary["chosen_index"] == {1: 1, 0: 1}
    assert summary["unedited_ratio"] == 0.5
    assert any("존버" in phrase for phrase, _ in summary["often_added"])


def test_invalid_choice_records_nothing(tmp_path):
    path = tmp_path / "fb.jsonl"
    assert memo_feedback.record_publish(_job(), 5, "x", path=path) is None
    assert not path.exists()


def test_finish_memo_records_published_draft(tmp_path, monkeypatch):
    import content_queue
    from workspace_ui import create, editor, job_view

    queue = tmp_path / "queue.json"
    data = content_queue.empty_queue()
    data["drafts"].append({"id": "d1", "text": "실적 나와야 오르려나 ㅋㅋ", "status": "published", "source_job_id": "j1-1"})
    content_queue.save_queue(queue, data)
    monkeypatch.setattr(editor, "QUEUE_PATH", queue)
    monkeypatch.setattr(job_view, "load_job", lambda job_id, **kw: _job() if job_id == "j1" else None)
    fb = tmp_path / "fb.jsonl"
    monkeypatch.setattr(memo_feedback, "FEEDBACK_PATH", fb)

    store = {"active_memo_job_id": "j1", "memo_choice": 1}
    create._finish_memo(store, lambda: None)

    records = memo_feedback.load_records(fb)
    assert records[0]["final"] == "실적 나와야 오르려나 ㅋㅋ"
    assert store["active_memo_job_id"] is None
