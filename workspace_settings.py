"""NiceGUI 서명 쿠키용 스토리지 시크릿 — 서버에만 남는다.

이 파일은 자격 증명 저장소가 아니다. 브라우저 세션을 서버 측 사용자
스토리지에 묶어 주는 서명 키 하나만 다루며, .env 나 API 키에는 손대지
않는다. 쓰기는 content_queue.save_queue 와 같은 방식(mkstemp + os.replace)
으로 원자적이라, 워커와 앱이 동시에 처음 부팅해도 반쯤 쓰인 시크릿을
읽는 일이 없다.
"""

from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path


SECRET_PATH = Path("content_queue/nicegui_storage_secret")

# secrets.token_urlsafe 는 바이트 수를 받는다. 32바이트 → 43자 URL-safe 문자열.
SECRET_BYTES = 32

# 소유자만 읽고 쓴다. 홈 디렉터리를 공유하는 다른 계정이 세션을 위조하지 못한다.
SECRET_MODE = 0o600


def load_or_create_storage_secret(path: Path | str = SECRET_PATH) -> str:
    """저장된 시크릿을 돌려주고, 없으면 하나 만들어 저장한 뒤 돌려준다."""
    path = Path(path)
    existing = _read_secret(path)
    if existing:
        return existing

    _write_secret(path, secrets.token_urlsafe(SECRET_BYTES))
    # 동시에 두 프로세스가 만들었다면 파일에 남은 쪽이 승자다. 다시 읽어
    # 승자의 값을 쓰면 두 프로세스가 같은 시크릿으로 수렴한다.
    stored = _read_secret(path)
    if not stored:
        raise OSError(f"storage secret could not be persisted at {path}")
    return stored


def _read_secret(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""


def _write_secret(path: Path, secret: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        os.fchmod(fd, SECRET_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(secret)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
