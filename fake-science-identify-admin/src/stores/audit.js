import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import request from '@/utils/request'
import { useAdminStore } from '@/stores/admin'
import { V1 } from '@/api/v1/endpoints'

export const useAuditStore = defineStore('audit', () => {
  const contentList = ref([])
  const totalCount = ref(0)
  const statsData = ref({})

  /** 待审核队列（对接 GET /review/queue），筛选参数下发后端 */
  const getContentList = async (params) => {
    const page = params?.page ?? 1
    const page_size = params?.size ?? 10
    const risk_level = params?.risk_level
    const content_type = params?.content_type
    const audit_status = params?.audit_status
    const res = await request.get(V1.REVIEW_QUEUE, {
      params: {
        page,
        page_size,
        ...(risk_level ? { risk_level } : {}),
        ...(content_type ? { content_type } : {}),
        ...(audit_status !== undefined && audit_status !== ''
          ? { audit_status }
          : {})
      }
    })
    const d = res.data
    contentList.value = d.list || []
    totalCount.value = d.total ?? 0
    return { list: d.list || [], total: d.total ?? 0 }
  }

  /** audit_action: confirm=标记伪科普 -> reject；dismiss=驳回 -> approve */
  const batchAudit = async (payload) => {
    const ids = payload.content_ids || []
    const act =
      payload.audit_action === 'confirm' ? 'reject' : 'approve'
    for (const id of ids) {
      await request.post(V1.REVIEW_ACTION, { public_id: id, action: act })
    }
    return { ok: true }
  }

  const getStatsData = async () => {
    const [ov, rb, dailyRes] = await Promise.all([
      request.get(V1.ADMIN_STATS_OVERVIEW),
      request.get(V1.ADMIN_STATS_RISK_BUCKETS),
      request.get(V1.ADMIN_STATS_DAILY, { params: { days: 7 } })
    ])
    const o = ov.data
    const accN = o.accuracy_review_count ?? 0
    const acc =
      o.accuracy_percent != null && accN > 0
        ? Number(o.accuracy_percent)
        : null
    const buckets = rb.data?.buckets || {}
    let high_risk_count = 0
    for (const [k, v] of Object.entries(buckets)) {
      if (String(k).includes('高')) high_risk_count += Number(v) || 0
    }
    let today_analyze_calls = 0
    let avg_inference_sec = null
    try {
      const mr = await request.get(V1.ADMIN_STATS_MODEL_RUNTIME)
      const m = mr.data
      if (m && typeof m === 'object') {
        today_analyze_calls = m.today_calls ?? 0
        avg_inference_sec = m.avg_elapsed_sec ?? null
      }
    } catch (e) {
      console.error('获取模型运行统计失败', e)
    }
    statsData.value = {
      today_count: o.contents ?? 0,
      today_analyze_calls,
      avg_inference_sec,
      high_risk_count,
      active_user_count: o.users ?? 0,
      accuracy: acc,
      accuracy_review_count: accN,
      overview: o,
      risk_buckets: rb.data,
      daily_series: dailyRes.data?.series || {}
    }
    return statsData.value
  }

  /** 导出当前筛选条件下的审核队列为 CSV（直连 axios，避免 blob 被响应拦截器改写） */
  const exportData = async (filterForm) => {
    const adminStore = useAdminStore()
    const headers = {}
    if (adminStore.token) {
      headers.Authorization = `Bearer ${adminStore.token}`
    }
    const params = {}
    if (filterForm?.risk_level) params.risk_level = filterForm.risk_level
    if (filterForm?.content_type) params.content_type = filterForm.content_type
    if (filterForm?.audit_status !== undefined && filterForm?.audit_status !== '') {
      params.audit_status = filterForm.audit_status
    }
    const resp = await axios.get('/api/v1/admin/content/export', {
      params,
      responseType: 'blob',
      timeout: 120000,
      headers
    })
    return resp.data
  }

  return {
    contentList,
    totalCount,
    statsData,
    getContentList,
    batchAudit,
    getStatsData,
    exportData
  }
})
