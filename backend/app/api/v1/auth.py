"""认证：注册、登录、刷新令牌。"""
from __future__ import annotations

import logging
import base64
from io import BytesIO
import random
import secrets
import string
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from backend.app.core.exceptions import AppException
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.orm import Role, User
from backend.app.schemas.auth import CaptchaResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])
oplog = logging.getLogger("operation")
CAPTCHA_TTL_SECONDS = 300
_captcha_memory: dict[str, tuple[str, float]] = {}
_captcha_alphabet = string.ascii_uppercase + string.digits
_captcha_ambiguous = str.maketrans("", "", "0O1I")
_captcha_chars = _captcha_alphabet.translate(_captcha_ambiguous)


def _captcha_key(captcha_id: str) -> str:
    return f"auth:captcha:{captcha_id}"


def _captcha_store(request: Request, captcha_id: str, answer: str) -> None:
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is not None:
        try:
            redis_client.setex(_captcha_key(captcha_id), CAPTCHA_TTL_SECONDS, answer)
            return
        except Exception:
            logging.getLogger(__name__).warning("Redis 验证码写入失败，退回内存缓存", exc_info=True)
    expires_at = time.time() + CAPTCHA_TTL_SECONDS
    _captcha_memory[captcha_id] = (answer, expires_at)


def _captcha_verify(request: Request, captcha_id: str, captcha_code: str) -> bool:
    cid = (captcha_id or "").strip()
    code = (captcha_code or "").strip().lower()
    if not cid or not code:
        return False

    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client is not None:
        try:
            key = _captcha_key(cid)
            answer = redis_client.get(key)
            if answer is not None:
                redis_client.delete(key)
                return secrets.compare_digest(str(answer).strip().lower(), code)
            return False
        except Exception:
            logging.getLogger(__name__).warning("Redis 验证码读取失败，退回内存缓存", exc_info=True)

    item = _captcha_memory.pop(cid, None)
    if not item:
        return False
    answer, expires_at = item
    if expires_at < time.time():
        return False
    return secrets.compare_digest(answer.lower(), code)


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for item in candidates:
        try:
            return ImageFont.truetype(item, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _captcha_image(code: str) -> str:
    width, height = 150, 48
    bg = (248, 252, 255)
    image = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(image)

    for _ in range(130):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = (
            random.randint(150, 215),
            random.randint(170, 225),
            random.randint(185, 235),
        )
        draw.point((x, y), fill=color)

    for _ in range(5):
        points = [
            (random.randint(-10, width // 3), random.randint(0, height)),
            (random.randint(width // 4, width), random.randint(0, height)),
        ]
        color = (
            random.randint(55, 115),
            random.randint(110, 170),
            random.randint(150, 205),
        )
        draw.line(points, fill=color, width=random.randint(1, 2))

    font = _font(29)
    x = 14
    for ch in code:
        char_layer = Image.new("RGBA", (34, 40), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_layer)
        color = (
            random.randint(18, 80),
            random.randint(80, 145),
            random.randint(115, 190),
        )
        char_draw.text((4, 4), ch, font=font, fill=color)
        char_layer = char_layer.rotate(random.randint(-18, 18), resample=Image.Resampling.BICUBIC, expand=1)
        image.paste(char_layer, (x, random.randint(3, 9)), char_layer)
        x += random.randint(28, 32)

    image = image.filter(ImageFilter.SMOOTH)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@router.get("/captcha", response_model=CaptchaResponse)
def captcha(request: Request) -> CaptchaResponse:
    code = "".join(random.choice(_captcha_chars) for _ in range(4))
    captcha_id = secrets.token_urlsafe(18)
    _captcha_store(request, captcha_id, code)
    return CaptchaResponse(
        captcha_id=captcha_id,
        question="请输入图片验证码",
        image=_captcha_image(code),
        expires_in=CAPTCHA_TTL_SECONDS,
    )


@router.post("/register", response_model=TokenPair)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPair:
    if db.query(User).filter(User.username == payload.username).first():
        raise AppException("DUPLICATE", "用户名已存在", status_code=409)
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise AppException("DUPLICATE", "邮箱已注册", status_code=409)
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    role = db.query(Role).filter(Role.name == "user").first()
    if role is not None:
        user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    oplog.info("register user_id=%s username=%s", user.id, user.username)
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenPair)
def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenPair:
    if not _captcha_verify(request, payload.captcha_id, payload.captcha_code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    rid = getattr(request.state, "request_id", "")
    oplog.info("login ok user_id=%s request_id=%s", user.id, rid)
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPair:
    try:
        body = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="refresh_token 无效")
    if body.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="令牌类型错误")
    sub = body.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="令牌无效")
    user = db.query(User).filter(User.id == int(sub)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不可用")
    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )
