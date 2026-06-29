from __future__ import annotations

import secrets


def verify_bearer_token(authorization: str | None, expected_token: str) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization.removeprefix("Bearer ").strip()
    return secrets.compare_digest(token, expected_token)
