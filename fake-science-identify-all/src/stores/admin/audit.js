import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useAuditStore = defineStore('audit', () => {
  // 状态定义
  const contentList = ref([])
  const totalCount = ref(0)
  const statsData = ref({})

  // 获取内容列表
  const getContentList = async (params) => {
    const { data } = await request.get('/admin/content/list', { params })
    contentList.value = data.list
    totalCount.value = data.total
    return data
  }

  // 批量审核
  const batchAudit = async (auditData) => {
    const { data } = await request.post('/admin/content/batch-audit', auditData)
    return data
  }

  // 获取统计数据
  const getStatsData = async () => {
    const { data } = await request.get('/admin/stats')
    statsData.value = data
    return data
  }

  // 导出数据
  const exportData = async (params) => {
    const { data } = await request.get('/admin/content/export', { 
      params, 
      responseType: 'blob' 
    })
    return data
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