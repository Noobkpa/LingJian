"""角色列表（管理）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, require_permission
from backend.app.models.orm import Role, User

router = APIRouter(prefix="/roles", tags=["roles"])


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[RoleOut])
def list_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("admin:stats"))],
) -> list[Role]:
    return db.query(Role).order_by(Role.id.asc()).all()
