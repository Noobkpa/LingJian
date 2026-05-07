"""slowapi 限流键：IP + Authorization。"""
from __future__ import annotations

import zlib

from fastapi import Request
from slowapi.util import get_remote_address


def rate_limit_key(request: Request) -> str:
    ip = get_remote_address(request)
    auth = request.headers.get("Authorization") or ""
    tag = zlib.adler32(auth.encode("utf-8", errors="ignore")) & 0xFFFFFFFF
    return f"{ip}:{tag:x}"
