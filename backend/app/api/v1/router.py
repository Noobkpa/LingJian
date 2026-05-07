"""聚合 `/api/v1` 路由。"""
from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import (
    admin_content,
    admin_management,
    admin_stats,
    analyze,
    auth,
    content,
    exports,
    favorites,
    feedback,
    review,
    roles,
    search,
    tasks,
    users,
)

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(roles.router)
api_v1_router.include_router(analyze.router)
api_v1_router.include_router(favorites.router)
api_v1_router.include_router(feedback.router)
api_v1_router.include_router(content.router)
api_v1_router.include_router(tasks.router)
api_v1_router.include_router(admin_content.router)
api_v1_router.include_router(admin_management.router)
api_v1_router.include_router(admin_stats.router)
api_v1_router.include_router(review.router)
api_v1_router.include_router(search.router)
api_v1_router.include_router(exports.router)
