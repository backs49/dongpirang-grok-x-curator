"""비밀번호 원문 없이 브라우저 재접속을 인증하는 서명 토큰.

Streamlit의 session_state는 WebSocket 세션에 귀속되므로 모바일 브라우저가
백그라운드에서 연결을 끊으면 사라진다. 이 모듈은 서버 로컬의 난수 서명키로
검증 가능한, 만료 시간을 가진 불투명 토큰만 쿠키에 저장한다.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from pathlib import Path


ACCESS_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60
AUTH_SECRET_PATH = Path("content_queue/access_auth_secret")
_TOKEN_VERSION = "v1"
_MIN_SECRET_BYTES = 32


def load_or_create_signing_secret(path: Path = AUTH_SECRET_PATH) -> bytes:
    """재시작 뒤에도 유지되는 서버 전용 서명키를 소유자 읽기/쓰기 권한으로 둔다."""
    path = Path(path)
    try:
        existing = path.read_bytes()
    except OSError:
        existing = b""
    if len(existing) >= _MIN_SECRET_BYTES:
        os.chmod(path, 0o600)
        return existing

    path.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_bytes(_MIN_SECRET_BYTES)
    try:
        file_descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        # 동시에 두 요청이 처음 들어와도 먼저 만든 키를 그대로 사용한다.
        existing = path.read_bytes()
        if len(existing) >= _MIN_SECRET_BYTES:
            os.chmod(path, 0o600)
            return existing
        file_descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC)

    try:
        os.write(file_descriptor, secret)
    finally:
        os.close(file_descriptor)
    os.chmod(path, 0o600)
    return secret


def issue_access_token(secret: bytes, *, now: int, ttl_seconds: int = ACCESS_TOKEN_TTL_SECONDS) -> str:
    """만료 시각과 난수에 서버 서명을 붙인 쿠키용 토큰을 만든다."""
    if not isinstance(secret, bytes) or len(secret) < _MIN_SECRET_BYTES:
        raise ValueError("access token secret must be at least 32 bytes")
    expires_at = now + ttl_seconds
    nonce = secrets.token_urlsafe(24)
    payload = f"{_TOKEN_VERSION}.{expires_at}.{nonce}"
    signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def validate_access_token(token: object, secret: bytes, *, now: int) -> bool:
    """서명과 만료 시각을 모두 확인한다. 비밀번호와 비교하지 않는다."""
    if not isinstance(token, str) or not isinstance(secret, bytes):
        return False
    parts = token.split(".")
    if len(parts) != 4 or parts[0] != _TOKEN_VERSION:
        return False
    _, raw_expiry, nonce, supplied_signature = parts
    try:
        expires_at = int(raw_expiry)
    except ValueError:
        return False
    if expires_at <= now or not nonce or not supplied_signature:
        return False
    payload = f"{_TOKEN_VERSION}.{expires_at}.{nonce}"
    expected_signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(supplied_signature, expected_signature)
