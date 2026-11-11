from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import mock_auth
from app.core import security


def test_demo_login_token_is_scoped_and_rejects_bad_password(monkeypatch):
    settings = SimpleNamespace(environment="dev", auth_provider="token", mock_auth_secret="test-secret", auth_tokens={})
    monkeypatch.setattr(mock_auth, "get_settings", lambda: settings)
    monkeypatch.setattr(security, "get_settings", lambda: settings)

    token = mock_auth.login({"username": "merchant@example.com", "password": "DemoPass123!"})["accessToken"]
    principal = security.get_current_principal(authorization=f"Bearer {token}")
    assert (principal.role, principal.subject) == ("merchant", "demo-merchant")

    with pytest.raises(HTTPException) as wrong:
        mock_auth.login({"username": "merchant@example.com", "password": "wrong"})
    assert wrong.value.status_code == 401

    settings.environment = "production"
    with pytest.raises(HTTPException) as disabled:
        mock_auth.login({"username": "merchant@example.com", "password": "DemoPass123!"})
    assert disabled.value.status_code == 404
