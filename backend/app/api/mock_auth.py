"""Explicitly enabled local demo accounts; never used in deployed auth."""

from datetime import datetime, timedelta, timezone
from hmac import compare_digest

import jwt
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/auth/mock")

ACCOUNTS = {
    "consumer@example.com": ("demo-consumer", "consumer", "CON-DEMO001", "Demo Consumer"),
    "merchant@example.com": ("demo-merchant", "merchant", "MER-DEMO001", "Demo Merchant"),
}
PASSWORD = "DemoPass123!"


def _secret() -> str:
    settings = get_settings()
    if settings.environment != "dev" or settings.auth_provider != "token" or not settings.mock_auth_secret:
        raise HTTPException(status_code=404, detail="Mock login is disabled")
    return settings.mock_auth_secret


@router.post("/lookup")
def lookup(payload: dict[str, object]) -> dict[str, str]:
    _secret()
    custom_id = str(payload.get("customId") or "").strip().upper()
    user_type = str(payload.get("userType") or "").strip().lower()
    for email, (subject, role, account_id, name) in ACCOUNTS.items():
        if compare_digest(custom_id, account_id) and user_type == role:
            return {"userId": subject, "username": email, "email": email, "fullName": name,
                    "userType": role, "customId": account_id}
    raise HTTPException(status_code=404, detail="Demo account not found")


@router.post("/login")
def login(payload: dict[str, object]) -> dict[str, object]:
    secret = _secret()
    username = str(payload.get("username") or "").strip().lower()
    password = str(payload.get("password") or "")
    account = ACCOUNTS.get(username)
    if not account or not compare_digest(password, PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid demo credentials")
    subject, role, account_id, name = account
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": subject, "role": role, "email": username, "name": name,
                        "iat": now, "exp": now + timedelta(hours=12), "iss": "safebill-local-demo"}, secret, algorithm="HS256")
    return {"accessToken": token, "idToken": token, "expiresIn": 43200,
            "user": {"userId": subject, "userType": role, "email": username,
                     "loginId": username, "customId": account_id, "name": name}}
