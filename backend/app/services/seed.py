"""首次启动时写入默认 RBAC；可选创建首个管理员；默认 Prompt 模板。"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.orm import AppSetting, Permission, Role, User
from backend.app.services.app_settings_store import KEY_PROMPTS

PERMISSION_DEFS: list[tuple[str, str]] = [
    ("analyze:run", "执行分析流水线"),
    ("content:upload", "单条上传"),
    ("content:batch", "批量/ZIP 导入"),
    ("review:read", "查看审核队列"),
    ("review:write", "认领/审核流转"),
    ("admin:stats", "管理端统计"),
    ("admin:export", "批量导出"),
]

ROLE_BINDINGS: dict[str, list[str]] = {
    "admin": [code for code, _ in PERMISSION_DEFS],
    "user": ["analyze:run", "content:upload"],
    "reviewer": ["analyze:run", "review:read", "review:write"],
}


def seed_rbac_if_empty(db: Session) -> None:
    if db.query(Permission).first() is not None:
        return
    code_to_perm: dict[str, Permission] = {}
    for code, desc in PERMISSION_DEFS:
        p = Permission(code=code, description=desc)
        db.add(p)
        code_to_perm[code] = p
    db.flush()

    for role_name, perm_codes in ROLE_BINDINGS.items():
        r = Role(name=role_name, description=f"角色 {role_name}")
        db.add(r)
        for pc in perm_codes:
            r.permissions.append(code_to_perm[pc])

    db.commit()


# 内置四类场景模板顺序（与路由 medical/health/tech/general 一致）
_BUILTIN_SCENE_ORDER: tuple[str, ...] = ("general", "medical", "health", "tech")


def _builtin_prompt_for_scene(scene: str, now_str: str) -> dict:
    """单条内置模板；scene 须为 general|medical|health|tech。"""
    scene = str(scene).lower().strip()
    common_fmt = (
        "顶层键仅限契约所列字段；勿添加 Markdown；judgment_basis、why_sound、why_risky、reader_actions "
        "须为完整书面中文；禁止把 BERT 机读摘要句当作 judgment_basis 主体。"
    )
    if scene == "general":
        return {
            "prompt_id": "tpl-system-general",
            "prompt_name": "默认通用研判模板",
            "prompt_scene": "general",
            "prompt_content": (
                "在严格遵守上文 JSON 输出契约的前提下，补充考量：\n"
                "1）区分事实陈述、推断结论与营销话术；对缺乏出处或过度绝对的表述提高警觉。\n"
                "2）结合 BERT 显性标签与文本语义：标签命中但语境明显为反讽/辟谣时，勿机械升格风险。\n"
                "3）judgment_basis 须面向读者说明「为何是该档」与阅读提醒，避免复述【文本】长句。\n"
                "4）涉及医疗健康时，关注夸大疗效、替代正规诊疗等表述；仍输出要求的 JSON 风险档位。"
            ),
            "output_format": common_fmt,
            "status": 1,
            "create_time": now_str,
            "update_time": now_str,
        }
    if scene == "medical":
        return {
            "prompt_id": "tpl-system-medical",
            "prompt_name": "默认医疗类伪科普研判模板",
            "prompt_scene": "medical",
            "prompt_content": (
                "本模板适用于医疗、药品、疾病诊疗相关表述。在契约 JSON 前提下侧重：\n"
                "1）警惕「包治」「根治」「永不复发」「无效退款」及暗示替代正规诊疗、停药换药等高危话术。\n"
                "2）对治愈率、有效率、临床验证、权威背书等数据与身份，要求可核查来源；个人体验不得冒充循证结论。\n"
                "3）区分正规科普（来源可溯、限定适应症与禁忌）与营销软文；后者在 logical_fallacy / scientific_error 中写清不当类比或证据不足。\n"
                "4）why_risky 须用短引号「」点出正文中最具体的医疗断言或推销句，勿空泛套用「药品类」等标签而不摘句。\n"
                "5）reader_actions 至少一条指向国家药监局说明书/批准信息、国家卫健委或学会公开指南、正规医院门诊等可核实渠道。"
            ),
            "output_format": common_fmt,
            "status": 1,
            "create_time": now_str,
            "update_time": now_str,
        }
    if scene == "health":
        return {
            "prompt_id": "tpl-system-health",
            "prompt_name": "默认养生类伪科普研判模板",
            "prompt_scene": "health",
            "prompt_content": (
                "本模板适用于养生、保健、食疗、体质调理等非处方语境。在契约 JSON 前提下侧重：\n"
                "1）关注酸碱体质、排毒/清宿便、辟谷轻断食治病、经络穴位「治病」、保健品当药、能量/量子/磁疗养生等常见话术。\n"
                "2）对「几天见效」「去湿驱寒包治」「食品代替药物」等绝对化承诺提高权重；区分一般生活方式建议与疗效断言。\n"
                "3）scientific_error 可点明违背生理学或缺乏对照证据之处；勿把普通食疗科普一律打成高风险，须结合语气与承诺强度。\n"
                "4）reader_actions 可建议查阅中国营养学会、疾控中心科普、市监总局保健食品专区等公开信息。"
            ),
            "output_format": common_fmt,
            "status": 1,
            "create_time": now_str,
            "update_time": now_str,
        }
    if scene == "tech":
        return {
            "prompt_id": "tpl-system-tech",
            "prompt_name": "默认科技类伪科普研判模板",
            "prompt_scene": "tech",
            "prompt_content": (
                "本模板适用于通信、数码、家电、芯片、AI、能源、航天等 ICT 与硬科技话题。在契约 JSON 前提下侧重：\n"
                "1）关注辐射致癌恐吓、5G/基站/家电夸大危害、量子民用玄学、芯片/算力谣言、AI 恐吓营销、伪专业名词堆砌等。\n"
                "2）对可验证的技术参数（国标、工信部公告、厂商白皮书、IEEE/3GPP 等）与自媒体结论要区分证据层级；勿用药品疗效话术评价工程问题。\n"
                "3）若正文为产品性能优化、系统卡顿修复等 IT 场景，judgment_basis 与 why_risky 应从「宣传是否夸大技术效果、是否存在虚假工程背书」切入，不要强行写成医药宣传。\n"
                "4）reader_actions 三至五条须以工程与信息科技求证为主（如国标全文公开平台、工信部/市监通报、厂商技术文档、CVE/NVD、可重复测评）；"
                "禁止通篇只写卫健委门诊、处方药或「问医生」等纯医疗路径。\n"
                "5）若正文同时夹带健康恐吓（如辐射致癌），可单列一条指向国家疾控或世卫公开技术说明原文，但仍不应把全文写成就诊指南。"
            ),
            "output_format": common_fmt,
            "status": 1,
            "create_time": now_str,
            "update_time": now_str,
        }
    raise ValueError(f"unknown scene: {scene}")


def _default_prompt_templates(now_str: str) -> list[dict]:
    """系统内置四类场景默认 Prompt（首次空库时一次性写入）。"""
    return [_builtin_prompt_for_scene(s, now_str) for s in _BUILTIN_SCENE_ORDER]


def ensure_default_prompt_templates(db: Session) -> None:
    """写入并补全内置 Prompt：空库时写入四类；已有数据时仅为缺失的场景追加内置条（不覆盖自定义）。"""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    row = db.query(AppSetting).filter(AppSetting.key == KEY_PROMPTS).first()

    items: list[Any] = []
    if row is not None and isinstance(row.value, list):
        items = list(row.value)

    scenes_present: set[str] = set()
    for it in items:
        if isinstance(it, dict):
            s = str(it.get("prompt_scene", "general")).lower().strip() or "general"
            scenes_present.add(s)

    to_append: list[dict] = []
    for scene in _BUILTIN_SCENE_ORDER:
        if scene in scenes_present:
            continue
        tpl = _builtin_prompt_for_scene(scene, now_str)
        to_append.append(tpl)
        scenes_present.add(scene)

    if not to_append and row is not None:
        return

    if row is None:
        db.add(
            AppSetting(
                key=KEY_PROMPTS,
                value=_default_prompt_templates(now_str) if not items else items + to_append,
            )
        )
    else:
        row.value = _default_prompt_templates(now_str) if not items else items + to_append
    db.commit()


def ensure_bootstrap_admin(db: Session) -> None:
    """当环境变量提供 LINGJIAN_BOOTSTRAP_ADMIN / LINGJIAN_BOOTSTRAP_PASSWORD 且库中无用户时创建 admin 角色用户。"""
    u = os.getenv("LINGJIAN_BOOTSTRAP_ADMIN", "").strip()
    p = os.getenv("LINGJIAN_BOOTSTRAP_PASSWORD", "").strip()
    if not u or not p:
        return
    if db.query(User).first() is not None:
        return
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if admin_role is None:
        return
    user = User(username=u, email=None, hashed_password=hash_password(p))
    user.roles.append(admin_role)
    db.add(user)
    db.commit()
