import base64
import binascii
import hashlib
import json
import time

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.schemas.enums import RoleEnum

SALT = "sih2026_lmpc_salt"


def hash_password(password: str) -> str:
    """Generate SHA-256 hash with salt for demo authentication."""
    return hashlib.sha256(f"{SALT}_{password}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return hash_password(plain_password) == hashed_password


def create_access_token(username: str, role: str, expires_in_seconds: int = 86400) -> str:
    """Lightweight self-contained token for demo auth (no external JWT dependency required)."""
    payload = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_bytes = json.dumps(payload).encode()
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode()
    signature = hashlib.sha256(f"{SALT}_{b64_payload}".encode()).hexdigest()[:16]
    return f"{b64_payload}.{signature}"


def decode_access_token(token: str) -> dict | None:
    """Validate token format and signature."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hashlib.sha256(f"{SALT}_{b64_payload}".encode()).hexdigest()[:16]
        if signature != expected_sig:
            return None
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode())
        payload = json.loads(payload_bytes.decode())
        if payload.get("exp", 0) < time.time():
            return None  # expired
        return payload
    except (json.JSONDecodeError, ValueError, KeyError, binascii.Error):
        return None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to retrieve current authenticated user.

    If no header is provided, defaults to demo 'inspector' account for smooth local dev/demo.
    """
    if not authorization or not authorization.startswith("Bearer "):
        # Demo fallback: return default inspector
        default_user = db.query(User).filter(User.role == "inspector").first()
        if default_user:
            return default_user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.replace("Bearer ", "").strip()
    payload = decode_access_token(token)
    if not payload:
        # Check legacy mock token prefix
        if "inspector" in token:
            user = db.query(User).filter(User.role == "inspector").first()
            if user:
                return user
        elif "admin" in token:
            user = db.query(User).filter(User.role == "admin").first()
            if user:
                return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(allowed_roles: list[RoleEnum]):
    """Role-based authorization dependency (Inspector vs Admin)."""

    def role_checker(user: User = Depends(get_current_user)) -> User:
        user_role = RoleEnum(user.role)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires role in {[r.value for r in allowed_roles]}",
            )
        return user

    return role_checker
