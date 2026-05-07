"""用户反馈：匿名或带登录均可提交，写入 uploads/feedback/entries.jsonl。"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.app.core.deps import get_current_user_optional
from backend.app.models.orm import User
from backend.app.services.feedback_store import append_feedback

logger = logging.getLogger("backend.app.feedback")

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackBody(BaseModel):
    content_id: str | None = Field(default=None, max_length=80)
    message: str = Field(..., min_length=1, max_length=4000)


class FeedbackOut(BaseModel):
    ok: bool = True


@router.post("/", response_model=FeedbackOut)
def submit_feedback(
    request: Request,
    body: FeedbackBody,
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> FeedbackOut:
    msg = body.message.strip()
    if not msg:
        raise HTTPException(status_code=422, detail="反馈内容不能为空")
    fwd = request.headers.get("x-forwarded-for")
    client_ip = (fwd.split(",")[0].strip() if fwd else None) or (request.client.host if request.client else None)
    ua = request.headers.get("user-agent")

    extra: dict[str, object] | None = None
    if user is not None:
        name = getattr(user, "username", None) or getattr(user, "email", None)
        extra = {"user_id": user.id, "username": name}

    try:
        append_feedback(
            message=msg,
            content_id=body.content_id,
            client_ip=client_ip,
            user_agent=ua,
            extra=extra,
        )
    except OSError:
        logger.exception("feedback persist failed")
        raise HTTPException(status_code=503, detail="反馈暂无法保存，请稍后重试") from None

    return FeedbackOut(ok=True)
