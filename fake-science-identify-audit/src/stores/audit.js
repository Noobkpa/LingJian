import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request, { rawClient } from '@/utils/request'
import { useUserStore } from '@/stores/user'
import { V1 } from '@/api/v1/endpoints'

function zhRiskToUi(z) {
  const s = String(z || '')
  if (s === '高') return 'high'
  if (s === '中') return 'middle'
  return 'low'
}

function mapAnalyzeToTask(p) {
  const sj = p.standard_judgment || {}
  const lines = []
  if (sj.logical_fallacy) lines.push(`逻辑谬误：${sj.logical_fallacy}`)
  if (sj.scientific_error) lines.push(`科学事实：${sj.scientific_error}`)
  if (sj.why_sound) lines.push(`为何仍可能成立：${sj.why_sound}`)
  if (sj.why_risky) lines.push(`为何存疑：${sj.why_risky}`)
  if (sj.reader_actions) lines.push(`建议：${sj.reader_actions}`)
  if (sj.core_features?.length) lines.push(`核心特征：${sj.core_features.join('、')}`)
  if (sj.judgment_basis) lines.push(`综合依据：${sj.judgment_basis}`)
  const modality = p.modality
  const ct =
    modality === 'mixed' ? 'mix' : modality === 'image' ? 'image' : 'text'
  return {
    content_id: p.content_id,
    content_type: ct,
    risk_level: zhRiskToUi(sj.risk_level),
    llm_score: sj.comprehensive_score ?? p.final?.score ?? 0,
    content_text: [String(p.input_text ?? '').trim(), String(p.ocr?.text ?? '').trim()]
      .filter(Boolean)
      .join('\n\n'),
    upload_time: sj.infer_time || '',
    upload_user: '-',
    judgment_basis: lines.length ? lines : sj.judgment_basis ? [sj.judgment_basis] : []
  }
}

export const useAuditStore = defineStore('auditTask', () => {
  const taskList = ref([])
  const historyList = ref([])
  const currentTask = ref(null)
  const totalCount = ref(0)
  /** 两个审核历史接口均 404 时为 true，用于页面内提示（不弹全局 Message） */
  const historyUnavailable = ref(false)

  const dismissHistoryUnavailable = () => {
    historyUnavailable.value = false
  }

  const getTaskList = async (params) => {
    const page = params?.page ?? 1
    const page_size = params?.size ?? 10
    const res = await request.get(V1.REVIEW_QUEUE, {
      params: { page, page_size }
    })
    const d = res.data
    taskList.value = d.list || []
    totalCount.value = d.total ?? 0
    return { list: d.list || [], total: d.total ?? 0 }
  }

  const getTaskDetail = async (contentId) => {
    const res = await request.get(V1.REVIEW_ITEM(contentId))
    const task = mapAnalyzeToTask(res.data)
    currentTask.value = task
    return task
  }

  const submitAudit = async (auditData) => {
    const action = auditData.audit_result === 'dismiss' ? 'approve' : 'reject'
    const res = await request.post(V1.REVIEW_ACTION, {
      public_id: auditData.content_id,
      action,
      audit_opinion: auditData.audit_opinion ?? ''
    })
    return res.data
  }

  /**
   * 使用 rawClient，避免 404 时全局拦截器只弹出「Not Found」。
   * 双路径均 404 时设置 historyUnavailable，由 AuditHistory 页面展示说明，不弹长文案 Toast。
   */
  const getHistoryList = async (params) => {
    const page = params?.page ?? 1
    const page_size = params?.size ?? 10
    const audit_result = params?.audit_result
    const token = useUserStore().token
    if (!token) {
      historyList.value = []
      totalCount.value = 0
      return { list: [], total: 0 }
    }

    const res = await rawClient.get(V1.REVIEW_HISTORY, {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        page,
        page_size,
        ...(audit_result ? { audit_result } : {})
      },
      validateStatus: () => true
    })

    const applyOk = (r) => {
      if (r.status !== 200) return false
      const d = r.data || {}
      historyList.value = d.list || []
      totalCount.value = d.total ?? 0
      return true
    }

    if (applyOk(res)) {
      historyUnavailable.value = false
      const d = res.data || {}
      return { list: d.list || [], total: d.total ?? 0 }
    }

    if (res.status === 404) {
      const res2 = await rawClient.get(V1.USERS_ME_REVIEW_HISTORY, {
        headers: { Authorization: `Bearer ${token}` },
        params: {
          page,
          page_size,
          ...(audit_result ? { audit_result } : {})
        },
        validateStatus: () => true
      })
      if (applyOk(res2)) {
        historyUnavailable.value = false
        const d = res2.data || {}
        return { list: d.list || [], total: d.total ?? 0 }
      }
      if (res2.status === 403) {
        historyUnavailable.value = false
        const detail = res2.data?.detail
        ElMessage.error(typeof detail === 'string' ? detail : '无审核权限（review:read）')
        historyList.value = []
        totalCount.value = 0
        return { list: [], total: 0 }
      }
      historyUnavailable.value = true
      historyList.value = []
      totalCount.value = 0
      return { list: [], total: 0 }
    }

    historyUnavailable.value = false
    const detail = res.data?.detail
    const msg =
      typeof detail === 'string'
        ? detail
        : res.status === 403
          ? '无审核权限（review:read）'
          : '加载审核历史失败'
    ElMessage.error(msg)
    historyList.value = []
    totalCount.value = 0
    return { list: [], total: 0 }
  }

  return {
    taskList,
    historyList,
    currentTask,
    totalCount,
    historyUnavailable,
    dismissHistoryUnavailable,
    getTaskList,
    getTaskDetail,
    submitAudit,
    getHistoryList
  }
})
