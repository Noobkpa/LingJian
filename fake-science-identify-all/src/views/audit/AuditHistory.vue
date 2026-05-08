<template>
  <div class="audit-history-container">
    <h2 class="page-title">我的审核历史</h2>

    <div class="base-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="审核结果">
          <el-select v-model="filterForm.audit_result" placeholder="全部" clearable style="width: 160px">
            <el-option label="判定伪科普" value="pseudo_science" />
            <el-option label="予以通过" value="dismiss" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getHistoryList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="base-card" v-loading="loading">
      <el-table :data="historyList" stripe style="width: 100%">
        <el-table-column prop="audit_id" label="审核ID" width="100" />
        <el-table-column prop="content_id" label="内容ID" width="120" />
        <el-table-column prop="risk_level" label="原风险等级" width="120">
          <template #default="{ row }">
            <RiskTag :level="row.risk_level" />
          </template>
        </el-table-column>
        <el-table-column prop="audit_result" label="审核结果" width="140">
          <template #default="{ row }">
            <el-tag :type="row.audit_result === 'pseudo_science' ? 'danger' : 'success'" size="small">
              {{ row.audit_result === 'pseudo_science' ? '判定伪科普' : '予以通过' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="audit_opinion" label="审核意见" show-overflow-tooltip />
        <el-table-column prop="audit_time" label="审核时间" width="180" />
      </el-table>

      <div class="pagination-area">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="getHistoryList"
          @current-change="getHistoryList"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuditStore } from '@/stores/audit/audit'
import RiskTag from '@/components/audit/RiskTag.vue'

const auditStore = useAuditStore()

const loading = ref(false)
const historyList = ref([])
const totalCount = ref(0)

const filterForm = reactive({
  audit_result: ''
})

const pagination = reactive({
  page: 1,
  size: 10
})

const getHistoryList = async () => {
  try {
    loading.value = true
    const data = await auditStore.getHistoryList({ ...pagination, ...filterForm })
    historyList.value = data.list
    totalCount.value = data.total
  } catch (error) {
    console.error('获取审核历史失败', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.audit_result = ''
  pagination.page = 1
  getHistoryList()
}

onMounted(() => {
  getHistoryList()
})
</script>

<style scoped>
.audit-history-container {
  width: 100%;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 20px 0;
}
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
