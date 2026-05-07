<template>
  <div class="audit-history-container">
    <h2 class="page-title">我的审核历史</h2>

    <el-alert
      v-if="auditStore.historyUnavailable"
      type="warning"
      show-icon
      closable
      class="history-hint"
      title="审核历史接口返回 404"
      @close="auditStore.dismissHistoryUnavailable"
    >
      <p class="hint-line">
        当前请求未命中带「审核历史」路由的后端（与是否使用 admin 无关）。请确认：①本机已用<strong>当前仓库代码</strong>启动 uvicorn，且端口与 <code>.env.development</code> 里 <code>VITE_API_BASE_URL</code> 一致（默认 <code>http://127.0.0.1:8000/api/v1</code>）；②改完环境变量后已<strong>重启</strong> <code>npm run dev</code>；③打开 <code>http://127.0.0.1:8000/docs</code> 是否能看到 <code>GET /api/v1/review/history</code>。
      </p>
    </el-alert>

    <div class="base-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="审核结果">
          <el-select v-model="filterForm.audit_result" placeholder="全部" clearable style="width: 160px">
            <el-option label="判定伪科普" value="pseudo_science" />
            <el-option label="不构成伪科普（人工认定）" value="dismiss" />
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
        <template #empty>
          <div v-if="auditStore.historyUnavailable" class="table-empty-muted">暂无数据</div>
          <div v-else class="history-empty-wrap">
            <el-empty description="">
              <template #description>
                <div class="empty-desc">
                  <p class="empty-title">暂无审核记录</p>
                  <p>
                    本列表<strong>仅包含当前登录账号</strong>在「审核任务」中<strong>提交</strong>的审核结果（不构成伪科普 / 判定伪科普）。只有在这里点「提交」后，系统才会把该条记在您名下并显示在此页。
                  </p>
                  <p class="empty-sub">若尚未在任务大厅处理过内容、或曾用其他账号/管理端操作，此处会为空；也可点「重置」后查「全部」结果。</p>
                </div>
              </template>
              <el-button type="primary" @click="goTask">去审核任务</el-button>
            </el-empty>
          </div>
        </template>
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
              {{
                row.audit_result === 'pseudo_science'
                  ? '判定伪科普'
                  : '不构成伪科普'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="audit_opinion" label="审核意见" show-overflow-tooltip />
        <el-table-column prop="audit_time" label="审核时间" width="180" />
      </el-table>

      <div class="pagination-area" v-show="totalCount > 0">
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
import { useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
import RiskTag from '@/components/RiskTag.vue'

const auditStore = useAuditStore()
const router = useRouter()

const goTask = () => router.push('/audit/task')

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
.history-hint {
  margin-bottom: 16px;
}
.history-hint .hint-line {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
.table-empty-muted {
  padding: 24px 0;
  color: #909399;
  font-size: 14px;
}
.history-empty-wrap {
  padding: 12px 0 24px;
}
.empty-desc {
  max-width: 440px;
  margin: 0 auto 16px;
  text-align: left;
}
.empty-desc p {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.65;
  color: #606266;
}
.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  text-align: center;
  margin-bottom: 12px !important;
}
.empty-sub {
  color: #909399 !important;
  font-size: 12px !important;
}
</style>
