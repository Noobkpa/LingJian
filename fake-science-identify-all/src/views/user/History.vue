<template>
  <div class="history-container">
    <div class="page-header">
      <h2 class="page-title">识别历史记录</h2>
    </div>

    <!-- 筛选区 -->
    <div class="filter-card base-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="风险等级">
          <el-select v-model="filterForm.risk_level" placeholder="全部" clearable style="width: 140px">
            <el-option label="高风险" value="high" />
            <el-option label="中风险" value="middle" />
            <el-option label="低风险" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容类型">
          <el-select v-model="filterForm.content_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="文本" value="text" />
            <el-option label="图片" value="image" />
            <el-option label="图文混合" value="mix" />
          </el-select>
        </el-form-item>
        <el-form-item label="识别时间">
          <el-date-picker
            v-model="filterForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getHistoryList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 操作区 -->
    <div class="action-bar">
      <el-button type="danger" :disabled="selectedRows.length === 0" @click="batchDelete">
        批量删除
      </el-button>
      <el-button type="danger" @click="clearAll">清空全部记录</el-button>
      <div class="total-text">共 {{ totalCount }} 条记录</div>
    </div>

    <!-- 列表区 -->
    <div v-if="loading" class="loading-area">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="historyList.length > 0" class="history-list">
      <el-table
        :data="historyList"
        row-key="content_id"
        stripe
        class="history-table"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" align="center" />
        <el-table-column
          prop="content_id"
          label="内容ID"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column prop="content_type" label="内容类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ typeMap[row.content_type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="riskTagMap[row.risk_level]" size="small">
              {{ riskTextMap[row.risk_level] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="llm_score" label="风险得分" width="100" align="center" />
        <el-table-column prop="upload_time" label="识别时间" min-width="180" />
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" @click="goDetail(row.content_id)">查看详情</el-button>
            <el-button size="small" type="danger" @click="deleteSingle(row.content_id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-area">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="getHistoryList"
          @current-change="getHistoryList"
        />
      </div>
    </div>

    <EmptyState v-else description="暂无识别历史记录">
      <el-button type="primary" @click="router.push('/user/home')">去识别内容</el-button>
    </EmptyState>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useIdentifyStore } from '@/stores/user/identify'
import { ElMessageBox, ElMessage } from 'element-plus'
import EmptyState from '@/components/user/EmptyState.vue'

const router = useRouter()
const identifyStore = useIdentifyStore()

// 状态定义
const loading = ref(false)
const selectedRows = ref([])
// 筛选表单
const filterForm = reactive({
  risk_level: '',
  content_type: '',
  date_range: []
})
// 分页
const pagination = reactive({
  page: 1,
  size: 10
})
// 映射关系
const typeMap = {
  text: '文本',
  image: '图片',
  mix: '图文混合'
}
const riskTextMap = {
  high: '高风险',
  middle: '中风险',
  low: '低风险'
}
const riskTagMap = {
  high: 'danger',
  middle: 'warning',
  low: 'success'
}

// 计算属性
const historyList = computed(() => identifyStore.historyList)
const totalCount = computed(() => identifyStore.totalCount)

const handleSelectionChange = (rows) => {
  selectedRows.value = rows || []
}

// 方法
const getHistoryList = async () => {
  const params = {
    page: pagination.page,
    size: pagination.size,
    risk_level: filterForm.risk_level,
    content_type: filterForm.content_type,
    start_date: filterForm.date_range?.[0] || '',
    end_date: filterForm.date_range?.[1] || ''
  }
  try {
    loading.value = true
    await identifyStore.getHistoryList(params)
  } catch (error) {
    console.error('获取历史记录失败', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.risk_level = ''
  filterForm.content_type = ''
  filterForm.date_range = []
  pagination.page = 1
  getHistoryList()
}

const goDetail = (contentId) => {
  router.push(`/user/result/${contentId}`)
}

const deleteSingle = (contentId) => {
  ElMessageBox.confirm('确定要删除该条记录吗？删除后无法恢复', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await identifyStore.deleteHistory([contentId])
    ElMessage.success('删除成功')
    getHistoryList()
  }).catch(() => {})
}

const batchDelete = () => {
  const ids = selectedRows.value.map((r) => r.content_id).filter(Boolean)
  if (ids.length === 0) {
    ElMessage.warning('请选择要删除的记录')
    return
  }
  ElMessageBox.confirm(`确定要删除选中的 ${ids.length} 条记录吗？删除后无法恢复`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await identifyStore.deleteHistory(ids)
    ElMessage.success('批量删除成功')
    selectedRows.value = []
    getHistoryList()
  }).catch(() => {})
}

const clearAll = () => {
  ElMessageBox.confirm('确定要清空全部识别记录吗？清空后无法恢复', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    await identifyStore.clearAllHistory()
    ElMessage.success('全部记录已清空')
    getHistoryList()
  }).catch(() => {})
}

onMounted(() => {
  getHistoryList()
})
</script>

<style scoped>
.history-container {
  width: 100%;
}
.history-list {
  width: 100%;
}
.history-table {
  width: 100%;
}
.page-header {
  margin-bottom: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.action-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}
.total-text {
  margin-left: auto;
  font-size: 14px;
  color: #606266;
}
.loading-area {
  padding: 20px 0;
}
.pagination-area {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
