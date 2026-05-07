"""由流水线中间结果组装 StandardJudgmentOutput（含回退逻辑）。"""
from __future__ import annotations

import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Literal
from zoneinfo import ZoneInfo

from backend.app.core.config import settings
from backend.app.schemas.analyze import AnalyzeResponse, BertResult, FinalResult, LlmResult
from backend.app.schemas.standard_judgment import StandardJudgmentOutput

StandardRiskLevel = Literal["高", "中", "低"]


def heuristic_risk_label_to_std(risk_label: str) -> StandardRiskLevel:
    """启发式 / LLM 返回的「高风险」等映射为 standard_judgment 用的档位。"""
    s = (risk_label or "").strip()
    if s.startswith("低") or "低风险" in s:
        return "低"
    if s.startswith("高") or "高风险" in s:
        return "高"
    return "中"


_INTERNAL_ERR_MARKERS = re.compile(
    r"(cannot\s+import|importerror|modulenotfounderror|traceback\s*\(|"
    r"site-packages|\.py\",\s*line\s*\d+|:\\users\\|/lib/python\d)",
    re.IGNORECASE,
)


def _text_looks_like_internal_stack(s: str) -> bool:
    t = (s or "").strip()
    if len(t) < 24:
        return False
    return bool(_INTERNAL_ERR_MARKERS.search(t))


def _infer_tz() -> ZoneInfo:
    try:
        return ZoneInfo(settings.infer_time_zone)
    except Exception:
        return ZoneInfo("Asia/Shanghai")


def _format_infer_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_infer_tz())
    else:
        dt = dt.astimezone(_infer_tz())
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_infer_time(dt: datetime | None = None) -> str:
    """供流水线 / LLM 提示词使用的推理时间字符串（与 standard_judgment.infer_time 同格式）。"""
    at = dt if dt is not None else datetime.now(_infer_tz())
    return _format_infer_time(at)


def _clean_basis(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"[；;]\s*阈值[:：]\s*[\d.]+\s*", "", text)
    t = re.sub(r"\s*阈值[:：]\s*[\d.]+\s*", "", t)
    return t.strip()


def _basis_is_bert_style_stats(text: str) -> bool:
    """是否为 BERT prediction_summary_zh 式机读句（不应直接作为对外判定依据主体）。"""
    b = (text or "").strip()
    if not b:
        return False
    if re.search(r"风险[高中低][；;，,]\s*命中标签", b):
        return True
    if "命中标签" in b and re.search(r"总得分\s*[:：]?\s*[\d.]+\s*/\s*100", b):
        return True
    return False


def _basis_embeds_substantial_source(basis: str, source_text: str) -> bool:
    """模型是否把输入正文粘进依据（设计文档要求依据为总结，而非原文复述）。"""
    st = (source_text or "").strip()
    if len(st) < 12:
        return False
    b = basis or ""
    if st in b:
        return True
    head = st[: min(120, len(st))].strip()
    return len(head) >= 12 and head in b


def _basis_should_force_narrative(basis: str, source_text: str) -> bool:
    b = (basis or "").strip()
    if not b:
        return False
    if _basis_is_bert_style_stats(b):
        return True
    if _basis_embeds_substantial_source(b, source_text):
        return True
    return False


def _basis_too_short(text: str) -> bool:
    s = (text or "").strip()
    return len(s) < 24 or s.isdigit()


def _strip_basis_noise_lines(text: str) -> str:
    """去掉模型常见的无效独行编号（如单独一行的「1」），避免前端拆行后首条像乱码。"""
    lines = []
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        if re.fullmatch(r"\d+[\.、．)]?\s*", s):
            continue
        if re.fullmatch(r"[（(]?\d+[）)]?\s*", s):
            continue
        lines.append(s)
    return "\n".join(lines) if lines else (text or "").strip()


def _expand_judgment_basis(
    risk: StandardRiskLevel,
    feats: list[str],
    bert: BertResult,
    score_f: float,
    bert_tag_summary: str,
) -> str:
    tags = "、".join(feats[:8]) if feats else "无显性命中维度"
    bt = bert_tag_summary or "无"
    if risk == "低":
        return (
            f"该内容在伪科普显性特征上未见显著命中（核心特征维度：{tags}），"
            f"BERT 侧提示标签为「{bt}」，综合得分约 {score_f}/100，"
            f"文本逻辑与可核查科学表述整体一致或未见明显冲突，故判定为低风险档科普内容；"
            f"若涉及个体诊疗，仍需以医疗机构与权威指南为准。"
        )
    if risk == "高":
        return (
            f"综合判定为高风险：BERT 侧命中「{tags}」等维度，综合得分约 {score_f}/100；"
            f"存在疗效承诺绝对化、事实夸大或来源不可信等模式，建议读者严格核查来源并避免据此决策。"
        )
    return (
        f"综合判定为中风险：BERT 标签「{bt}」，特征维度「{tags}」，得分约 {score_f}/100；"
        f"论证链条或事实表述存在一定跳跃与不确定性，建议对关键论断进行交叉验证。"
    )


def _default_three_pillars(
    risk: StandardRiskLevel,
    feats: list[str],
    bert_tag_summary: str,
    score_f: float,
    lf: str,
    se: str,
) -> tuple[str, str, str]:
    """当 LLM 未返回 why_sound / why_risky / reader_actions 时的可读兜底。"""
    tags = "、".join(feats[:8]) if feats else "无显性命中维度"
    bt = bert_tag_summary or "无"
    if risk == "低":
        return (
            f"综合得分约 {score_f}/100，BERT 提示标签「{bt}」，在伪科普显性维度上未见强命中（{tags}），"
            f"故在自动研判框架下更偏向「科普表述整体可接受」一侧。",
            f"仍须注意：任何网络科普都不能替代个体化诊疗；若正文含绝对化疗效承诺，即使当前为低风险也应复核。",
            "优先对照国家卫健委、疾控中心或三甲医院公开科普；涉及用药、剂量或停药请面询执业医师；勿仅凭短视频做健康决策。",
        )
    if risk == "高":
        return (
            "在当前自动化证据下，难以找到可采信的权威出处或严谨对照来支撑文中的关键疗效/机理断言，"
            "故不宜将正文视为「已证实的科学结论」。"
            "统计模型反映的是用语与论证模式上的风险信号，并不等同于对作者主观故意或法律责任的认定；"
            "在未核验原始论文、注册研究与监管通报前，读者宜把本页结论当作「优先核查清单」，而非可直接采纳的诊疗方案。",
            f"BERT 提示「{bt}」，显性特征包含「{tags}」，综合得分约 {score_f}/100。"
            f"论证侧可概括为：{lf}。"
            f"科学事实与证据层级侧：{se}。"
            "请结合全文语境理解：上述摘要无法覆盖每一个具体句子，若正文含个案经验或「内部方案」类表述，更需对照大样本研究与指南结论。",
            "请勿转发或截图二次传播以免误导他人；"
            "建议在国家卫健委、疾控中心官网或中华医学会公开指南中检索与正文主题对应的关键词；"
            "涉及用药、停药、剂量或替代疗法的，务必面询执业医师或药师并携带完整病史；"
            "可在国家药监局网站核对药品批准信息与说明书警示；"
            "若正文引用「研究」「数据」，请用原始论文数据库（如 PubMed）核对题目、作者与结论是否被曲解；"
            "对声称「快速起效」「根治」类表述保持高度警觉，以随机对照试验与指南推荐等级为准绳。",
        )
    return (
        f"综合得分约 {score_f}/100，BERT 标签「{bt}」，特征维度「{tags}」表明文本在论证方式或信源呈现上存在可识别的薄弱点；"
        f"在未见相反权威材料前，尚不足以在自动化框架下将全文盖棺为「伪科普」，但亦不宜无保留采信。"
        f"换言之：当前信号更像「黄灯」——提醒放慢阅读、逐项核实，而非绿灯放行。",
        f"与上述标签相关的论证侧问题可概括为：{lf}。"
        f"科学事实与证据链侧需要读者重点把关的是：{se}。"
        "若正文含疗效承诺、个案经验上升为普遍结论、或引用不明「专家/内部经验」，请回到原文标出具体句子，再与公开指南逐条对照。",
        "建议优先查阅国家卫健委与疾控中心发布的疾病科普与就诊提示；"
        "在中华医学会或各省级医学会网站上检索该病种的临床指南或专家共识；"
        "对涉及治疗决策的内容，请预约正规医院对应科室门诊（可按症状选择全科初筛后再转诊专科）；"
        "勿根据社交媒体短文自行购药或调整正在使用的处方药；"
        "若正文含数据或治愈率，请检索原始出处并核对是否断章取义；"
        "可把本页作为「提问清单」带至门诊，请医生结合检查结果解读风险与获益。",
    )


def _zh_text_similarity(a: str, b: str) -> float:
    x, y = (a or "").strip(), (b or "").strip()
    if not x or not y:
        return 0.0
    return SequenceMatcher(None, x, y).ratio()


def _longest_common_substring_len(a: str, b: str) -> int:
    """两段话是否复制了同一句子（中文字符级公共子串长度）。"""
    x, y = (a or "").strip(), (b or "").strip()
    if not x or not y:
        return 0
    na, nb = len(x), len(y)
    if na * nb > 640_000:
        return 0
    best = 0
    prev = [0] * (nb + 1)
    for i in range(na):
        cur = [0] * (nb + 1)
        cx = x[i]
        for j in range(nb):
            if cx == y[j]:
                v = prev[j] + 1
                cur[j + 1] = v
                if v > best:
                    best = v
        prev = cur
    return best


def _why_sound_risky_too_redundant(why_sound: str, why_risky: str) -> bool:
    """模型常把同一套「标签说明」复制进两栏，导致读起来像复读。"""
    ws, wr = (why_sound or "").strip(), (why_risky or "").strip()
    if len(ws) < 22 or len(wr) < 22:
        return False
    if _zh_text_similarity(ws, wr) >= 0.48:
        return True
    if _longest_common_substring_len(ws, wr) >= 16:
        return True
    # 同一句式起笔（如「某某标签表明…」）
    head = 26
    if len(ws) >= head and len(wr) >= head and ws[:head] == wr[:head]:
        return True
    return False


def _resplit_why_sound_after_redundancy(
    risk: StandardRiskLevel,
    feats: list[str],
    bert_tag_summary: str,
    score_f: float,
    lf: str,
    se: str,
    why_risky: str,
) -> str:
    """保留 why_risky，重写 why_sound 为「证据边界 / 为何不直接定性」视角，避免与风险段同构。"""
    d_ws, _d_wr, _ = _default_three_pillars(risk, feats, bert_tag_summary, score_f, lf, se)
    if _zh_text_similarity(d_ws, why_risky) < 0.42 and _longest_common_substring_len(d_ws, why_risky) < 14:
        return d_ws
    if risk == "高":
        return (
            "在未核验原始论文、注册研究与监管通报前，自动化结论不包含对作者主观故意的法律评价；"
            "读者宜把正文视为「待核实信息」，而非可直接采纳的医疗或投资依据。"
        )
    if risk == "低":
        return (
            "当前提示主要来自统计语义特征：在未见其它信源互证前，适合作为阅读警觉而非对个人的定性结论。"
        )
    return (
        "统计标签与得分反映的是用语与论证模式上的风险提示，并不等同于正文每一句都已不实；"
        "在未核对原始出处与权威机构说法前，宜把上栏「为何存疑」当作提高警觉的阅读指引，而非终局裁决。"
    )


def _dedupe_identical_semicolon_segments(s: str) -> str:
    """模型常把同一句用 ;/； 重复多遍；合并为一句便于阅读与后续判定。"""
    t = (s or "").strip()
    if not t:
        return ""
    parts = re.split(r"\s*[;；]\s*", t)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return t
    out: list[str] = []
    for p in parts:
        if not out or out[-1] != p:
            out.append(p)
    return "；".join(out)


def _why_risky_is_bert_methodology_stub(s: str) -> bool:
    """大模型用「依据 BERT 预测」空转句占满 why_risky，无正文具体指认；应清空以走模板兜底。"""
    raw = (s or "").strip()
    if not raw:
        return False
    parts = re.split(r"\s*[;；]\s*", raw)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2 and len({p.lower() for p in parts}) == 1 and "bert" in parts[0].lower():
        return True
    t = _dedupe_identical_semicolon_segments(raw)
    tl = t.lower()
    if "bert" not in tl:
        return False
    # 合规输出常会短引号摘原文；纯元描述通常没有角引号摘句
    if "「" in t or "『" in t:
        return False
    if len(t) > 200:
        return False
    if any(
        x in t
        for x in (
            "风险评估基于",
            "基于BERT模型",
            "基于bert模型",
            "统计模型预测",
        )
    ):
        return True
    # 短句且同时出现「模型 + 预测结果」类元说明，与常见合规摘句区分
    return "预测结果" in t and ("bert模型" in tl or "bert 模型" in tl) and len(t) < 96


def _is_prompt_echo_why_sound(s: str) -> bool:
    """模型把系统提示里的小标题原样填进 JSON。"""
    t = (s or "").strip()
    if not t or len(t) > 200:
        return False
    if "只写" in t or "「相对成立" in t or "本说明" in t:
        return True
    if "相对成立" in t and "证据边界" in t and ("一棍子" in t or "为何不直接" in t):
        return True
    return False


def _is_prompt_echo_why_risky(s: str) -> bool:
    t = (s or "").strip()
    if not t or len(t) > 200:
        return False
    if "只写" in t:
        return True
    if "具体哪里可疑" in t and "怎样误导" in t and len(t) < 120:
        return True
    return False


def _is_prompt_echo_reader_actions(s: str) -> bool:
    """如：查阅权威机构信息;勿转发… 无动词、无句号，像提纲。"""
    t = (s or "").strip()
    if not t:
        return False
    if len(t) > 260:
        return False
    if "只写" in t or "可执行" in t and "动词" in t:
        return True
    has_soft_verb = any(
        x in t
        for x in (
            "请",
            "建议",
            "宜",
            "应当",
            "可优先",
            "请勿",
            "勿要",
            "咨询",
            "面询",
            "检索",
            "对照",
            "核实",
            "查证",
        )
    )
    if len(t) < 140 and ("；" in t or ";" in t) and t.count("。") == 0 and not has_soft_verb:
        return True
    if len(t) < 42 and t.count("。") == 0:
        return True
    return False


def infer_completed_at() -> datetime:
    """流水线结束时刻（使用 LINGJIAN_INFER_TZ）。"""
    return datetime.now(_infer_tz())


def _resolve_standard_risk(final: FinalResult, bert: BertResult) -> StandardRiskLevel:
    r = (final.risk_level or "").strip()
    if r.startswith("高") or r == "高风险":
        return "高"
    if r.startswith("低") or r == "低风险":
        return "低"
    if r.startswith("中") or r == "中风险":
        return "中"
    br = (bert.risk_level or "").strip()
    if br == "高":
        return "高"
    if br == "低":
        return "低"
    if br == "中":
        return "中"
    return "中"


def _lf_se_is_placeholder_none(s: str) -> bool:
    """模型常把「无」当作模板输出；与空串一样需在非低风险场景下用兜底文案替换。"""
    t = (s or "").strip().rstrip("。").strip()
    if not t:
        return True
    if len(t) > 24:
        return False
    return t in ("无", "没有", "暂无", "无明显问题", "未发现", "无。", "没有。")


def _fallback_logical(features: list[str]) -> str:
    if not features:
        return "统计模型提示论证表述可能存在不严谨之处，具体谬误类型需结合全文语境复核。"
    tail = "、".join(features[:5])
    return (
        f"与「{tail}」等表述相关的论证，易把个案传闻、修辞包装与经核验的医学结论混为一谈；"
        f"常见风险包括夸大疗效、来源不明的「权威」背书或数据剪裁，需回到原文与可核查出处逐项核对。"
    )


def _fallback_scientific(*, features: list[str], risk: StandardRiskLevel) -> str:
    if risk == "高" and any("疗效" in str(x) or "治愈" in str(x) or "预防" in str(x) for x in features):
        return (
            "若正文含治疗、预防或「有效/治愈」等疗效断言，须有临床试验、指南或监管机构公开材料支撑；"
            "仅有口号式承诺或非正规渠道背书时，证据层级不足，不能作为用药或停药依据。"
        )
    return (
        "单次自动研判无法替代跨学科事实核查；若涉及疗效、疾病预防或机理断言，"
        "请以卫健委、药监局、WHO 等权威机构公开信息与指南为准。"
    )


def build_standard_judgment(
    *,
    content_id: str,
    bert: BertResult,
    llm: LlmResult,
    final: FinalResult,
    completed_at: datetime | None = None,
    source_text: str = "",
) -> StandardJudgmentOutput:
    """组装面向前端的标准 JSON；`completed_at` 缺省时取当前时区的「此刻」。

    `source_text` 用于识别「判定依据」是否错误粘贴了输入正文或 BERT 机读摘要，必要时改写为书面叙事段落。
    """
    at = completed_at if completed_at is not None else datetime.now(_infer_tz())
    if at.tzinfo is None:
        at = at.replace(tzinfo=_infer_tz())

    risk = _resolve_standard_risk(final, bert)
    score_f = round(float(max(0.0, min(100.0, final.score))), 1)
    feats = list(final.features) if final.features else list(llm.features)
    bert_tag_summary = (
        "、".join(bert.predicted_label_names[:12]) if bert.predicted_label_names else "无"
    )

    lf = (llm.logical_fallacy or "").strip()
    need_lf_fallback = (not lf) or (
        _lf_se_is_placeholder_none(lf) and (risk != "低" or bool(feats))
    )
    if need_lf_fallback:
        if risk == "低" and not feats:
            lf = "无"
        else:
            lf = _fallback_logical(feats)

    se = (llm.scientific_error or "").strip()
    need_se_fallback = (not se) or (_lf_se_is_placeholder_none(se) and risk != "低")
    if need_se_fallback:
        if risk == "低":
            se = "无"
        else:
            se = _fallback_scientific(features=feats, risk=risk)

    basis = (final.basis or "").strip() or (llm.judgment_basis or "").strip()
    basis = _strip_basis_noise_lines(basis)
    basis = _clean_basis(basis)
    if not basis:
        basis = _clean_basis((bert.prediction_summary_zh or "").strip())
    if not basis:
        basis = "基于多模型融合的综合风险提示。"
    if _basis_should_force_narrative(basis, source_text):
        basis = _expand_judgment_basis(risk, feats, bert, score_f, bert_tag_summary)
    elif _basis_too_short(basis):
        basis = _expand_judgment_basis(risk, feats, bert, score_f, bert_tag_summary)
    bl = basis.lower()
    if "site-packages" in bl or "cannot import" in bl or _text_looks_like_internal_stack(basis):
        basis = _expand_judgment_basis(risk, feats, bert, score_f, bert_tag_summary)

    why_sound = (llm.why_sound or "").strip()
    why_risky = _dedupe_identical_semicolon_segments((llm.why_risky or "").strip())
    reader_actions = (llm.reader_actions or "").strip()
    if _why_risky_is_bert_methodology_stub(why_risky):
        why_risky = ""
    if _is_prompt_echo_why_sound(why_sound):
        why_sound = ""
    if _is_prompt_echo_why_risky(why_risky):
        why_risky = ""
    if _is_prompt_echo_reader_actions(reader_actions):
        reader_actions = ""
    if _text_looks_like_internal_stack(why_risky):
        why_risky = ""
    if _text_looks_like_internal_stack(why_sound):
        why_sound = ""
    if _text_looks_like_internal_stack(reader_actions):
        reader_actions = ""
    if not why_sound or not why_risky or not reader_actions:
        d_ws, d_wr, d_ra = _default_three_pillars(risk, feats, bert_tag_summary, score_f, lf, se)
        why_sound = why_sound or d_ws
        why_risky = why_risky or d_wr
        reader_actions = reader_actions or d_ra

    if _why_sound_risky_too_redundant(why_sound, why_risky):
        why_sound = _resplit_why_sound_after_redundancy(
            risk, feats, bert_tag_summary, score_f, lf, se, why_risky
        )

    return StandardJudgmentOutput(
        content_id=content_id,
        risk_level=risk,
        comprehensive_score=score_f,
        logical_fallacy=lf,
        scientific_error=se,
        core_features=feats,
        judgment_basis=basis,
        why_sound=why_sound,
        why_risky=why_risky,
        reader_actions=reader_actions,
        infer_time=_format_infer_time(at),
    )


def rehydrate_standard_judgment(resp: AnalyzeResponse) -> AnalyzeResponse:
    """从库读取等场景：用当前脱敏与模板规则重建 standard_judgment，保留原 infer_time 字符串。Redis 命中路径不再调用本函数，直接返回缓存 JSON。"""
    s = (resp.standard_judgment.infer_time or "").strip()
    at: datetime | None = None
    if s:
        try:
            at = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=_infer_tz())
        except ValueError:
            at = None
    if at is None:
        at = infer_completed_at()
    sj = build_standard_judgment(
        content_id=resp.content_id,
        bert=resp.bert,
        llm=resp.llm,
        final=resp.final,
        completed_at=at,
        source_text=resp.input_text,
    )
    return resp.model_copy(update={"standard_judgment": sj})
