<template>
  <div class="audit-task-container">
    <div class="page-header">
      <h2 class="page-title">待审核任务</h2>
      <el-button type="primary" @click="getTaskList">刷新任务</el-button>
    </div>

    <!-- 任务列表 -->
    <div class="base-card" v-loading="loading">
      <el-table :data="taskList" stripe style="width: 100%">
        <el-table-column prop="content_id" label="内容ID" width="100" />
        <el-table-column prop="content_type" label="内容类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.content_type === 'text' ? '文本' : '图片' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="120">
          <template #default="{ row }">
            <RiskTag :level="row.risk_level" />
          </template>
        </el-table-column>
        <el-table-column prop="llm_score" label="AI风险得分" width="120" />
        <el-table-column prop="content_text" label="内容预览" show-overflow-tooltip />
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="goToDetail(row)">
              开始审核
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-area">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="getTaskList"
          @current-change="getTaskList"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit/audit'
import RiskTag from '@/components/RiskTag.vue'

const router = useRouter()
const auditStore = useAuditStore()

const loading = ref(false)
const taskList = ref([])
const totalCount = ref(0)

const pagination = reactive({
  page: 1,
  size: 10
})

const getTaskList = async () => {
  try {
    loading.value = true
    const data = await auditStore.getTaskList(pagination)
    taskList.value = data.list
    totalCount.value = data.total
  } catch (error) {
    console.error('获取任务列表失败', error)
  } finally {
    loading.value = false
  }
}

const goToDetail = (row) => {
  router.push(`/audit/detail/${row.content_id}`)
}

onMounted(() => {
  getTaskList()
})
</script>

<style scoped>
.audit-task-container {
  width: 100%;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>