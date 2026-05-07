"""收藏：仅本人已完成识别（有 analyze_results）的 content。"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.app.api.v1.analyze import HistoryItemOut, HistoryListOut, _history_row_to_item
from backend.app.core.deps import require_permission
from backend.app.db.session import get_db
from backend.app.models.orm import Content, ContentFavorite, User

router = APIRouter(prefix="/favorites", tags=["favorites"])


class FavoriteAddBody(BaseModel):
    content_id: str = Field(..., description="与历史接口一致的 public_id")


class FavoriteAddOut(BaseModel):
    ok: bool
    already: bool = False


class FavoriteDeleteOut(BaseModel):
    ok: bool
    removed: bool


class FavoriteCheckOut(BaseModel):
    favorited: bool


@router.post("", response_model=FavoriteAddOut)
def add_favorite(
    body: FavoriteAddBody,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> FavoriteAddOut:
    content = (
        db.query(Content)
        .options(joinedload(Content.result))
        .filter(Content.public_id == body.content_id, Content.owner_id == user.id)
        .first()
    )
    if content is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    if content.result is None or not content.result.payload:
        raise HTTPException(status_code=400, detail="仅支持已完成的识别记录")
    existing = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user.id, ContentFavorite.content_id == content.id)
        .first()
    )
    if existing is not None:
        return FavoriteAddOut(ok=True, already=True)
    db.add(ContentFavorite(user_id=user.id, content_id=content.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return FavoriteAddOut(ok=True, already=True)
    return FavoriteAddOut(ok=True, already=False)


@router.delete("/{public_id}", response_model=FavoriteDeleteOut)
def remove_favorite(
    public_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> FavoriteDeleteOut:
    content = (
        db.query(Content).filter(Content.public_id == public_id, Content.owner_id == user.id).first()
    )
    if content is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    fav = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user.id, ContentFavorite.content_id == content.id)
        .first()
    )
    if fav is None:
        return FavoriteDeleteOut(ok=True, removed=False)
    db.delete(fav)
    db.commit()
    return FavoriteDeleteOut(ok=True, removed=True)


@router.get("", response_model=HistoryListOut)
def list_favorites(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
    page: int = 1,
    page_size: int = 20,
) -> HistoryListOut:
    q = (
        db.query(Content)
        .join(ContentFavorite, ContentFavorite.content_id == Content.id)
        .filter(ContentFavorite.user_id == user.id)
        .options(joinedload(Content.result))
        .order_by(ContentFavorite.created_at.desc())
    )
    rows = q.all()
    items_raw: list[HistoryItemOut] = []
    for row in rows:
        item = _history_row_to_item(row)
        if item is not None:
            items_raw.append(item)
    total = len(items_raw)
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size
    return HistoryListOut(list=items_raw[start : start + page_size], total=total)


@router.get("/check/{public_id}", response_model=FavoriteCheckOut)
def check_favorite(
    public_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_permission("analyze:run"))],
) -> FavoriteCheckOut:
    row = db.query(Content).filter(Content.public_id == public_id, Content.owner_id == user.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    fav = (
        db.query(ContentFavorite)
        .filter(ContentFavorite.user_id == user.id, ContentFavorite.content_id == row.id)
        .first()
    )
    return FavoriteCheckOut(favorited=fav is not None)
