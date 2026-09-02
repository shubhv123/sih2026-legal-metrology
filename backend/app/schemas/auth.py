"""Owned by: Aditya"""

from pydantic import BaseModel
from enum import Enum


class UserRole(str, Enum):
    INSPECTOR = "inspector"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str


class CurrentUser(BaseModel):
    username: str
    role: UserRole
