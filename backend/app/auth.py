from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .storage import DATA_PATH


USER_FILE = DATA_PATH / "users.json"
TOKEN_TTL = int(os.environ.get("AUTH_TOKEN_TTL", "28800"))  # 8 hours
TOKEN_SECRET = os.environ.get("AUTH_TOKEN_SECRET", "change-me-please")
VALID_ROLES = {"admin", "general"}
_bearer = HTTPBearer(auto_error=False)


def _load_users() -> Dict[str, Dict[str, Any]]:
    if not USER_FILE.exists():
        return {}
    try:
        with USER_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid users.json: {exc}") from exc
    users: Dict[str, Dict[str, Any]] = {}
    if isinstance(payload, dict):
        for email, password in payload.items():
            if not isinstance(password, str):
                continue
            users[email.lower()] = {"email": email, "password": password, "role": "admin"}
    elif isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            email = entry.get("email")
            password = entry.get("password_hash") or entry.get("password")
            role = entry.get("role") or entry.get("type") or "admin"
            if not email or not password:
                continue
            if role not in VALID_ROLES:
                role = "admin"
            users[email.lower()] = {"email": email, "password": password, "role": role}
    return users


def _save_users(users: Dict[str, Dict[str, Any]]) -> None:
    sorted_items = sorted(users.items(), key=lambda item: item[0])
    payload = [
        {"email": item[1]["email"], "password": item[1]["password"], "role": item[1].get("role", "admin")}
        for item in sorted_items
    ]
    USER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USER_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("sha256$"):
        try:
            _, salt, digest = stored.split("$", 2)
        except ValueError:
            return False
        calc = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(calc, digest)
    return hmac.compare_digest(stored, password)


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    email_key = (email or "").strip().lower()
    users = _load_users()
    user = users.get(email_key)
    if not user or not _verify_password(password or "", user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def _sign(payload: str) -> str:
    secret = TOKEN_SECRET.encode("utf-8")
    return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _encode_payload(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _decode_payload(token: str) -> Dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc


def generate_token(email: str) -> str:
    payload = {"email": email, "exp": int(time.time()) + TOKEN_TTL}
    encoded = _encode_payload(payload)
    signature = _sign(encoded)
    return f"{encoded}.{signature}"


def _validate_token(token: str) -> Dict[str, Any]:
    try:
        encoded, signature = token.rsplit(".", 1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    expected = _sign(encoded)
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    payload = _decode_payload(encoded)
    if payload.get("exp", 0) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)) -> Dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    payload = _validate_token(credentials.credentials)
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing email")
    users = _load_users()
    user = users.get(email.lower())
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return {"email": user["email"], "role": user.get("role", "admin")}


def _hash_password(password: str) -> str:
    salt = os.urandom(8).hex()
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def list_users() -> list[dict[str, str]]:
    users = _load_users()
    return [{"email": u["email"], "role": u.get("role", "admin")} for u in users.values()]


def create_user(email: str, password: str, role: str) -> dict[str, str]:
    email_key = (email or "").strip().lower()
    if not email_key or not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password are required")
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}"
        )
    users = _load_users()
    if email_key in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    users[email_key] = {"email": email, "password": _hash_password(password), "role": role}
    _save_users(users)
    return {"email": email, "role": role}


def delete_user(email: str) -> None:
    email_key = (email or "").strip().lower()
    users = _load_users()
    if email_key not in users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    users.pop(email_key)
    _save_users(users)
