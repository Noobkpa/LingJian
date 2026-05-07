"""分类日志：运行 / 操作 / 错误。"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: Path, level: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    lvl = getattr(logging, level.upper(), logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(lvl)

    # 控制台
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # app 运行日志
    app_h = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    app_h.setFormatter(fmt)
    logging.getLogger("backend").addHandler(app_h)
    logging.getLogger("backend").setLevel(lvl)
    logging.getLogger("backend").propagate = False
    logging.getLogger("backend").addHandler(ch)

    # 操作日志（认证与关键业务）
    op = logging.getLogger("operation")
    op.setLevel(lvl)
    op.propagate = False
    oh = RotatingFileHandler(
        log_dir / "operation.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    oh.setFormatter(fmt)
    op.addHandler(oh)

    # 错误日志
    err = logging.getLogger("error")
    err.setLevel(logging.ERROR)
    err.propagate = False
    eh = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    eh.setFormatter(fmt)
    err.addHandler(eh)

    # uvicorn 降噪
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
