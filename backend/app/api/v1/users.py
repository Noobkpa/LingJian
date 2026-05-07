"""当前用户。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.core.deps import get_current_user, get_db, require_permission
from backend.app.core.security import hash_password, verify_password
from backend.app.models.orm import Content, ReviewStatus, User
from backend.app.schemas.auth import PasswordChangeBody, ReviewerProfileOut, UserPublic
from backend.app.services.reviewer_history import reviewer_history_list

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/review-history")
def me_review_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("review:read"))],
    page: int = 1,
    page_size: int = 20,
    audit_result: str | None = None,
) -> dict:
    """与 GET /review/history 相同数据；供网关只放行 /users/** 或旧版路由 404 时备用。"""
    return reviewer_history_list(
        db, user, page=page, page_size=page_size, audit_result=audit_result
    )


@router.get("/me/profile", response_model=ReviewerProfileOut)
def read_reviewer_profile(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> ReviewerProfileOut:
    """审核端个人中心：角色、累计审核量等。"""
    role_names = [r.name for r in current.roles]
    audit_count = (
        db.query(Content)
        .filter(Content.reviewer_id == current.id)
        .filter(
            or_(
                Content.review_status == ReviewStatus.approved.value,
                Content.review_status == ReviewStatus.rejected.value,
            )
        )
        .count()
    )
    jt = ""
    if current.created_at:
        jt = current.created_at.strftime("%Y-%m-%d %H:%M:%S")
    label = "、".join(role_names) if role_names else "用户"
    return ReviewerProfileOut(
        id=current.id,
        username=current.username,
        email=current.email,
        nickname=current.nickname,
        phone=current.phone,
        join_time=jt,
        roles=role_names,
        role_label=label,
        audit_count=audit_count,
        accuracy_display="100%",
    )


@router.get("/me", response_model=UserPublic)
def read_me(current: Annotated[User, Depends(get_current_user)]) -> UserPublic:
    return UserPublic.model_validate(current)


@router.post("/me/password")
def change_password(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    body: PasswordChangeBody,
) -> dict[str, bool]:
    if not verify_password(body.old_password, current.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
