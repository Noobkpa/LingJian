"""用户反馈落盘（JSON Lines），便于运维查看，无需额外数据库表。"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger("backend.app.feedback_store")

_lock = threading.Lock()


def _feedback_file() -> Path:
    d = settings.upload_dir / "feedback"
    d.mkdir(parents=True, exist_ok=True)
    return d / "entries.jsonl"


def append_feedback(
    *,
    message: str,
    content_id: str | None,
    client_ip: str | None,
    user_agent: str | None,
    extra: dict[str, Any] | None = None,
) -> None:
    row: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "content_id": (content_id or "").strip() or None,
        "message": message,
        "client_ip": client_ip,
        "user_agent": (user_agent or "")[:512] or None,
    }
    if extra:
        row["extra"] = extra
    line = json.dumps(row, ensure_ascii=False) + "\n"
    path = _feedback_file()
    try:
        with _lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line)
    except OSError as e:
        logger.exception("feedback write failed: %s", e)
        raise
