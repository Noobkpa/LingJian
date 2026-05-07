"""上传校验：扩展名、大小、魔数。"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.app.core.config import settings

_ALLOWED_SUFFIX = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _magic_ok(head: bytes, suffix: str) -> bool:
    if suffix in {".jpg", ".jpeg"}:
        return head.startswith(b"\xff\xd8\xff")
    if suffix == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix == ".bmp":
        return head.startswith(b"BM")
    if suffix == ".webp":
        chunk = head[:32] if len(head) >= 32 else head
        return chunk.startswith(b"RIFF") and b"WEBP" in chunk
    return False


async def save_upload_validated(upload: UploadFile) -> tuple[Path, str]:
    """保存上传图片并返回路径与内容 SHA256（用于缓存键）。"""
    if not upload.filename:
        raise HTTPException(status_code=400, detail="上传文件名为空")
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in _ALLOWED_SUFFIX:
        raise HTTPException(status_code=400, detail="仅支持 png/jpg/jpeg/bmp/webp 图片")

    save_dir = settings.upload_dir / uuid.uuid4().hex
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(upload.filename).name)
    if not safe_name.lower().endswith(suffix):
        safe_name = f"upload{suffix}"
    path = save_dir / safe_name

    h = hashlib.sha256()
    size = 0
    with path.open("wb") as fout:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.max_upload_bytes:
                path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="文件过大")
            h.update(chunk)
            fout.write(chunk)

    raw = path.read_bytes()
    head = raw[:32]
    if not _magic_ok(head, suffix):
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="文件内容与扩展名不匹配或非受支持图片")

    return path, h.hexdigest()
