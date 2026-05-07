import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import { V1 } from '@/api/v1/endpoints'

/** 后端 standard_judgment.risk_level 为高/中/低，卡片组件使用英文档位 */
function mapRiskLevel(zh) {
  const m = { 高: 'high', 中: 'middle', 低: 'low' }
  if (zh && m[zh]) return m[zh]
  const s = String(zh || '').toLowerCase()
  if (s.includes('high') || s.includes('高')) return 'high'
  if (s.includes('mid') || s.includes('中')) return 'middle'
  if (s.includes('low') || s.includes('低')) return 'low'
  return 'low'
}

/** AnalyzeResponse → 结果页所需字段 */
function normalizeAnalyze(raw) {
  const sj = raw.standard_judgment || {}
  const riskZh = sj.risk_level || raw.final?.risk_level || raw.llm?.risk_level || '低'

  const logical_fallacy = String(sj.logical_fallacy ?? raw.llm?.logical_fallacy ?? '').trim()
  const scientific_error = String(sj.scientific_error ?? raw.llm?.scientific_error ?? '').trim()
  const why_sound = String(sj.why_sound ?? raw.llm?.why_sound ?? '').trim()
  const why_risky = String(sj.why_risky ?? raw.llm?.why_risky ?? '').trim()
  const reader_actions = String(sj.reader_actions ?? raw.llm?.reader_actions ?? '').trim()
  const core_features = Array.isArray(sj.core_features)
    ? sj.core_features.map((x) => String(x).trim()).filter(Boolean)
    : [...(raw.final?.features || raw.llm?.features || [])].filter(Boolean)

  /** 综合判定依据段落（与结构化字段并列展示） */
  let judgment_summary = String(sj.judgment_basis ?? '').trim()
  if (!judgment_summary) {
    judgment_summary = String(raw.llm?.judgment_basis || raw.final?.basis || '').trim()
  }

  /** 分享图等兼容：拆成多行要点 */
  let judgment_basis = []
  if (logical_fallacy) judgment_basis.push(`【逻辑谬误】${logical_fallacy}`)
  if (scientific_error) judgment_basis.push(`【科学事实错误】${scientific_error}`)
  if (why_sound) judgment_basis.push(`【为何仍可能成立】${why_sound}`)
  if (why_risky) judgment_basis.push(`【为何存疑】${why_risky}`)
  if (reader_actions) judgment_basis.push(`【建议您】${reader_actions}`)
  if (core_features.length) judgment_basis.push(`【核心特征】${core_features.join('、')}`)
  if (judgment_summary) judgment_basis.push(`【综合判定】${judgment_summary}`)
  if (!judgment_basis.length) {
    if (judgment_summary) judgment_basis = [judgment_summary]
    else {
      const basisStr = raw.llm?.judgment_basis || raw.final?.basis || ''
      if (basisStr) {
        judgment_basis = String(basisStr)
          .split(/\n/)
          .map((s) => s.trim())
          .filter((s) => s && !/^\d+\.?$/.test(s))
      }
      if (!judgment_basis.length) judgment_basis = [...core_features]
    }
  }

  const rawScore = sj.comprehensive_score ?? raw.final?.score ?? raw.llm?.comprehensive_score ?? 0
  const llm_score = typeof rawScore === 'number' ? rawScore : parseFloat(rawScore) || 0

  const bert_predicted_labels = raw.bert?.predicted_label_names || []

  const ocrText = String(raw.ocr?.text ?? '').trim()
  const inputText = String(raw.input_text ?? '').trim()
  const content_text = [inputText, ocrText].filter(Boolean).join('\n\n')

  return {
    content_id: raw.content_id,
    risk_level: mapRiskLevel(riskZh),
    llm_score,
    logical_fallacy,
    scientific_error,
    why_sound,
    why_risky,
    reader_actions,
    core_features,
    judgment_summary,
    judgment_basis,
    content_text,
    image_list: [],
    bert_predicted_labels,
    human_review: normalizeHumanReview(raw.human_review),
    _raw: raw
  }
}

function normalizeHumanReview(hr) {
  if (!hr || typeof hr !== 'object') return null
  const status = String(hr.status || '').trim()
  if (!status) return null
  return {
    status,
    summary_zh: String(hr.summary_zh || '').trim(),
    note: hr.note != null && String(hr.note).trim() ? String(hr.note).trim() : null,
    reviewed_at: hr.reviewed_at != null ? String(hr.reviewed_at) : null
  }
}

function normalizeHistoryContentIds(contentIds) {
  return (contentIds || [])
    .map((x) => {
      if (x == null) return ''
      if (typeof x === 'object' && x.content_id != null) return String(x.content_id).trim()
      return String(x).trim()
    })
    .filter(Boolean)
}

export const useIdentifyStore = defineStore('identify', () => {
  const currentContentId = ref('')
  const currentResult = ref({})
  const historyList = ref([])
  const totalCount = ref(0)
  /** content_id → 归一化结果（会话内缓存 + 可与服务端对齐） */
  const resultCache = ref({})

  const submitIdentify = async (formData) => {
    const type = formData.get('content_type')

    if (type === 'text') {
      const text = String(formData.get('content_text') || '').trim()
      const skip = formData.get('skip_infer_cache') === '1'
      const body = { text }
      if (skip) body.skip_infer_cache = true
      const res = await request.post(V1.ANALYZE_TEXT, body)
      const normalized = normalizeAnalyze(res.data)
      resultCache.value[normalized.content_id] = normalized
      currentContentId.value = normalized.content_id
      currentResult.value = normalized
      return { content_id: normalized.content_id }
    }

    if (type === 'image') {
      const files = formData.getAll('image_files')
      if (!files?.length) throw new Error('缺少图片')
      if (files.length > 1) {
        ElMessage.warning('后端单次仅分析一张图，已使用第一张')
      }
      const fd = new FormData()
      fd.append('file', files[0])
      if (formData.get('skip_infer_cache') === '1') {
        fd.append('skip_infer_cache', 'true')
      }
      const res = await request.post(V1.ANALYZE_IMAGE, fd)
      const normalized = normalizeAnalyze(res.data)
      resultCache.value[normalized.content_id] = normalized
      currentContentId.value = normalized.content_id
      currentResult.value = normalized
      return { content_id: normalized.content_id }
    }

    if (type === 'mix') {
      const text = String(formData.get('content_text') || '')
      const files = formData.getAll('image_files')
      if (!files?.length) {
        if (text.trim()) {
          const res = await request.post(V1.ANALYZE_TEXT, { text: text.trim() })
          const normalized = normalizeAnalyze(res.data)
          resultCache.value[normalized.content_id] = normalized
          currentContentId.value = normalized.content_id
          currentResult.value = normalized
          return { content_id: normalized.content_id }
        }
        throw new Error('图文混合需要你至少上传一张图片')
      }
      if (files.length > 1) {
        ElMessage.warning('后端单次仅分析一张图，已使用第一张')
      }
      const fd = new FormData()
      fd.append('text', text)
      fd.append('file', files[0])
      if (formData.get('skip_infer_cache') === '1') {
        fd.append('skip_infer_cache', 'true')
      }
      const res = await request.post(V1.ANALYZE_MIXED, fd)
      const normalized = normalizeAnalyze(res.data)
      resultCache.value[normalized.content_id] = normalized
      currentContentId.value = normalized.content_id
      currentResult.value = normalized
      return { content_id: normalized.content_id }
    }

    throw new Error('未知的内容类型')
  }

  const getIdentifyResult = async (contentId) => {
    try {
      const res = await request.get(V1.ANALYZE_RESULT(contentId))
      const normalized = normalizeAnalyze(res.data)
      resultCache.value[contentId] = normalized
      currentResult.value = normalized
      return normalized
    } catch {
      ElMessage.warning('未找到该识别记录或无权查看')
      currentResult.value = {}
      return {}
    }
  }

  const getHistoryList = async (params = {}) => {
    const res = await request.get(V1.ANALYZE_HISTORY, {
      params: {
        page: params.page ?? 1,
        page_size: params.size ?? 10,
        risk_level: params.risk_level || undefined,
        content_type: params.content_type || undefined,
        start_date: params.start_date || undefined,
        end_date: params.end_date || undefined
      }
    })
    historyList.value = res.data.list || []
    totalCount.value = res.data.total ?? 0
    return res.data
  }

  const deleteHistory = async (contentIds) => {
    const ids = normalizeHistoryContentIds(contentIds)
    if (ids.length === 0) return
    await request.post(V1.ANALYZE_HISTORY_DELETE, { content_ids: ids })
    for (const id of ids) {
      delete resultCache.value[id]
    }
  }

  const clearAllHistory = async () => {
    await request.delete(V1.ANALYZE_HISTORY_ALL)
    historyList.value = []
    totalCount.value = 0
    resultCache.value = {}
  }

  const toggleCollect = async () => {
    ElMessage.info('后端暂无收藏接口')
  }

  const getCollectList = async () => {
    return { list: [], total: 0 }
  }

  return {
    currentContentId,
    currentResult,
    historyList,
    totalCount,
    resultCache,
    submitIdentify,
    getIdentifyResult,
    getHistoryList,
    deleteHistory,
    clearAllHistory,
    toggleCollect,
    getCollectList
  }
})
