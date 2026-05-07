<template>
  <div class="result-container">
    <div class="page-header">
      <el-button @click="goBack" :icon="ArrowLeft">返回上一页</el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-area">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 结果内容 -->
    <div v-else-if="resultInfo.content_id" class="result-content">
      <el-alert
        v-if="resultInfo.human_review"
        :title="resultInfo.human_review.summary_zh || '人工复核'"
        :type="humanReviewAlertType"
        :closable="false"
        show-icon
        class="human-review-alert"
      >
        <div v-if="resultInfo.human_review.note || resultInfo.human_review.reviewed_at">
          <p v-if="resultInfo.human_review.note" class="human-review-note">审核说明：{{ resultInfo.human_review.note }}</p>
          <p v-if="resultInfo.human_review.reviewed_at" class="human-review-meta">复核时间：{{ formatReviewedAt }}</p>
        </div>
      </el-alert>

      <!-- 风险等级卡片 -->
      <RiskLevelCard
        :risk-level="resultInfo.risk_level"
        :risk-score="resultInfo.llm_score"
        :logical-fallacy="resultInfo.logical_fallacy"
        :scientific-error="resultInfo.scientific_error"
        :why-sound="resultInfo.why_sound"
        :why-risky="resultInfo.why_risky"
        :reader-actions="resultInfo.reader_actions"
        :core-features="resultInfo.core_features"
        :judgment-summary="resultInfo.judgment_summary"
      />

      <!-- 原始内容展示 -->
      <div class="original-content base-card">
        <h3 class="content-title">原始识别内容</h3>
        <!-- 文本内容：高风险用语红色高亮 -->
        <div v-if="resultInfo.content_text" class="text-content">
          <HighlightedPlainText
            :text="resultInfo.content_text"
            :core-features="resultInfo.core_features"
            :bert-labels="resultInfo.bert_predicted_labels"
          />
        </div>
        <!-- 图片内容 -->
        <div v-if="resultInfo.image_list && resultInfo.image_list.length" class="image-content">
          <el-image
            v-for="(img, index) in resultInfo.image_list"
            :key="index"
            :src="img.url"
            :preview-src-list="resultInfo.image_list.map(item => item.url)"
            fit="cover"
            class="result-image"
          />
        </div>
      </div>

      <!-- 操作按钮区 -->
      <div class="action-area">
        <el-button type="primary" @click="toggleCollect" :icon="isCollected ? StarFilled : Star">
          {{ isCollected ? '已收藏' : '收藏结果' }}
        </el-button>
        <el-button @click="showShare = true" :icon="Share">分享结果</el-button>
        <el-button @click="showFeedback = true" :icon="ChatDotRound">意见反馈</el-button>
        <el-button @click="reIdentify" :icon="Refresh">重新识别</el-button>
      </div>
    </div>

    <!-- 空状态 -->
    <EmptyState v-else description="未找到该识别结果" />

    <!-- 分享弹窗 -->
    <ResultShare
      v-model:visible="showShare"
      :result-info="resultInfo"
      :content-id="contentId"
    />

    <el-dialog
      v-model="showFeedback"
      title="意见反馈"
      width="520px"
      destroy-on-close
      @closed="feedbackMessage = ''"
    >
      <p class="feedback-hint">
        若识别结果与您的理解不符、存在明显错误或希望改进功能，请简要说明（将附带当前结果 ID，便于我们定位）。
      </p>
      <el-input
        v-model="feedbackMessage"
        type="textarea"
        :rows="5"
        maxlength="2000"
        show-word-limit
        placeholder="请描述您的问题或建议…"
      />
      <template #footer>
        <el-button @click="showFeedback = false">取消</el-button>
        <el-button type="primary" :loading="feedbackSubmitting" @click="submitFeedback">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useIdentifyStore } from '@/stores/identify'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Star, StarFilled, Share, Refresh, ChatDotRound } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'
import RiskLevelCard from '@/components/RiskLevelCard.vue'
import HighlightedPlainText from '@/components/HighlightedPlainText.vue'
import ResultShare from '@/components/ResultShare.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const identifyStore = useIdentifyStore()

// 状态定义
const contentId = ref(route.params.contentId || '')
const loading = ref(false)
const showShare = ref(false)
const showFeedback = ref(false)
const feedbackMessage = ref('')
const feedbackSubmitting = ref(false)
const isCollected = ref(false)
const resultInfo = computed(() => identifyStore.currentResult)

const humanReviewAlertType = computed(() => {
  const st = resultInfo.value?.human_review?.status
  if (st === 'approved') return 'success'
  if (st === 'rejected') return 'error'
  return 'info'
})

const formatReviewedAt = computed(() => {
  const iso = resultInfo.value?.human_review?.reviewed_at
  if (!iso) return ''
  try {
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) return iso
    return d.toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
})

// 方法
const getResultDetail = async () => {
  if (!contentId.value) return
  try {
    loading.value = true
    await identifyStore.getIdentifyResult(contentId.value)
  } catch (error) {
    console.error('获取识别结果失败', error)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const reIdentify = () => {
  router.push('/home')
}

const toggleCollect = async () => {
  try {
    await identifyStore.toggleCollect(contentId.value, !isCollected.value)
    isCollected.value = !isCollected.value
    ElMessage.success(isCollected.value ? '收藏成功' : '取消收藏成功')
  } catch (error) {
    console.error('收藏操作失败', error)
  }
}

const submitFeedback = async () => {
  const text = feedbackMessage.value.trim()
  if (!text) {
    ElMessage.warning('请填写反馈内容')
    return
  }
  try {
    feedbackSubmitting.value = true
    await request.post(
      V1.FEEDBACK,
      { content_id: contentId.value || undefined, message: text },
      { timeout: 60_000 }
    )
    ElMessage.success('感谢反馈，我们已收到')
    showFeedback.value = false
    feedbackMessage.value = ''
  } catch (e) {
    console.error('提交反馈失败', e)
  } finally {
    feedbackSubmitting.value = false
  }
}

onMounted(() => {
  getResultDetail()
})
</script>

<style scoped>
.result-container {
  width: 100%;
}
.page-header {
  margin-bottom: 20px;
}
.loading-area {
  padding: 20px 0;
}
.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.content-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 16px;
}
.text-content {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
  font-size: 14px;
  color: #303133;
}
.image-content {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.result-image {
  width: 120px;
  height: 120px;
  border-radius: 6px;
}
.action-area {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
  padding: 16px 0;
}
.feedback-hint {
  margin: 0 0 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
.human-review-alert {
  margin-bottom: 4px;
}
.human-review-note,
.human-review-meta {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--el-text-color-regular);
}
.human-review-meta {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
}
</style>