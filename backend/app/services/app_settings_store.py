"""管理端 app_settings 读写与审计日志。"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.orm import AppSetting, AuditLog

KEY_MODEL = "admin_model_config"
KEY_PROMPTS = "admin_prompt_templates"
KEY_SYSTEM = "admin_system_config"
KEY_BACKUP_CFG = "admin_backup_config"
KEY_BACKUP_RECORDS = "admin_backup_records"


def _touch(db: Session, key: str, value: Any) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row is None:
        db.add(AppSetting(key=key, value=value))
    else:
        row.value = value


def get_json(db: Session, key: str, default: Any) -> Any:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row is None:
        return default
    return row.value


def set_json(
    db: Session,
    key: str,
    value: Any,
    *,
    user_id: int | None,
    action: str,
    log_type: str = "system",
    extra_detail: dict[str, Any] | None = None,
) -> None:
    _touch(db, key, value)
    detail: dict[str, Any] = {"log_type": log_type, "keys": key}
    if extra_detail:
        detail.update(extra_detail)
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type="app_setting",
            resource_id=key,
            detail=detail,
        )
    )
    db.commit()
