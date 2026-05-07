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
            <el-alert
              v-if="riskAuditGuide"
              type="info"
              :closable="false"
              show-icon
              class="risk-guide-alert"
            >
              <p class="risk-guide-text">{{ riskAuditGuide }}</p>
            </el-alert>
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
          <div class="base-card audit-action-card">
            <h3 class="card-title">审核操作</h3>
            <p class="audit-action-hint">
              先选审核结果：认定「伪科普」须写清依据；认定「不构成伪科普」时意见可留空。人工结论与 AI
              风险标签不要求一一对应，以您对内容性质的认定为准。
            </p>
            <el-form
              ref="auditFormRef"
              :model="auditForm"
              :rules="auditRules"
              label-width="88px"
            >
              <el-form-item label="审核结果" prop="audit_result">
                <el-radio-group v-model="auditForm.audit_result" class="audit-result-group">
                  <el-radio label="pseudo_science">判定为伪科普</el-radio>
                  <el-radio label="dismiss">不构成伪科普（人工认定）</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item prop="audit_opinion">
                <template #label>
                  <span class="audit-opinion-label">
                    审核意见
                    <span v-if="auditForm.audit_result === 'pseudo_science'" class="req-star">*</span>
                    <span v-else-if="auditForm.audit_result === 'dismiss'" class="label-optional">（选填）</span>
                  </span>
                </template>
                <el-input
                  v-model="auditForm.audit_opinion"
                  type="textarea"
                  :rows="4"
                  maxlength="2000"
                  show-word-limit
                  :placeholder="opinionPlaceholder"
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
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
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

const auditRules = computed(() => ({
  audit_result: [{ required: true, message: '请选择审核结果', trigger: 'change' }],
  audit_opinion: [
    {
      validator: (_rule, value, callback) => {
        const v = String(value ?? '').trim()
        if (auditForm.audit_result === 'pseudo_science') {
          if (!v) {
            callback(new Error('判定为伪科普时须填写审核意见'))
            return
          }
          if (v.length < 10) {
            callback(new Error('审核意见不少于10个字'))
            return
          }
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}))

/** 说明：风险等级是模型参考；人工仍按「是否伪科普」二选一，低风险也可在确有依据时判伪科普。 */
const riskAuditGuide = computed(() => {
  const lv = task.value?.risk_level
  if (lv === 'low') {
    return (
      '低风险表示模型认为疑点较少。若您复核后也认为不构成伪科普，一般选第二项「不构成伪科普（人工认定）」；' +
      '若您认为仍属伪科普，应选「判定为伪科普」并写明依据。'
    )
  }
  if (lv === 'middle') {
    return (
      '中风险请结合正文与下方判定依据独立判断：确认伪科普选第一项；认为不构成伪科普则选第二项。'
    )
  }
  if (lv === 'high') {
    return '高风险表示模型认为疑点较多，请结合正文与依据重点判断；最终仍由您在下方两项中选择是否认定伪科普。'
  }
  return ''
})

const opinionPlaceholder = computed(() => {
  if (auditForm.audit_result === 'dismiss') {
    return '选填：可写认定理由或备注，不填也可提交'
  }
  if (auditForm.audit_result === 'pseudo_science') {
    return '请写明判定为伪科普的依据（不少于10字）'
  }
  return '请先选择审核结果'
})

watch(
  () => auditForm.audit_result,
  () => {
    auditFormRef.value?.clearValidate('audit_opinion')
  }
)

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
  try {
    await auditFormRef.value.validate()
  } catch {
    return
  }

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
.risk-guide-alert {
  margin-top: 12px;
}
.risk-guide-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-regular);
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
.audit-action-card {
  margin-top: 16px;
}
@media (min-width: 992px) {
  .audit-action-card {
    position: sticky;
    top: 16px;
  }
}
.audit-action-hint {
  margin: -8px 0 14px;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}
.audit-result-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
}
.audit-opinion-label {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  line-height: 1.2;
}
.req-star {
  color: var(--el-color-danger);
  font-weight: 600;
}
.label-optional {
  color: #909399;
  font-weight: normal;
  font-size: 12px;
}
</style>