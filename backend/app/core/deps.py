"""FastAPI 依赖：数据库、当前用户、RBAC。"""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from backend.app.core.exceptions import ForbiddenError, UnauthorizedError
from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models.orm import Role, User

security_scheme = HTTPBearer(auto_error=False)


def _user_permission_codes(user: User) -> set[str]:
    codes: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            codes.add(perm.code)
    return codes


def get_current_user_optional(
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
) -> User | None:
    if creds is None or not creds.credentials:
        return None
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        return None
    if payload.get("typ") != "access":
        return None
    sub = payload.get("sub")
    if not sub:
        return None
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        return None
    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(Role.permissions))
        .filter(User.id == user_id)
        .first()
    )
    if user is None or not user.is_active:
        return None
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise UnauthorizedError()
    return user


def require_permission(code: str):
    def _checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if code not in _user_permission_codes(user):
            raise ForbiddenError(f"缺少权限：{code}")
        return user

    return _checker


def redis_dependency(request: Request):
    """从 app.state 取 Redis 客户端（可能为 None）。"""
    return getattr(request.app.state, "redis_client", None)
