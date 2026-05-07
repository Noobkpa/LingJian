"""FastAPI 入口：日志、限流、Redis、路由聚合。"""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.engine.url import make_url

from backend.app.api.v1.router import api_v1_router
from backend.app.core.config import settings
from backend.app.core.handlers import register_exception_handlers
from backend.app.core.logging_config import setup_logging
from backend.app.core.rate_limit import rate_limit_key
from backend.app.db.session import SessionLocal
from backend.app.middleware.request_id import RequestIdMiddleware
from backend.app.services.seed import (
    ensure_bootstrap_admin,
    ensure_default_prompt_templates,
    seed_rbac_if_empty,
)


def _ensure_sqlite_parent_dir() -> None:
    url = make_url(settings.database_url)
    if url.drivername.startswith("sqlite") and url.database:
        Path(url.database).resolve().parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.log_dir, settings.log_level)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    _ensure_sqlite_parent_dir()
    backend_root = Path(__file__).resolve().parents[1]
    alembic_ini = backend_root / "alembic.ini"
    if alembic_ini.is_file():
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(alembic_ini))
        command.upgrade(cfg, "head")

    db = SessionLocal()
    try:
        seed_rbac_if_empty(db)
        ensure_default_prompt_templates(db)
        ensure_bootstrap_admin(db)
    finally:
        db.close()

    log = logging.getLogger(__name__)
    try:
        # 未启动 Redis 时，默认连接会长时间阻塞（Windows 上可达数分钟），导致一直停在「Waiting for application startup」
        client = redis.from_url(
            settings.redis_cache_url,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        client.ping()
        app.state.redis_client = client
    except (redis.RedisError, OSError, TimeoutError) as e:
        log.warning("Redis 不可用（%s），跳过缓存客户端；限流等仍可用。", e)
        app.state.redis_client = None

    if settings.enable_llm:
        try:
            import tiktoken  # noqa: F401
        except ImportError:
            logging.getLogger(__name__).warning(
                "LINGJIAN_ENABLE_LLM 已开启，但当前解释器无法导入 tiktoken（sys.executable=%s）。"
                "Qwen  tokenizer 会报错，请执行：\"%s -m pip install tiktoken\" 后重启。",
                sys.executable,
                sys.executable,
            )

    yield

    rc = getattr(app.state, "redis_client", None)
    if rc is not None:
        try:
            rc.close()
        except redis.RedisError:
            pass


limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=[f"{settings.rate_limit_per_second}/second"],
)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.limiter = limiter

    register_exception_handlers(app)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "app": settings.app_name}

    app.include_router(api_v1_router, prefix=settings.api_prefix)

    _frontend = Path(__file__).resolve().parents[2] / "frontend"
    if _frontend.is_dir():
        app.mount("/demo", StaticFiles(directory=str(_frontend), html=True), name="demo")

    return app


app = create_app()
