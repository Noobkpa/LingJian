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
      <!-- 风险等级卡片 -->
      <RiskLevelCard
        :risk-level="resultInfo.risk_level"
        :risk-score="resultInfo.llm_score"
        :judgment-basis="resultInfo.judgment_basis"
      />

      <!-- 原始内容展示 -->
      <div class="original-content base-card">
        <h3 class="content-title">原始识别内容</h3>
        <!-- 文本内容 -->
        <div v-if="resultInfo.content_text" class="text-content">
          <p>{{ resultInfo.content_text }}</p>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useIdentifyStore } from '@/stores/user/identify'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Star, StarFilled, Share, Refresh } from '@element-plus/icons-vue'
import RiskLevelCard from '@/components/user/RiskLevelCard.vue'
import ResultShare from '@/components/user/ResultShare.vue'
import EmptyState from '@/components/user/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const identifyStore = useIdentifyStore()

// 状态定义
const contentId = ref(route.params.contentId || '')
const loading = ref(false)
const showShare = ref(false)
const isCollected = ref(false)
const resultInfo = computed(() => identifyStore.currentResult)

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
  router.push('/user/home')
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
  gap: 16px;
  justify-content: center;
  padding: 16px 0;
}
</style>