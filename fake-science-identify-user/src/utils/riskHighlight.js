/**
 * 原文高风险用语高亮：结合内置话术库与命中特征标签做子串/正则匹配。
 * 返回分段数组供模板 v-for，避免 v-html 整段注入不可信 HTML。
 */

/** 常见伪科普、绝对化与疗效夸大话术（可按业务扩充） */
const BUILTIN_REGEXES = [
  /据传临床都在用/g,
  /临床都在用/g,
  /见效很快/g,
  /立竿见影/g,
  /当天见效/g,
  /包治百病/g,
  /百分之百(?:治愈|有效)/g,
  /绝不复发/g,
  /祖传秘方/g,
  /无效退款/g,
  /一盒见效/g,
  /三天见效/g,
  /七天根治/g,
  /纯天然无副作用/g,
  /医生都在推荐/g
]

/** 按 core_features / BERT 标签名追加的弱提示词（在正文做子串检索） */
const FEATURE_EXTRA_TERMS = {
  绝对化用语: ['一定', '必须', '肯定', '彻底', '永不', '百分百', '百分之百', '根治', '治愈'],
  虚假疗效: ['见效', '痊愈', '好转', '奇效', '神药'],
  权威伪造: ['据传', '听说', '有人说', '专家表示'],
  标点异常: [], // 样式层面难展示，依赖正则
  术语堆砌: [],
  数据篡改: ['%', '％']
}

/**
 * @param {string} text 原始正文
 * @param {{ core_features?: string[], bert_labels?: string[] }} hints
 * @returns {{ mark: boolean, text: string }[]}
 */
export function buildRiskHighlightSegments(text, hints = {}) {
  const raw = String(text || '')
  if (!raw) return []

  const ranges = []

  const pushRange = (start, end) => {
    if (end <= start) return
    ranges.push({ start, end })
  }

  for (const re of BUILTIN_REGEXES) {
    const flags = re.flags.includes('g') ? re.flags : re.flags + 'g'
    const rg = new RegExp(re.source, flags)
    let m
    while ((m = rg.exec(raw)) !== null) {
      pushRange(m.index, m.index + m[0].length)
      if (m[0].length === 0) rg.lastIndex++
    }
  }

  const labels = [
    ...(hints.core_features || []),
    ...(hints.bert_labels || [])
  ].map((s) => String(s || '').trim()).filter(Boolean)

  const seenTerms = new Set()
  for (const lb of labels) {
    const extras = FEATURE_EXTRA_TERMS[lb]
    if (!extras) continue
    for (const term of extras) {
      if (seenTerms.has(term)) continue
      seenTerms.add(term)
      let from = 0
      while (from < raw.length) {
        const idx = raw.indexOf(term, from)
        if (idx === -1) break
        pushRange(idx, idx + term.length)
        from = idx + term.length
      }
    }
  }

  if (!ranges.length) return [{ mark: false, text: raw }]

  ranges.sort((a, b) => a.start - b.start || b.end - a.end)

  const merged = []
  for (const r of ranges) {
    const last = merged[merged.length - 1]
    if (!last || r.start > last.end) merged.push({ ...r })
    else last.end = Math.max(last.end, r.end)
  }

  const segments = []
  let pos = 0
  for (const r of merged) {
    if (pos < r.start) segments.push({ mark: false, text: raw.slice(pos, r.start) })
    segments.push({ mark: true, text: raw.slice(r.start, r.end) })
    pos = r.end
  }
  if (pos < raw.length) segments.push({ mark: false, text: raw.slice(pos) })
  return segments
}
