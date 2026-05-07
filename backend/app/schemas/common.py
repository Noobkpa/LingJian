"""通用 API 模型：分页、统一错误体。"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiErrorBody(BaseModel):
    """标准错误响应（配合全局异常处理器）。"""

    code: str = Field(..., description="业务或错误码")
    message: str = Field(..., description="可读说明")
    detail: Any | None = Field(None, description="附加细节")
    request_id: str | None = Field(None, description="请求追踪 ID")


class PaginatedMeta(BaseModel):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=500)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    meta: PaginatedMeta


class MessageOk(BaseModel):
    ok: bool = True
    message: str = "success"
