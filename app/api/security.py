from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional

from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from config import AppConfig


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
MIN_PASSWORD_LENGTH = 12


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_jwt_secret() -> str:
    # JWT_SECRET_KEY must be provided as an environment variable for production
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is required but not set. "
            "Set it on your server or in your deployment configuration."
        )
    return secret


@dataclass
class AuthUser:
    username: str
    password_hash: str
    created_at: str
    updated_at: str


class AuthStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or AppConfig.AUTH_USERS_FILE)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def authenticate(self, username: str, password: str, bcrypt) -> Optional[AuthUser]:
        record = self._read().get("users", {}).get(username)
        if not record:
            return None
        password_hash = record.get("password_hash")
        if not password_hash or not bcrypt.check_password_hash(password_hash, password):
            return None
        return AuthUser(
            username=username,
            password_hash=password_hash,
            created_at=record.get("created_at", utc_now()),
            updated_at=record.get("updated_at", utc_now()),
        )

    def add_user(self, username: str, password: str, bcrypt, force: bool = False) -> AuthUser:
        username = (username or "").strip()
        password = password or ""

        if not USERNAME_RE.match(username):
            raise ValueError("Username must be 3-64 chars and use letters, numbers, dot, underscore, or dash.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

        payload = self._read()
        users = payload.setdefault("users", {})
        existing = users.get(username)
        if existing and not force:
            raise ValueError("User already exists. Use --force to replace the stored hash.")

        now = utc_now()
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = {
            "username": username,
            "password_hash": password_hash,
            "created_at": existing.get("created_at", now) if existing else now,
            "updated_at": now,
        }
        users[username] = user
        self._write(payload)
        return AuthUser(**user)

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"schema": 1, "users": {}}
        with self.path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("auth store must contain a JSON object")
        data.setdefault("schema", 1)
        data.setdefault("users", {})
        return data

    def _write(self, payload: Dict[str, Any]) -> None:
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.flush()
            os.fsync(fh.fileno())
        tmp_path.replace(self.path)


def api_user_required(match_username: bool = True):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get("role") != "user":
                    return {"success": False, "error": "forbidden"}, 403

                current_username = get_jwt_identity()
                route_username = kwargs.get("username")
                if match_username and route_username and route_username != current_username:
                    return {"success": False, "error": "forbidden"}, 403

                if match_username and not route_username and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                    body = request.get_json(silent=True) or {}
                    body_username = body.get("username")
                    if body_username and body_username != current_username:
                        return {"success": False, "error": "forbidden"}, 403
            except Exception as exc:
                return {"success": False, "error": str(exc)}, 401

            return fn(*args, **kwargs)

        return wrapped

    return decorator