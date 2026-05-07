"""应用层业务异常。"""
from __future__ import annotations


class AppException(Exception):
    """可映射为标准 JSON 的业务异常。"""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        detail: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "未认证或令牌无效") -> None:
        super().__init__("UNAUTHORIZED", message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "无权访问") -> None:
        super().__init__("FORBIDDEN", message, status_code=403)


class NotFoundError(AppException):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__("NOT_FOUND", message, status_code=404)
