"""Elasticsearch 检索（高亮 + 本人数据过滤）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.core.deps import get_current_user
from backend.app.models.orm import User
from backend.app.services.es_service import es_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search_contents(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
) -> dict:
    if not es_service.enabled:
        raise HTTPException(status_code=503, detail="Elasticsearch 未配置")
    try:
        return es_service.search_for_user(owner_id=user.id, q=q, page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
