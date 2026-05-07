"""全局异常处理。"""
from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException
from backend.app.schemas.common import ApiErrorBody

logger = logging.getLogger("backend.app.handlers")


def register_exception_handlers(app) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(request: Request, exc: AppException) -> JSONResponse:
        rid = getattr(request.state, "request_id", None)
        body = ApiErrorBody(
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            request_id=rid,
        )
        logger.info("AppException %s %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        rid = getattr(request.state, "request_id", None)
        body = ApiErrorBody(
            code="VALIDATION_ERROR",
            message="请求参数无效",
            detail=exc.errors(),
            request_id=rid,
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def _catch_all(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        rid = getattr(request.state, "request_id", None)
        logger.exception("未处理异常 request_id=%s", rid)
        body = ApiErrorBody(
            code="INTERNAL_ERROR",
            message="服务器内部错误",
            detail=str(exc) if settings.debug else None,
            request_id=rid,
        )
        return JSONResponse(status_code=500, content=body.model_dump())
