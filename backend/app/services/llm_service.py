from __future__ import annotations

import json
import re
from threading import Lock
from typing import Any

from pathlib import Path

from backend.app.core.config import settings
from backend.app.schemas.analyze import BertResult, LlmResult
from backend.app.services.standard_judgment_builder import (
    _fallback_logical,
    _fallback_scientific,
    _strip_basis_noise_lines,
    heuristic_risk_label_to_std,
)


def _keyword_topic_scene(text: str, bert: BertResult | None) -> str:
    """与路由层关键词推断一致（不依赖管理端模板是否启用），用于回退文案与场景提示。"""
    from backend.app.services.prompt_scene_router import infer_scene_from_signals

    s, _ = infer_scene_from_signals(text or "", bert)
    return s if s else "general"


def _fallback_reader_actions(text: str, bert: BertResult, risk: str, reason: str | None) -> str:
    scene = _keyword_topic_scene(text, bert)
    if risk == "低风险":
        if scene == "tech":
            return (
                "请通过系统或设备厂商官方支持页、软件发行说明与已知问题列表核对性能表述；"
                "勿仅凭社群截图或短视频结论做升级或消费决策。"
            )
        if scene == "health":
            return (
                "请查阅国家疾控局营养健康科普、市监总局「监管科普」或学会公开材料；"
                "勿把个人博主「几天见效」类承诺当成医学结论。"
            )
        return (
            "继续留意信息来源是否为卫健委、疾控中心、医院官网等；"
            "勿仅凭社交媒体截图做健康决策。"
        )
    if _reason_is_llm_json_parse_failure(reason):
        if scene == "tech":
            return (
                "可先稍后重试识别；请核对国家标准全文公开平台、工信部政务公开或厂商技术文档中的相关表述；"
                "若多次出现解析失败，请联系管理员检查生成长度与提示词配置。"
            )
        return (
            "可先稍后重试识别；对正文关键论断请自行交叉核对权威来源；涉及用药与治疗务必咨询执业医师。"
            "若多次出现解析失败，请联系管理员检查生成长度与提示词配置。"
        )
    if scene == "tech":
        return (
            "请检索国家标准全文公开平台、工信部政务公开或市监总局通报中与产品/通信相关的原文；"
            "涉及电磁辐射与健康请对照疾控或世卫公开技术说明中的具体结论段落；"
            "勿将本文当作就医、购药或调整处方药的依据。"
        )
    if scene == "health":
        return (
            "请交叉核对学会公开指南与保健食品注册信息；涉及疾病治疗与处方用药务必咨询执业医师或药师。"
        )
    return "请交叉核对原始论文或官方通报；涉及用药与治疗务必咨询执业医师。"


def _reason_is_llm_json_parse_failure(reason: str | None) -> bool:
    """模型已跑通，但 `_parse_json` 未得到合法 JSON（与「未加载 LLM」区分）。"""
    if not reason:
        return False
    r = str(reason).strip()
    return r == "LLM 输出 JSON 解析失败" or "JSON 解析失败" in r


def _fallback_why_risky_message(reason: str | None) -> str:
    """将依赖类异常改写成面向用户的说明，避免把英文 pip / 导入栈直接塞进「为何存疑」。"""
    if not reason:
        return "LLM 未参与研判，以下风险提示来自统计模型与规则层。"
    if _reason_is_llm_json_parse_failure(reason):
        return (
            "常见原因包括：输出被截断、前后夹杂说明文字或 Markdown 代码块、JSON 括号或引号不合法。"
            "当前已回退为仅以统计模型结论呈现风险；若反复出现，可由管理员适当放宽单次生成长度，"
            "并在提示词中强调「只输出一段合法 JSON、不要用代码围栏」。"
        )
    rl = reason.lower()
    if "einops" in rl or "transformers_stream_generator" in rl:
        return (
            "大模型环境缺少必要依赖（Qwen 建模需 einops、transformers_stream_generator），"
            "已降级为仅依据 BERT 统计与规则提示风险。请在运行后端的 Python 环境中执行 "
            "`pip install einops transformers_stream_generator` 或重新安装项目根目录 `requirement.txt`，然后重启服务。"
        )
    if "beamsearch" in rl or ("cannot import" in rl and "transformers" in rl):
        return (
            "当前 Python 环境中的 transformers 与 Qwen 流式依赖不兼容（常见原因："
            "transformers≥4.57 移除了 BeamSearchScorer，或使用了未在 requirement.txt 中锁版本的解释器）。"
            "请用 Python 3.12（推荐）运行后端，并在该环境中执行 "
            "`pip install -r requirement.txt`（含 transformers<4.57）后重启；勿混用例如 Python 3.14 的全局包。"
        )
    if "python314" in rl or "python 3.14" in rl or "python3.14" in rl.replace(" ", ""):
        return (
            "检测到后端使用 Python 3.14 等过新版本；当前 Qwen/transformers 依赖链尚未按该版本验证，"
            "易出现 BeamSearchScorer 等导入错误。请改用 Python 3.10—3.12（推荐 3.12）启动后端并安装项目根目录 "
            "`requirement.txt` 后重启。"
        )
    if "tiktoken" in rl:
        return (
            "大模型依赖 tiktoken 未就绪，已降级为 BERT+规则。请在后端解释器执行 "
            "`pip install tiktoken` 或与 `requirement.txt` 一致安装后重启。"
        )
    if (
        "matmulltstate" in rl
        or "memory_efficient_backward" in rl
        or ("bitsandbytes" in rl and "object has no attribute" in rl)
    ):
        return (
            "大模型在 GPU 推理时触发底层线性层/量化相关错误（常见于旧版 bitsandbytes 与当前 PyTorch 不匹配）。"
            "当前服务已固定为 fp16 推理路径；若仍出现本提示，请在运行后端的 Python 3.12 环境中按项目根目录 "
            "`requirement.txt` 重装 `torch` 与相关依赖并重启。"
        )
    if "object has no attribute" in rl and (
        "backward" in rl or "matmul" in rl or "quant" in rl
    ):
        return (
            "大模型推理时触发底层算子或自动求导接口异常（多与 PyTorch / CUDA 版本有关），已降级为 BERT+规则。"
            "请在后端环境按 `requirement.txt` 对齐依赖并重启；若持续失败请检查显卡驱动与 CUDA 是否匹配。"
        )
    if "site-packages" in rl or "\\users\\" in rl or "/lib/python" in rl:
        return (
            "大模型加载失败（环境或依赖异常），已降级为 BERT+规则研判。"
            "请在后端实际运行的 Python 中按项目根目录 `requirement.txt` 安装依赖并重启服务。"
        )
    if len(reason) > 320:
        return reason[:320].rstrip() + "…"
    return reason


def _public_llm_reason_for_basis(reason: str | None) -> str:
    """judgment_basis 里附一句人话，避免把整段 ImportError 粘进依据。"""
    if not reason:
        return "大模型未参与本次推理。"
    if _reason_is_llm_json_parse_failure(reason):
        return "大模型已推理，但输出未能解析为结构化结果，本次展示仍以统计模型结论为主。"
    msg = _fallback_why_risky_message(reason)
    parts = [p.strip() for p in msg.split("。") if p.strip()]
    head = (parts[0] + "。") if parts else msg
    return head[:220] + ("…" if len(head) > 220 else "")


class LlmService:
    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._lock = Lock()
        self._loaded_infer_key: str | None = None
        self._runtime_model_path: str | None = None
        self._runtime_temperature: float = 0.1

    @staticmethod
    def _adapter_has_weights(adapter_dir: Path) -> bool:
        return (adapter_dir / "adapter_model.safetensors").is_file() or (
            adapter_dir / "adapter_model.bin"
        ).is_file()

    @staticmethod
    def _parse_json(raw_output: str) -> dict | None:
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if not match:
            return None
        json_str = match.group(0)
        json_str = re.sub(r'(["\d])\s*;\s*', r"\1, ", json_str)
        json_str = json_str.replace("\n", " ").replace("\r", " ")
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_risk_level(value: object) -> str:
        raw = str(value or "未知").strip()
        mapping = {
            "高": "高风险",
            "中": "中风险",
            "低": "低风险",
            "极高": "高风险",
        }
        if raw in mapping:
            return mapping[raw]
        if raw in {"高风险", "中风险", "低风险"}:
            return raw
        return "未知"

    @staticmethod
    def _normalize_score(value: object, fallback: float) -> float:
        try:
            return round(max(0.0, min(100.0, float(value))), 1)
        except (TypeError, ValueError):
            return round(max(0.0, min(100.0, float(fallback))), 1)

    @staticmethod
    def _risk_level_short(normalized: str) -> str:
        n = (normalized or "").strip()
        if n.startswith("高"):
            return "高"
        if n.startswith("中"):
            return "中"
        if n.startswith("低"):
            return "低"
        return "中"

    @staticmethod
    def _canonical_llm_json(
        *,
        content_id: str,
        infer_time_str: str,
        risk_normalized: str,
        comprehensive_score: float,
        logical_fallacy: str,
        scientific_error: str,
        core_features: list[str],
        judgment_basis: str,
        why_sound: str = "",
        why_risky: str = "",
        reader_actions: str = "",
    ) -> str:
        payload = {
            "content_id": content_id,
            "risk_level": LlmService._risk_level_short(risk_normalized),
            "comprehensive_score": comprehensive_score,
            "logical_fallacy": logical_fallacy,
            "scientific_error": scientific_error,
            "core_features": core_features,
            "judgment_basis": judgment_basis,
            "why_sound": why_sound,
            "why_risky": why_risky,
            "reader_actions": reader_actions,
            "infer_time": infer_time_str,
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _fallback(
        text: str,
        bert: BertResult,
        reason: str | None = None,
        *,
        content_id: str = "",
        infer_time_str: str = "",
    ) -> LlmResult:
        if bert.risk_level == "高":
            risk = "高风险"
        elif bert.risk_level == "中":
            risk = "中风险"
        elif bert.risk_level == "低":
            risk = "低风险"
        else:
            risk = "未知"
        features = list(bert.predicted_label_names)
        basis_parts = []
        if not bert.available:
            basis_parts.append(f"BERT 不可用：{bert.error or '未知错误'}")
        if bert.prediction_summary_zh:
            basis_parts.append(bert.prediction_summary_zh)
        if features:
            basis_parts.append(f"BERT 命中显性伪科普特征：{'、'.join(features)}")
        elif text.strip() and bert.available:
            basis_parts.append("BERT 未命中明显显性伪科普特征")
        if reason:
            if _reason_is_llm_json_parse_failure(reason):
                basis_parts.append(_public_llm_reason_for_basis(reason))
            else:
                basis_parts.append(f"LLM 未启用或不可用：{_public_llm_reason_for_basis(reason)}")
        basis = "; ".join(basis_parts)
        score_f = LlmService._normalize_score(bert.total_score_pct, bert.total_score_pct)
        if risk == "低风险" and not features:
            lf, se = "无", "无"
        else:
            lf = _fallback_logical(features)
            se = "无" if risk == "低风险" else _fallback_scientific(
                features=features, risk=heuristic_risk_label_to_std(risk)
            )
        scene = _keyword_topic_scene(text, bert)
        if risk == "低风险":
            if scene == "tech":
                ws = (
                    "当前统计与文本未呈现强烈伪科普模式，故在自动研判框架下保留相对保守结论；"
                    "若涉及工程采购、网络安全或数码消费决策，仍应以标准符合性、厂商支持与可复查测试为准。"
                )
            else:
                ws = (
                    "当前统计与文本未呈现强烈伪科普模式，故在自动研判框架下保留相对保守结论；"
                    "若涉及个体健康决策，仍应以面诊与权威指南为准。"
                )
        elif _reason_is_llm_json_parse_failure(reason):
            ws = (
                "大模型已参与本轮推理，但输出未能稳定解析为结构化结果，故未采用其分字段结论；"
                "当前档位与说明主要依据统计模型与规则层，属自动化粗判，不能替代您逐句细读原文。"
            )
        else:
            ws = "在 LLM 不可用时，系统仅能依据 BERT 统计与规则提示风险，无法展开逐句论证。"
        wr = (
            "未发现足以单独支撑「伪科普」定论的强信号；若您掌握相反权威证据，可提交复核。"
            if risk == "低风险"
            else _fallback_why_risky_message(reason)
        )
        ra = _fallback_reader_actions(text, bert, risk, reason)
        raw = LlmService._canonical_llm_json(
            content_id=content_id,
            infer_time_str=infer_time_str,
            risk_normalized=risk,
            comprehensive_score=score_f,
            logical_fallacy=lf,
            scientific_error=se,
            core_features=features,
            judgment_basis=basis,
            why_sound=ws,
            why_risky=wr,
            reader_actions=ra,
        )
        return LlmResult(
            available=False,
            error=reason,
            risk_level=risk,
            comprehensive_score=score_f,
            judgment_basis=basis,
            why_sound=ws,
            why_risky=wr,
            reader_actions=ra,
            features=features,
            logical_fallacy=lf,
            scientific_error=se,
            raw_output=raw,
        )

    def _extra_model_kw(self, torch_mod: object) -> dict[str, object]:
        """GPU：fp16 全精度推理（不使用 bitsandbytes 4/8bit，避免与 PyTorch 版本冲突）。CPU：float32。"""
        torch = torch_mod
        if not torch.cuda.is_available():
            return {"torch_dtype": torch.float32, "device_map": None}
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        return {"torch_dtype": torch.float16, "device_map": {"": 0}}

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            def load_causal(model_path: str) -> object:
                kwargs: dict[str, object] = dict(
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    **self._extra_model_kw(torch),
                )
                return AutoModelForCausalLM.from_pretrained(model_path, **kwargs)

            runtime_base = getattr(self, "_runtime_model_path", None) or settings.llm_model
            adapter_dir = settings.llm_adapter_dir
            base_path = runtime_base
            use_peft = (
                adapter_dir is not None
                and adapter_dir.is_dir()
                and self._adapter_has_weights(adapter_dir)
            )
            if use_peft:
                cfg_path = adapter_dir / "adapter_config.json"
                if cfg_path.is_file():
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    base_path = str(cfg.get("base_model_name_or_path") or base_path)
                tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir), trust_remote_code=True)
                base_model = load_causal(base_path)
                from peft import PeftModel

                model = PeftModel.from_pretrained(base_model, str(adapter_dir))
                model.eval()
            else:
                tokenizer = AutoTokenizer.from_pretrained(runtime_base, trust_remote_code=True)
                model = load_causal(runtime_base)
                model.eval()
            if tokenizer.pad_token_id is None:
                tid = getattr(tokenizer, "eod_id", None) or getattr(tokenizer, "eos_token_id", None)
                if tid is not None:
                    tokenizer.pad_token_id = tid
            self._tokenizer = tokenizer
            self._model = model

    def analyze(
        self,
        text: str,
        bert: BertResult,
        *,
        content_id: str,
        infer_time_str: str,
        preferred_prompt_scene: str | None = None,
        infer_bundle: dict[str, Any] | None = None,
    ) -> LlmResult:
        if not settings.enable_llm:
            return self._heuristic_analyze(text, bert, content_id, infer_time_str)
        try:
            from backend.app.services.infer_admin_settings import (
                get_infer_bundle,
                resolve_generation_temperature,
                resolve_llm_model_path,
                resolve_system_prompt,
            )

            bundle = infer_bundle if infer_bundle is not None else get_infer_bundle()
            resolved_path = resolve_llm_model_path(bundle)
            desired_key = resolved_path
            if desired_key != self._loaded_infer_key:
                self._tokenizer = None
                self._model = None
            self._runtime_model_path = resolved_path
            self._runtime_temperature = resolve_generation_temperature(bundle)
            system_prompt = resolve_system_prompt(
                bundle, preferred_scene=preferred_prompt_scene
            )
            scene_eff = (
                (preferred_prompt_scene or "").strip().lower()
                or _keyword_topic_scene(text, bert)
            )
            scene_block = (
                f"\n\n【本轮研判场景】{scene_eff}\n"
                "请据此撰写 scientific_error、why_sound、reader_actions，使其与正文主题一致：\n"
                "- tech：以国家标准全文公开平台、工信部/市监公开通报、厂商技术文档、CVE/NVD、可重复测评方法或学术论文原文等为主；"
                "禁止将 reader_actions 写成以「预约门诊、调整处方药、卫健委就诊」为主轴的纯医疗指南。\n"
                "- medical / health：读者建议可包含卫健、疾控、药监、学会指南与正规医院就诊等路径。\n"
                "- general：至少一条读者建议须为非医疗类权威求证路径，不得全部为药监门诊话术。\n"
            )

            self._load()
            assert self._tokenizer is not None
            assert self._model is not None
            self._loaded_infer_key = desired_key
            temp = float(self._runtime_temperature)
            report = bert.model_dump()
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "【固定字段】（下列两项必须原样写入 JSON，不得改写）：\n"
                        f'content_id: "{content_id}"\n'
                        f'infer_time: "{infer_time_str}"\n\n'
                        "请根据以下文本和 BERT 检测报告输出最终研判 JSON。\n"
                        f"【文本】\n{text}\n\n【BERT报告】\n"
                        f"{json.dumps(report, ensure_ascii=False)}"
                        f"{scene_block}"
                    ),
                },
            ]
            user_prompt = messages[1]["content"]
            if hasattr(self._model, "chat"):
                raw, _history = self._model.chat(
                    self._tokenizer,
                    user_prompt,
                    history=[("system", system_prompt)],
                    max_new_tokens=settings.llm_max_new_tokens,
                    temperature=temp,
                    top_p=0.9,
                )
            else:
                prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                inputs = self._tokenizer([prompt], return_tensors="pt").to(self._model.device)
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=settings.llm_max_new_tokens,
                    temperature=temp,
                    top_p=0.9,
                )
                generated = outputs[0][inputs["input_ids"].shape[-1] :]
                raw = self._tokenizer.decode(generated, skip_special_tokens=True)
            data = self._parse_json(raw)
            if not data:
                return self._fallback(
                    text,
                    bert,
                    "LLM 输出 JSON 解析失败",
                    content_id=content_id,
                    infer_time_str=infer_time_str,
                )
            features_list: list[str] = []
            cf_raw = data.get("core_features")
            if isinstance(cf_raw, list):
                features_list = [str(x).strip() for x in cf_raw if str(x).strip()]
            if not features_list:
                fe = data.get("features")
                if isinstance(fe, list):
                    features_list = [str(x).strip() for x in fe if str(x).strip()]
            features = features_list if features_list else list(bert.predicted_label_names)
            logical_fallacy = str(data.get("logical_fallacy", "")).strip()
            scientific_error = str(data.get("scientific_error", "")).strip()
            judgment_basis = str(data.get("judgment_basis", "")).strip()
            judgment_basis = re.sub(r"[；;]\s*阈值[:：]\s*[\d.]+\s*", "", judgment_basis)
            judgment_basis = re.sub(r"\s*阈值[:：]\s*[\d.]+\s*", "", judgment_basis).strip()
            judgment_basis = _strip_basis_noise_lines(judgment_basis)
            if not judgment_basis:
                judgment_basis = (
                    "模型未返回完整判定说明；已结合 BERT 风险档位、命中标签与总分给出结构化结论，"
                    "详见 prediction_summary_zh 与统计得分。"
                )
            why_sound = str(data.get("why_sound", "")).strip()
            why_risky = str(data.get("why_risky", "")).strip()
            reader_actions = str(data.get("reader_actions", "")).strip()
            risk_internal = self._normalize_risk_level(data.get("risk_level", "未知"))
            score_f = self._normalize_score(data.get("comprehensive_score"), bert.total_score_pct)
            raw_canon = self._canonical_llm_json(
                content_id=content_id,
                infer_time_str=infer_time_str,
                risk_normalized=risk_internal,
                comprehensive_score=score_f,
                logical_fallacy=logical_fallacy,
                scientific_error=scientific_error,
                core_features=features,
                judgment_basis=judgment_basis,
                why_sound=why_sound,
                why_risky=why_risky,
                reader_actions=reader_actions,
            )
            return LlmResult(
                risk_level=risk_internal,
                comprehensive_score=score_f,
                judgment_basis=judgment_basis,
                why_sound=why_sound,
                why_risky=why_risky,
                reader_actions=reader_actions,
                features=features,
                raw_output=raw_canon,
                logical_fallacy=logical_fallacy,
                scientific_error=scientific_error,
            )
        except Exception as exc:
            return self._fallback(
                text,
                bert,
                str(exc),
                content_id=content_id,
                infer_time_str=infer_time_str,
            )

    def _heuristic_analyze(
        self, text: str, bert: BertResult, content_id: str, infer_time_str: str
    ) -> LlmResult:
        """无本地 Qwen 权重时的结构化研判层，对外 raw_output 仍为完整 JSON。"""
        if bert.risk_level == "高":
            risk = "高风险"
        elif bert.risk_level == "中":
            risk = "中风险"
        elif bert.risk_level == "低":
            risk = "低风险"
        else:
            risk = "未知"
        features = list(bert.predicted_label_names)
        score_f = self._normalize_score(bert.total_score_pct, bert.total_score_pct)
        basis_parts: list[str] = []
        if not bert.available:
            basis_parts.append(f"BERT 不可用：{bert.error or '未知错误'}")
        if bert.available:
            basis_parts.append(f"BERT 基础风险为{bert.risk_level}，综合得分约 {score_f}/100")
            if features:
                basis_parts.append(f"显性特征包括：{'、'.join(features)}")
            if "癌" in text or "治愈" in text or "根治" in text or "预防" in text:
                basis_parts.append("文本涉及医疗健康效果承诺，需要提高风险关注")
        judgment_basis = (
            "；".join(basis_parts)
            if basis_parts
            else "启发式研判：依据 BERT 统计输出给出结构化结论（未加载本地大模型）。"
        )
        if risk == "低风险" and not features:
            lf, se = "无", "无"
        else:
            lf = _fallback_logical(features)
            se = "无" if risk == "低风险" else _fallback_scientific(
                features=features, risk=heuristic_risk_label_to_std(risk)
            )
        ws = (
            "启发式路径下，统计模型未给出强烈伪科普命中；若正文为常识科普且引用权威来源，则与当前档位一致。"
            if risk == "低风险"
            else "未加载大模型，无法做逐句论证；以下说明来自 BERT 统计与内置规则，可能弱于完整 LLM 研判。"
        )
        scene = _keyword_topic_scene(text, bert)
        if risk == "低风险":
            wr = (
                "若您看到与国标或厂商技术文档明显冲突的性能承诺，仍应提高警觉并自行核实。"
                if scene == "tech"
                else "若您看到与权威指南明显冲突的疗效承诺，仍应提高警觉并自行核实。"
            )
        else:
            wr = f"主要风险信号来自统计模型：{('、'.join(features)) if features else '需结合全文复核论证链条'}。"
        ra = _fallback_reader_actions(text, bert, risk, None)
        raw = self._canonical_llm_json(
            content_id=content_id,
            infer_time_str=infer_time_str,
            risk_normalized=risk,
            comprehensive_score=score_f,
            logical_fallacy=lf,
            scientific_error=se,
            core_features=features,
            judgment_basis=judgment_basis,
            why_sound=ws,
            why_risky=wr,
            reader_actions=ra,
        )
        return LlmResult(
            available=True,
            risk_level=risk,
            comprehensive_score=score_f,
            judgment_basis=judgment_basis,
            why_sound=ws,
            why_risky=wr,
            reader_actions=ra,
            features=features,
            raw_output=raw,
            logical_fallacy=lf,
            scientific_error=se,
        )


llm_service = LlmService()
