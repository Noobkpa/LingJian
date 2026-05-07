import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export const useAuditStore = defineStore('auditTask', () => {
  // 状态定义
  const taskList = ref([])
  const historyList = ref([])
  const currentTask = ref(null)
  const totalCount = ref(0)

  // 【真实后端】获取审核任务列表
  const getTaskList = async (params) => {
    const { data } = await request.get('/auditor/task/list', { params })
    taskList.value = data.list
    totalCount.value = data.total
    return data
  }

  // 【真实后端】获取审核详情
  const getTaskDetail = async (contentId) => {
    const { data } = await request.get(`/auditor/task/detail/${contentId}`)
    currentTask.value = data
    return data
  }

  // 【真实后端】提交审核结果
  const submitAudit = async (auditData) => {
    const { data } = await request.post('/auditor/task/submit', auditData)
    return data
  }

  // 【真实后端】获取审核历史
  const getHistoryList = async (params) => {
    const { data } = await request.get('/auditor/history/list', { params })
    historyList.value = data.list
    totalCount.value = data.total
    return data
  }

  return {
    taskList,
    historyList,
    currentTask,
    totalCount,
    getTaskList,
    getTaskDetail,
    submitAudit,
    getHistoryList
  }
})