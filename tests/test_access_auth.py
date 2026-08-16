"""모바일 재접속에도 비밀번호 원문 없이 인증을 복원하는 토큰 테스트."""

from __future__ import annotations

import stat

from access_auth import (
    ACCESS_TOKEN_TTL_SECONDS,
    issue_access_token,
    load_or_create_signing_secret,
    validate_access_token,
)


def test_issued_token_is_valid_until_its_expiry():
    secret = b"a" * 32
    token = issue_access_token(secret, now=1_000)

    assert validate_access_token(token, secret, now=1_000 + ACCESS_TOKEN_TTL_SECONDS - 1)
    assert not validate_access_token(token, secret, now=1_000 + ACCESS_TOKEN_TTL_SECONDS)


def test_tampered_token_is_rejected():
    secret = b"a" * 32
    token = issue_access_token(secret, now=1_000)
    tampered = token.replace("v1.", "v2.", 1)

    assert not validate_access_token(tampered, secret, now=1_001)


def test_generated_signing_secret_persists_with_owner_only_permissions(tmp_path):
    path = tmp_path / "access_auth_secret"

    first = load_or_create_signing_secret(path)
    second = load_or_create_signing_secret(path)

    assert first == second
    assert len(first) >= 32
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
