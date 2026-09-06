from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import RoleEnum


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    username: str
    full_name: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: RoleEnum
    full_name: str | None = None
    created_at: datetime
