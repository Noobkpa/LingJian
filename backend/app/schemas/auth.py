from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str = Field(..., min_length=8, max_length=80)
    captcha_code: str = Field(..., min_length=1, max_length=12)


class CaptchaResponse(BaseModel):
    captcha_id: str
    question: str
    image: str
    expires_in: int = 300


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    phone: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReviewerProfileOut(BaseModel):
    """审核端个人中心聚合信息。"""

    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    phone: str | None = None
    join_time: str = ""
    roles: list[str] = Field(default_factory=list)
    role_label: str = ""
    audit_count: int = 0
    accuracy_display: str = "100%"


class PasswordChangeBody(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)
