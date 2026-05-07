"""从 app_settings 读取管理端「模型与 Prompt」并在推理时生效。"""
from __future__ import annotations

import os
from typing import Any

from backend.app.core.config import LOCAL_QWEN_WEIGHTS_DIR, settings
from backend.app.db.session import SessionLocal
from backend.app.services.app_settings_store import KEY_MODEL, KEY_PROMPTS, get_json
from backend.app.schemas.analyze import BertResult
from backend.app.services.llm_prompt_base import DEFAULT_SYSTEM_PROMPT
from backend.app.services.prompt_scene_router import infer_scene_from_signals, truthy_auto_prompt

def _prompt_recency_ts(p: dict[str, Any]) -> str:
    """用于同场景多条启用模板时的选择：优先 update_time，否则 create_time（均为 YYYY-MM-DD HH:MM:SS 时可字典序比新旧）。"""
    for k in ("update_time", "create_time"):
        t = str(p.get(k) or "").strip()
        if t:
            return t
    return "1970-01-01 00:00:00"


def _pick_newest_prompt(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return max(candidates, key=_prompt_recency_ts)


def _local_qwen_available() -> bool:
    return LOCAL_QWEN_WEIGHTS_DIR.is_dir() and (LOCAL_QWEN_WEIGHTS_DIR / "config.json").is_file()


def get_infer_bundle() -> dict[str, Any]:
    """读取管理端配置；LINGJIAN_ADMIN_INFER=0 或读库失败时退回空配置（走环境变量/默认）。"""
    if os.getenv("LINGJIAN_ADMIN_INFER", "1").lower() in {"0", "false", "no", "off"}:
        return {"model": {}, "prompts": []}
    db = SessionLocal()
    try:
        model = get_json(db, KEY_MODEL, {})
        prompts = get_json(db, KEY_PROMPTS, [])
        if not isinstance(model, dict):
            model = {}
        if not isinstance(prompts, list):
            prompts = []
        return {"model": model, "prompts": prompts}
    except Exception:
        return {"model": {}, "prompts": []}
    finally:
        db.close()


def enabled_prompt_scenes(bundle: dict[str, Any]) -> set[str]:
    """当前启用中的模板所覆盖的场景集合。"""
    out: set[str] = set()
    for p in bundle.get("prompts") or []:
        if not isinstance(p, dict):
            continue
        if int(p.get("status", 1) or 0) != 1:
            continue
        s = str(p.get("prompt_scene", "general")).lower().strip() or "general"
        out.add(s)
    return out


def resolve_effective_prompt_scene(
    bundle: dict[str, Any], text: str, bert: BertResult | None
) -> tuple[str, str, dict[str, int] | None]:
    """
    决定本次推理使用的 Prompt 场景（与 resolve_system_prompt 的 preferred_scene 对齐）。

    返回 (effective_scene, source, scores|None)。
    source: manual_config | auto_router | auto_fallback_tech_missing_general | auto_fallback_model_scene
        | auto_fallback_general | auto_fallback_first_enabled | auto_no_templates_using_model_scene
    """
    m = bundle.get("model") or {}
    manual = str(m.get("prompt_scene", "general")).lower().strip() or "general"
    if not truthy_auto_prompt(m.get("auto_prompt_scene", True), default=True):
        return manual, "manual_config", None

    guessed, scores = infer_scene_from_signals(text, bert)
    es = enabled_prompt_scenes(bundle)
    if not es:
        return manual, "auto_no_templates_using_model_scene", scores

    if guessed in es:
        return guessed, "auto_router", scores

    # 路由推断为 tech 但未启用科技类模板时，若存在 general，优先于模型默认的 medical，避免 ICT 类文案误套医疗/药品向补充规则
    if guessed == "tech" and "tech" not in es and "general" in es:
        return "general", "auto_fallback_tech_missing_general", scores

    if manual in es:
        return manual, "auto_fallback_model_scene", scores

    if "general" in es:
        return "general", "auto_fallback_general", scores

    first = sorted(es)[0]
    return first, "auto_fallback_first_enabled", scores


def resolve_llm_model_path(bundle: dict[str, Any]) -> str:
    """优先环境变量 LINGJIAN_LLM_MODEL；否则按管理端 model_version 映射本地 Qwen；最后 settings.llm_model。"""
    env_path = os.getenv("LINGJIAN_LLM_MODEL", "").strip()
    if env_path:
        return env_path
    m = bundle.get("model") or {}
    ver = str(m.get("model_version", "qwen_v2")).lower()
    if ver.startswith("qwen") and _local_qwen_available():
        return str(LOCAL_QWEN_WEIGHTS_DIR.resolve())
    return settings.llm_model


def resolve_system_prompt(
    bundle: dict[str, Any], *, preferred_scene: str | None = None
) -> str:
    """默认契约 + 启用中的 Prompt 模板（优先 preferred_scene / model.prompt_scene，其次 general）。"""
    prompts = bundle.get("prompts") or []
    m = bundle.get("model") or {}
    if preferred_scene is not None:
        preferred_scene = str(preferred_scene).lower().strip() or "general"
    else:
        preferred_scene = str(m.get("prompt_scene", "general")).lower().strip()
    enabled = [
        p
        for p in prompts
        if isinstance(p, dict) and int(p.get("status", 1) or 0) == 1
    ]
    if not enabled:
        return DEFAULT_SYSTEM_PROMPT
    matching = [
        p
        for p in enabled
        if str(p.get("prompt_scene", "")).lower().strip() == preferred_scene
    ]
    if matching:
        pick = _pick_newest_prompt(matching)
    else:
        gen = [
            p
            for p in enabled
            if str(p.get("prompt_scene", "")).lower().strip() == "general"
        ]
        pick = _pick_newest_prompt(gen) if gen else _pick_newest_prompt(enabled)
    extra = str(pick.get("prompt_content") or "").strip()
    out_fmt = str(pick.get("output_format") or "").strip()
    if not extra and not out_fmt:
        return DEFAULT_SYSTEM_PROMPT
    parts: list[str] = [
        DEFAULT_SYSTEM_PROMPT,
        "\n\n---\n【管理员配置的补充规则】（不得违背上文 JSON 键名与输出结构要求；不得删减必填字段）\n",
    ]
    if extra:
        parts.append(extra)
    if out_fmt:
        parts.append("\n【输出格式补充说明】\n")
        parts.append(out_fmt)
    return "".join(parts)


def resolve_generation_temperature(bundle: dict[str, Any]) -> float:
    """由管理端「推理置信度阈值」slider 映射生成 temperature：置信度越高 temperature 越低。"""
    m = bundle.get("model") or {}
    try:
        c = float(m.get("confidence", 0.8))
    except (TypeError, ValueError):
        c = 0.8
    c = max(0.0, min(1.0, c))
    # confidence 0 -> t=0.5, confidence 1 -> t=0.05
    return round(0.05 + (1.0 - c) * 0.45, 3)


def resolve_quantization(bundle: dict[str, Any]) -> str:
    """GPU 权重量化：优先环境变量 LINGJIAN_LLM_QUANTIZATION，其次管理端 model.quantization；默认 8bit。"""
    env = os.getenv("LINGJIAN_LLM_QUANTIZATION", "").strip().lower()
    if env in ("8bit", "int8", "8"):
        return "8bit"
    if env in ("16bit", "fp16", "16", "none", "off", "false", "0"):
        return "16bit"
    m = bundle.get("model") or {}
    q = str(m.get("quantization", "8bit")).strip().lower()
    if q in ("8bit", "int8", "8"):
        return "8bit"
    return "16bit"
