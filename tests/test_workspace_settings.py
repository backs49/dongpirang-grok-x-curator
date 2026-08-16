"""워크스페이스 서버 경계 — 스토리지 시크릿과 로컬 전용 진입점."""

import string

import nicegui_app
from workspace_settings import SECRET_PATH, load_or_create_storage_secret


URL_SAFE = set(string.ascii_letters + string.digits + "-_")


def test_storage_secret_is_stable_and_owner_only(tmp_path):
    path = tmp_path / "nicegui_storage_secret"
    assert load_or_create_storage_secret(path) == load_or_create_storage_secret(path)
    assert path.stat().st_mode & 0o077 == 0


def test_storage_secret_is_url_safe_and_creates_its_directory(tmp_path):
    secret = load_or_create_storage_secret(tmp_path / "content_queue" / "secret")
    assert len(secret) >= 32
    assert set(secret) <= URL_SAFE


def test_storage_secret_never_touches_dotenv(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("XAI_API_KEY=super-secret\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    secret = load_or_create_storage_secret(tmp_path / "nicegui_storage_secret")

    assert env.read_text(encoding="utf-8") == "XAI_API_KEY=super-secret\n"
    assert "super-secret" not in secret
    # 임시 파일까지 정리되어 지정한 경로 외에는 아무것도 남기지 않는다.
    assert sorted(p.name for p in tmp_path.iterdir()) == [".env", "nicegui_storage_secret"]


def test_default_secret_location_lives_beside_the_json_stores():
    assert SECRET_PATH.parent.name == "content_queue"


def test_entry_point_is_import_safe_and_reads_the_port_from_the_environment(monkeypatch):
    # 이 모듈이 임포트된 것 자체가 "임포트만으로 서버가 뜨지 않는다"는 증거다.
    assert callable(nicegui_app.run)
    assert nicegui_app.DEFAULT_PORT == 8080

    monkeypatch.setenv("NICEGUI_PORT", "9001")
    assert nicegui_app.configured_port() == 9001
    monkeypatch.delenv("NICEGUI_PORT")
    assert nicegui_app.configured_port() == 8080


def test_entry_point_binds_localhost_only_without_reload(monkeypatch):
    captured = {}
    monkeypatch.setattr(nicegui_app.ui, "run", lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(nicegui_app, "load_or_create_storage_secret", lambda: "test-secret")

    nicegui_app.run(port=8123)

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8123
    assert captured["reload"] is False
    assert captured["storage_secret"] == "test-secret"
    assert captured["reconnect_timeout"] == 15.0
    assert captured["message_history_length"] == 1000
    assert captured["root"] is nicegui_app.build_workspace
