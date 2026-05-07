"""最简单的数据库备份：SQLite 复制文件；MySQL 调用本机 mysqldump。"""
from __future__ import annotations

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine.url import make_url

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def _sqlite_db_path(url: Any) -> Path:
    raw = url.database
    if not raw:
        raise ValueError("SQLite URL 缺少数据库路径")
    p = Path(raw)
    if not p.is_absolute():
        p = (settings.backup_dir.parent / p).resolve()
    return p


def run_simple_db_backup() -> dict[str, Any]:
    """
    执行一次备份，返回:
      ok: bool
      path: 备份文件绝对路径（成功时）
      size_bytes / file_size: 原始字节数 / 人类可读大小
      error: 失败原因
    """
    backup_dir = settings.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    url = make_url(settings.database_url)
    driver = (url.drivername or "").lower()

    try:
        if driver == "sqlite":
            src = _sqlite_db_path(url)
            if not src.is_file():
                return {"ok": False, "error": f"SQLite 文件不存在：{src}"}
            dest = backup_dir / f"lingjian_{ts}.db"
            shutil.copy2(src, dest)
            n = dest.stat().st_size
            return {
                "ok": True,
                "path": str(dest),
                "size_bytes": n,
                "file_size": _fmt_size(n),
            }

        if "mysql" in driver:
            db = url.database
            if not db:
                return {"ok": False, "error": "MySQL URL 缺少库名"}
            dest = backup_dir / f"lingjian_{ts}.sql"
            host = url.host or "127.0.0.1"
            port = int(url.port or 3306)
            user = url.username or "root"
            cmd: list[str] = [
                "mysqldump",
                "--single-transaction",
                "--quick",
                "-h",
                host,
                "-P",
                str(port),
                "-u",
                user,
            ]
            if url.password:
                cmd.append(f"-p{url.password}")
            cmd.append(db)
            with open(dest, "wb") as out:
                r = subprocess.run(
                    cmd,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    timeout=600,
                    shell=False,
                )
            if r.returncode != 0:
                err = (r.stderr or b"").decode("utf-8", errors="replace")[:800]
                try:
                    dest.unlink(missing_ok=True)
                except OSError:
                    pass
                return {"ok": False, "error": f"mysqldump 失败（exit {r.returncode}）：{err or '无 stderr'}"}
            n = dest.stat().st_size
            return {
                "ok": True,
                "path": str(dest),
                "size_bytes": n,
                "file_size": _fmt_size(n),
            }

        return {
            "ok": False,
            "error": f"当前驱动「{driver}」未实现自动备份，请改用 SQLite 或安装 mysqldump 后使用 MySQL。",
        }
    except FileNotFoundError:
        if "mysql" in driver:
            return {
                "ok": False,
                "error": "未找到 mysqldump，请安装 MySQL 客户端并把 bin 加入 PATH。",
            }
        return {"ok": False, "error": "备份失败：文件未找到"}
    except Exception as e:
        logger.exception("simple_db_backup failed")
        return {"ok": False, "error": str(e)}


def list_backup_files() -> list[dict[str, Any]]:
    """列出备份目录下的 .db / .sql，按修改时间倒序。"""
    d = settings.backup_dir
    if not d.is_dir():
        return []
    rows: list[tuple[Path, float]] = []
    for p in d.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".db", ".sql"}:
            continue
        if not p.name.startswith("lingjian_"):
            continue
        try:
            rows.append((p, p.stat().st_mtime))
        except OSError:
            continue
    rows.sort(key=lambda x: x[1], reverse=True)
    out: list[dict[str, Any]] = []
    for p, mtime in rows[:100]:
        try:
            n = p.stat().st_size
        except OSError:
            continue
        out.append(
            {
                "backup_id": p.name,
                "backup_type": "full",
                "file_size": _fmt_size(n),
                "create_time": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return out
