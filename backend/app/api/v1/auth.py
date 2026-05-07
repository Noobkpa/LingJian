"""认证：注册、登录、刷新令牌。"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.orm import Role, User
from backend.app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])
oplog = logging.getLogger("operation")


@router.post("/register", response_model=TokenPair)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPair:
    if db.query(User).filter(User.username == payload.username).first():
        raise AppException("DUPLICATE", "用户名已存在", status_code=409)
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise AppException("DUPLICATE", "邮箱已注册", status_code=409)
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    role = db.query(Role).filter(Role.name == "user").first()
    if role is not None:
        user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    oplog.info("register user_id=%s username=%s", user.id, user.username)
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenPair)
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenPair:
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    rid = getattr(request.state, "request_id", "")
    oplog.info("login ok user_id=%s request_id=%s", user.id, rid)
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPair:
    try:
        body = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="refresh_token 无效")
    if body.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="令牌类型错误")
    sub = body.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="令牌无效")
    user = db.query(User).filter(User.id == int(sub)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不可用")
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )

