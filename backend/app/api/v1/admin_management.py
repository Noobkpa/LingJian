"""管理端：用户、模型与 Prompt、系统配置、操作日志、备份等。"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.core.deps import get_db, redis_dependency, require_permission
from backend.app.core.security import hash_password
from backend.app.models.orm import AuditLog, Role, User
from backend.app.services.app_settings_store import (
    KEY_BACKUP_CFG,
    KEY_MODEL,
    KEY_PROMPTS,
    KEY_SYSTEM,
    get_json,
    set_json,
)
from backend.app.services.simple_db_backup import list_backup_files, run_simple_db_backup

router = APIRouter(prefix="/admin", tags=["admin"])

_perm = require_permission("admin:stats")

logger = logging.getLogger(__name__)


def _primary_role_name(user: User) -> str:
    names = {r.name for r in user.roles}
    if "admin" in names:
        return "admin"
    return "user"


def _serialize_user(u: User) -> dict[str, Any]:
    reg = u.created_at
    if hasattr(reg, "strftime"):
        rt = reg.strftime("%Y-%m-%d %H:%M:%S")
    else:
        rt = str(reg)
    return {
        "user_id": u.id,
        "username": u.username,
        "nickname": u.nickname or u.username,
        "phone": u.phone or "",
        "role": _primary_role_name(u),
        "status": 1 if u.is_active else 0,
        "register_time": rt,
    }


@router.get("/user/list")
def admin_user_list(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=500),
    username: str = "",
    status: str | None = None,
) -> dict[str, Any]:
    q = db.query(User).options(joinedload(User.roles))
    if username:
        q = q.filter(User.username.contains(username.strip()))
    if status is not None and status != "":
        if str(status) == "1":
            q = q.filter(User.is_active.is_(True))
        elif str(status) == "0":
            q = q.filter(User.is_active.is_(False))
    total = q.count()
    rows = (
        q.order_by(User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return {"list": [_serialize_user(u) for u in rows], "total": total}


class UserAddBody(BaseModel):
    username: str = Field(..., min_length=1, max_length=80)
    nickname: str = ""
    phone: str = ""
    role: str = "user"
    password: str = Field(..., min_length=6, max_length=128)


@router.post("/user/add")
def admin_user_add(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
    body: UserAddBody,
) -> dict[str, str]:
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    role_name = "admin" if body.role == "admin" else "user"
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        raise HTTPException(status_code=500, detail="角色未初始化")
    u = User(
        username=body.username,
        email=None,
        nickname=body.nickname or None,
        phone=body.phone or None,
        hashed_password=hash_password(body.password),
    )
    u.roles.append(role)
    db.add(u)
    db.commit()
    return {"ok": "true"}


class UserUpdateBody(BaseModel):
    user_id: int
    username: str | None = None
    nickname: str = ""
    phone: str = ""


@router.put("/user/update")
def admin_user_update(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
    body: UserUpdateBody,
) -> dict[str, str]:
    u = db.query(User).filter(User.id == body.user_id).first()
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.nickname is not None:
        u.nickname = body.nickname or None
    if body.phone is not None:
        u.phone = body.phone or None
    db.commit()
    return {"ok": "true"}


class UserToggleBody(BaseModel):
    user_id: int
    status: int = Field(..., ge=0, le=1)


@router.post("/user/toggle-status")
def admin_user_toggle(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(_perm)],
    body: UserToggleBody,
) -> dict[str, str]:
    if body.user_id == current.id:
        raise HTTPException(status_code=400, detail="不能冻结当前登录账号")
    u = db.query(User).filter(User.id == body.user_id).first()
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    u.is_active = body.status == 1
    db.commit()
    return {"ok": "true"}


class UserDeleteBody(BaseModel):
    user_id: int


@router.delete("/user/delete")
def admin_user_delete(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(_perm)],
    body: UserDeleteBody,
) -> dict[str, str]:
    if body.user_id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    u = db.query(User).filter(User.id == body.user_id).first()
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(u)
    db.commit()
    return {"ok": "true"}


def _normalize_quantization(raw: object) -> str:
    s = str(raw or "").strip().lower()
    if s in ("8bit", "int8", "8"):
        return "8bit"
    return "16bit"


def _normalize_bool(raw: object, *, default: bool) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    s = str(raw).strip().lower()
    if s in ("0", "false", "no", "off"):
        return False
    if s in ("1", "true", "yes", "on"):
        return True
    return default


def _normalize_prompt_scene(raw: object) -> str:
    s = str(raw or "").strip().lower()
    if s in ("general", "health", "medical", "tech"):
        return s
    return "general"


def _default_model() -> dict[str, Any]:
    return {
        "model_version": "qwen_v2",
        "quantization": "8bit",
        "confidence": 0.8,
        "prompt_scene": "general",
        "auto_prompt_scene": True,
    }


def _default_system() -> dict[str, Any]:
    return {
        "text_max_length": 5000,
        "image_max_size": 5,
        "batch_max_count": 100,
        "high_risk_threshold": 70,
        "mid_risk_threshold": 40,
    }


# --- 模型与 Prompt（持久化 app_settings） ---


@router.get("/model/settings")
def admin_model_settings_get(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
) -> dict[str, Any]:
    raw = get_json(db, KEY_MODEL, _default_model())
    if not isinstance(raw, dict):
        return _default_model()
    merged = {**_default_model(), **raw}
    merged["quantization"] = _normalize_quantization(merged.get("quantization"))
    merged["prompt_scene"] = _normalize_prompt_scene(merged.get("prompt_scene"))
    merged["auto_prompt_scene"] = _normalize_bool(
        merged.get("auto_prompt_scene"), default=True
    )
    return merged


@router.get("/prompt/list")
def admin_prompt_list(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
) -> dict[str, Any]:
    raw = get_json(db, KEY_PROMPTS, [])
    items = raw if isinstance(raw, list) else []
    return {"list": items}


@router.post("/model/config")
def admin_model_config(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    merged = {**_default_model(), **payload}
    merged["quantization"] = _normalize_quantization(merged.get("quantization"))
    merged["prompt_scene"] = _normalize_prompt_scene(merged.get("prompt_scene"))
    merged["auto_prompt_scene"] = _normalize_bool(
        payload.get("auto_prompt_scene"), default=True
    )
    set_json(
        db,
        KEY_MODEL,
        merged,
        user_id=user.id,
        action="admin.model.config",
        log_type="system",
    )
    return {"ok": "true"}


@router.post("/model/test")
def admin_model_test(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
) -> dict[str, bool]:
    db.add(
        AuditLog(
            user_id=user.id,
            action="admin.model.test",
            resource_type="model",
            detail={"log_type": "system", "result": "ok"},
        )
    )
    db.commit()
    return {"ok": True}


@router.post("/prompt/toggle-status")
def admin_prompt_toggle(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    pid = str(payload.get("prompt_id", ""))
    st = int(payload.get("status", 0))
    items: list[Any] = list(get_json(db, KEY_PROMPTS, []))
    for it in items:
        if isinstance(it, dict) and str(it.get("prompt_id")) == pid:
            it["status"] = st
            break
    set_json(
        db,
        KEY_PROMPTS,
        items,
        user_id=user.id,
        action="admin.prompt.toggle",
        log_type="user",
    )
    return {"ok": "true"}


@router.post("/prompt/test")
def admin_prompt_test(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    db.add(
        AuditLog(
            user_id=user.id,
            action="admin.prompt.test",
            resource_type="prompt",
            resource_id=str(payload.get("prompt_id", "")),
            detail={"log_type": "user"},
        )
    )
    db.commit()
    return {"ok": "true"}


@router.put("/prompt/update")
def admin_prompt_update(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    pid = str(payload.get("prompt_id", ""))
    items: list[Any] = list(get_json(db, KEY_PROMPTS, []))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for i, it in enumerate(items):
        if isinstance(it, dict) and str(it.get("prompt_id")) == pid:
            merged = {**it, **payload}
            merged["update_time"] = now
            items[i] = merged
            break
    set_json(
        db,
        KEY_PROMPTS,
        items,
        user_id=user.id,
        action="admin.prompt.update",
        log_type="user",
    )
    return {"ok": "true"}


@router.post("/prompt/add")
def admin_prompt_add(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    items: list[Any] = list(get_json(db, KEY_PROMPTS, []))
    row = {**payload}
    row["prompt_id"] = str(row.get("prompt_id") or uuid.uuid4().hex[:12])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    row["create_time"] = now
    row["update_time"] = now
    items.append(row)
    set_json(
        db,
        KEY_PROMPTS,
        items,
        user_id=user.id,
        action="admin.prompt.add",
        log_type="user",
    )
    return {"ok": "true"}


# --- 系统配置 ---


@router.get("/system/settings")
def admin_system_settings_get(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
) -> dict[str, Any]:
    return get_json(db, KEY_SYSTEM, _default_system())


@router.post("/system/config")
def admin_system_config(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    merged = {**_default_system(), **payload}
    set_json(
        db,
        KEY_SYSTEM,
        merged,
        user_id=user.id,
        action="admin.system.config",
        log_type="system",
    )
    return {"ok": "true"}


class ClearCacheBody(BaseModel):
    type: str = "redis"


@router.post("/system/clear-cache")
def admin_clear_cache(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    body: ClearCacheBody,
) -> dict[str, Any]:
    if body.type == "redis":
        rc = redis_dependency(request)
        flushed = False
        if rc is None:
            db.add(
                AuditLog(
                    user_id=user.id,
                    action="admin.system.clear_cache",
                    resource_type="cache",
                    detail={
                        "log_type": "system",
                        "type": "redis",
                        "redis_available": False,
                        "flushed": False,
                    },
                )
            )
            db.commit()
            return {
                "ok": True,
                "cleared": body.type,
                "redis_available": False,
                "flushed": False,
                "message": "Redis 未连接（启动时 ping 失败），推理缓存未写入 Redis，无需清理。",
            }
        try:
            rc.flushdb()
            flushed = True
        except Exception as e:
            logger.exception("admin clear-cache: Redis flushdb failed")
            raise HTTPException(
                status_code=503,
                detail=f"Redis FLUSHDB 失败：{e!s}",
            ) from e
        db.add(
            AuditLog(
                user_id=user.id,
                action="admin.system.clear_cache",
                resource_type="cache",
                detail={
                    "log_type": "system",
                    "type": "redis",
                    "redis_available": True,
                    "flushed": True,
                },
            )
        )
        db.commit()
        return {
            "ok": True,
            "cleared": body.type,
            "redis_available": True,
            "flushed": True,
            "message": "已清空本服务使用的 Redis 库（推理缓存等）。",
        }
    db.add(
        AuditLog(
            user_id=user.id,
            action="admin.system.clear_cache",
            resource_type="cache",
            detail={"log_type": "system", "type": body.type, "note": "ES 未接入"},
        )
    )
    db.commit()
    return {"ok": True, "cleared": body.type, "note": "ES 索引重建未实现"}


@router.get("/log/list")
def admin_log_list(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=500),
    log_type: str | None = None,
    username: str | None = None,
) -> dict[str, Any]:
    q = db.query(AuditLog)
    if username:
        q = q.join(User, AuditLog.user_id == User.id).filter(User.username.contains(username.strip()))
    if log_type:
        q = q.filter(func.json_extract(AuditLog.detail, "$.log_type") == log_type)
    total = q.count()
    rows = (
        q.order_by(AuditLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    user_ids = {r.user_id for r in rows if r.user_id}
    id_to_name: dict[int, str] = {}
    if user_ids:
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            id_to_name[u.id] = u.username

    out: list[dict[str, Any]] = []
    for r in rows:
        detail = r.detail or {}
        lt = str(detail.get("log_type") or "system")
        uname = id_to_name.get(r.user_id) if r.user_id else None
        ts = r.created_at
        ct = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        out.append(
            {
                "log_id": r.id,
                "log_type": lt,
                "username": uname or "-",
                "operation": r.action,
                "ip": detail.get("ip") or "-",
                "create_time": ct,
            }
        )
    return {"list": out, "total": total}


# --- 备份（配置与记录持久化） ---


@router.get("/backup/settings")
def admin_backup_settings_get(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(_perm)],
) -> dict[str, Any]:
    default = {"auto_backup": True, "backup_cycle": "daily", "retention_days": 30}
    return get_json(db, KEY_BACKUP_CFG, default)


@router.post("/backup/config")
def admin_backup_config(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, str]:
    default = {"auto_backup": True, "backup_cycle": "daily", "retention_days": 30}
    merged = {**default, **payload}
    set_json(
        db,
        KEY_BACKUP_CFG,
        merged,
        user_id=user.id,
        action="admin.backup.config",
        log_type="system",
    )
    return {"ok": "true"}


@router.post("/backup/manual")
def admin_backup_manual(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(_perm)],
    payload: dict[str, Any],
) -> dict[str, Any]:
    _ = str(payload.get("type", "full"))  # 增量暂未实现，全量与增量均执行一次完整导出
    result = run_simple_db_backup()
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error") or "备份失败")
    set_json(
        db,
        "admin_backup_last",
        {
            "path": result.get("path"),
            "size": result.get("file_size"),
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        },
        user_id=user.id,
        action="admin.backup.manual",
        log_type="system",
        extra_detail={"path": result.get("path")},
    )
    return {"ok": True, "path": result.get("path"), "file_size": result.get("file_size")}


@router.get("/backup/list")
def admin_backup_list(
    _: Annotated[User, Depends(_perm)],
) -> dict[str, Any]:
    return {"list": list_backup_files()}
