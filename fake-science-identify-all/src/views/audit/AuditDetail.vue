<template>
  <div class="audit-detail-container" v-loading="loading">
    <div v-if="task.content_id">
      <!-- 顶部操作栏 -->
      <div class="page-header">
        <el-button @click="goBack">返回任务列表</el-button>
        <span class="task-id">内容ID：{{ task.content_id }}</span>
      </div>

      <el-row :gutter="20">
        <!-- 左侧：内容详情 -->
        <el-col :span="16">
          <div class="base-card">
            <h3 class="card-title">待审核内容</h3>
            <div class="content-meta">
              <el-space wrap>
                <span>内容类型：<el-tag size="small">{{ task.content_type === 'text' ? '文本' : '图片' }}</el-tag></span>
                <span>上传用户：{{ task.upload_user }}</span>
                <span>上传时间：{{ task.upload_time }}</span>
              </el-space>
            </div>
            <div class="audit-content-text mt-4">
              {{ task.content_text }}
            </div>
          </div>
        </el-col>

        <!-- 右侧：AI辅助信息 + 审核操作 -->
        <el-col :span="8">
          <!-- AI辅助判定 -->
          <div class="base-card">
            <h3 class="card-title">AI辅助判定</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="风险等级">
                <RiskTag :level="task.risk_level" />
              </el-descriptions-item>
              <el-descriptions-item label="风险得分">
                <span class="score-text">{{ task.llm_score }}</span>
              </el-descriptions-item>
            </el-descriptions>
            <div class="judgment-basis mt-4">
              <h4>判定依据</h4>
              <ul>
                <li v-for="(item, index) in task.judgment_basis" :key="index">
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>

          <!-- 审核操作 -->
          <div class="base-card">
            <h3 class="card-title">审核操作</h3>
            <el-form
              ref="auditFormRef"
              :model="auditForm"
              :rules="auditRules"
              label-width="80px"
            >
              <el-form-item label="审核结果" prop="audit_result">
                <el-radio-group v-model="auditForm.audit_result">
                  <el-radio label="pseudo_science">判定为伪科普</el-radio>
                  <el-radio label="dismiss">予以通过</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="审核意见" prop="audit_opinion">
                <el-input
                  v-model="auditForm.audit_opinion"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入详细的审核意见"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  :loading="submitLoading"
                  @click="handleSubmit"
                  style="width: 100%"
                >
                  提交审核
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit/audit'
import { ElMessage } from 'element-plus'
import RiskTag from '@/components/RiskTag.vue'

const route = useRoute()
const router = useRouter()
const auditStore = useAuditStore()

const loading = ref(false)
const submitLoading = ref(false)
const auditFormRef = ref()
const task = ref({})

const auditForm = reactive({
  content_id: '',
  audit_result: '',
  audit_opinion: ''
})

const auditRules = {
  audit_result: [
    { required: true, message: '请选择审核结果', trigger: 'change' }
  ],
  audit_opinion: [
    { required: true, message: '请输入审核意见', trigger: 'blur' },
    { min: 10, message: '审核意见不少于10个字', trigger: 'blur' }
  ]
}

const getTaskDetail = async () => {
  try {
    loading.value = true
    const contentId = route.params.contentId
    auditForm.content_id = contentId
    task.value = await auditStore.getTaskDetail(contentId)
  } catch (error) {
    console.error('获取任务详情失败', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!auditFormRef.value) return
  const valid = await auditFormRef.value.validate()
  if (!valid) return

  try {
    submitLoading.value = true
    await auditStore.submitAudit(auditForm)
    ElMessage.success('审核提交成功')
    router.push('/audit/task')
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitLoading.value = false
  }
}

const goBack = () => {
  router.push('/audit/task')
}

onMounted(() => {
  getTaskDetail()
})
</script>

<style scoped>
.audit-detail-container {
  width: 100%;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.task-id {
  font-size: 14px;
  color: #909399;
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 16px 0;
}
.content-meta {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 16px;
}
.mt-4 {
  margin-top: 16px;
}
.score-text {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}
.judgment-basis h4 {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}
.judgment-basis ul {
  padding-left: 20px;
}
.judgment-basis li {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  margin-bottom: 4px;
}
</style>