"""
Owner: ADITYA

TODO(aditya):
 1. Replace hardcoded users with a real (tiny) users table -
    2 rows is fine for the demo: one inspector, one admin.
 2. Use core/security.py for password hashing (passlib) and JWT
    creation - don't store plaintext passwords even for a demo.
 3. Add a get_current_user dependency (reads JWT from Authorization
    header) that other routers can use to gate access by role.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.auth import LoginRequest, LoginResponse, UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# TEMPORARY - replace with real DB-backed auth
_MOCK_USERS = {
    "inspector1": {"password": "demo123", "role": UserRole.INSPECTOR},
    "admin1": {"password": "demo123", "role": UserRole.ADMIN},
}


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    user = _MOCK_USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO(aditya): issue a real JWT instead of this placeholder string
    fake_token = f"demo-token-{payload.username}"

    return LoginResponse(
        access_token=fake_token,
        role=user["role"],
        username=payload.username,
    )
