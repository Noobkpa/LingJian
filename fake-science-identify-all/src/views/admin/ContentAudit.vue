<template>
  <div class="content-audit-container">
    <div class="page-header">
      <h2 class="page-title">内容批量审核</h2>
      <el-space>
        <el-button type="primary" @click="handleBatchImport">批量导入</el-button>
        <el-button type="success" :disabled="selectedIds.length === 0" @click="handleBatchAudit('confirm')">
          批量标记伪科普
        </el-button>
        <el-button :disabled="selectedIds.length === 0" @click="handleBatchAudit('dismiss')">
          批量驳回
        </el-button>
        <el-button type="warning" @click="handleExport">导出数据</el-button>
      </el-space>
    </div>

    <!-- 筛选区 -->
    <div class="base-card">
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
        <el-form-item label="审核状态">
          <el-select v-model="filterForm.audit_status" placeholder="全部" clearable style="width: 140px">
            <el-option label="未审核" value="pending" />
            <el-option label="已审核" value="audited" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getContentList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格区 -->
    <div class="base-card">
      <el-table
        :data="contentList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="content_id" label="内容ID" width="120" />
        <el-table-column prop="content_type" label="内容类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ typeMap[row.content_type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="riskTagMap[row.risk_level]" size="small">
              {{ riskTextMap[row.risk_level] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="llm_score" label="风险得分" width="100" />
        <el-table-column prop="content_text" label="内容预览" show-overflow-tooltip />
        <el-table-column prop="audit_status" label="审核状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.audit_status === 'audited' ? 'success' : 'info'" size="small">
              {{ row.audit_status === 'audited' ? '已审核' : '未审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" class="table-action-btn" @click="handleViewDetail(row)">查看详情</el-button>
            <el-button
              size="small"
              type="danger"
              class="table-action-btn"
              @click="handleSingleAudit(row, 'confirm')"
              v-if="row.audit_status !== 'audited'"
            >
              标记伪科普
            </el-button>
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
          @size-change="getContentList"
          @current-change="getContentList"
        />
      </div>
    </div>

    <!-- 内容详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="内容详情" width="700px">
      <div v-if="currentContent.content_id" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="内容ID">{{ currentContent.content_id }}</el-descriptions-item>
          <el-descriptions-item label="内容类型">{{ typeMap[currentContent.content_type] }}</el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="riskTagMap[currentContent.risk_level]" size="small">
              {{ riskTextMap[currentContent.risk_level] }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险得分">{{ currentContent.llm_score }}</el-descriptions-item>
          <el-descriptions-item label="上传用户">{{ currentContent.username || '-' }}</el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ currentContent.upload_time }}</el-descriptions-item>
          <el-descriptions-item label="判定依据" :span="2">
            <ul>
              <li v-for="(item, index) in currentContent.judgment_basis" :key="index">
                {{ item }}
              </li>
            </ul>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="currentContent.content_text" class="text-preview">
          <h4>文本内容</h4>
          <p>{{ currentContent.content_text }}</p>
        </div>
        <div v-if="currentContent.image_list?.length" class="image-preview">
          <h4>图片内容</h4>
          <div class="image-list">
            <el-image
              v-for="(img, index) in currentContent.image_list"
              :key="index"
              :src="img.url"
              :preview-src-list="currentContent.image_list.map(item => item.url)"
              fit="cover"
              class="preview-image"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button
          type="danger"
          v-if="currentContent.audit_status !== 'audited'"
          @click="handleSingleAudit(currentContent, 'confirm')"
        >
          标记伪科普
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="批量导入内容" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">
            仅支持 .xlsx/.xls 格式的Excel文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="handleSubmitImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useAuditStore } from '@/stores/admin/audit'
import { handleBlobExport } from '@/utils/export'

const auditStore = useAuditStore()

// 状态定义
const loading = ref(false)
const importLoading = ref(false)
const showDetailDialog = ref(false)
const showImportDialog = ref(false)
const selectedIds = ref([])
const contentList = ref([])
const totalCount = ref(0)
const currentContent = ref({})
const uploadFile = ref(null)

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

// 筛选表单
const filterForm = reactive({
  risk_level: '',
  content_type: '',
  audit_status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 10
})

// 方法
const getContentList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filterForm
    }
    const data = await auditStore.getContentList(params)
    contentList.value = data.list
    totalCount.value = data.total
  } catch (error) {
    console.error('获取内容列表失败', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.risk_level = ''
  filterForm.content_type = ''
  filterForm.audit_status = ''
  pagination.page = 1
  getContentList()
}

const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.content_id)
}

const handleViewDetail = (row) => {
  currentContent.value = row
  showDetailDialog.value = true
}

const handleSingleAudit = async (row, action) => {
  try {
    await auditStore.batchAudit({
      content_ids: [row.content_id],
      audit_action: action,
      audit_remark: action === 'confirm' ? '标记为伪科普' : '驳回'
    })
    ElMessage.success('审核成功')
    showDetailDialog.value = false
    getContentList()
  } catch (error) {
    console.error('审核失败', error)
  }
}

const handleBatchAudit = async (action) => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要审核的内容')
    return
  }
  const actionText = action === 'confirm' ? '标记伪科普' : '驳回'
  ElMessageBox.confirm(`确定要对选中的 ${selectedIds.value.length} 条内容执行${actionText}操作吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await auditStore.batchAudit({
      content_ids: selectedIds.value,
      audit_action: action,
      audit_remark: `批量${actionText}`
    })
    ElMessage.success('批量审核成功')
    selectedIds.value = []
    getContentList()
  }).catch(() => {})
}

const handleExport = async () => {
  try {
    const blob = await auditStore.exportData(filterForm)
    handleBlobExport(blob, '伪科普识别结果')
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败', error)
  }
}

const handleBatchImport = () => {
  showImportDialog.value = true
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

const handleSubmitImport = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  try {
    importLoading.value = true
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    await request.post('/admin/content/batch-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('导入成功')
    showImportDialog.value = false
    getContentList()
  } catch (error) {
    console.error('导入失败', error)
  } finally {
    importLoading.value = false
  }
}

onMounted(() => {
  getContentList()
})
</script>

<style scoped>
.content-audit-container {
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
.detail-content h4 {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin: 16px 0 8px 0;
}
.text-preview p {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
  font-size: 14px;
}
.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.preview-image {
  width: 100px;
  height: 100px;
  border-radius: 4px;
}
</style>