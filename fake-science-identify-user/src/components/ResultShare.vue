<template>
  <div class="share-container">
    <el-dialog v-model="dialogVisible" title="分享识别结果" width="520px" @opened="initShare">
      <!-- 分享内容预览 -->
      <div id="share-content" class="share-content">
        <div class="share-header">
          <div class="share-logo">灵鉴伪科普识别系统</div>
          <div class="share-time">{{ formatDate }}</div>
        </div>
        <div class="share-result">
          <div class="share-risk" :class="`risk-${resultInfo.risk_level}`">
            <span class="risk-text">{{ riskTitle }}</span>
            <span class="risk-score">风险得分：{{ resultInfo.llm_score }}分</span>
          </div>
          <p v-if="resultInfo.human_review?.summary_zh" class="share-human-review">
            {{ resultInfo.human_review.summary_zh }}
          </p>
        </div>
        <div v-if="originalSnippet" class="share-original">
          <p class="original-title">原始识别内容</p>
          <p class="original-text">{{ originalSnippet }}</p>
        </div>
        <div class="share-basis">
          <p class="basis-title">核心判定依据</p>
          <ul class="basis-list">
            <li v-for="(item, index) in (resultInfo.judgment_basis || []).slice(0, 3)" :key="index">
              {{ index + 1 }}. {{ item }}
            </li>
          </ul>
          <p v-if="(resultInfo.judgment_basis || []).length > 3" class="basis-more">更多内容请扫码查看详情</p>
        </div>
        <div class="share-footer">
          <div class="qrcode-area">
            <canvas id="qrcode-canvas"></canvas>
            <p>扫码查看完整结果</p>
          </div>
          <div class="share-desc">
            <p>科学辟谣，从我做起</p>
            <p>拒绝伪科普，守护科学真相</p>
          </div>
        </div>
      </div>

      <!-- 分享操作按钮 -->
      <template #footer>
        <div class="share-footer-btn">
          <el-button @click="copyLink">复制分享链接</el-button>
          <el-button type="primary" @click="downloadImage">下载分享图片</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { generateQRCode, generateShareImage, copyShareLink } from '@/utils/share'

// 组件入参
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  resultInfo: {
    type: Object,
    default: () => ({})
  },
  contentId: {
    type: String,
    default: ''
  }
})

// 组件事件
const emit = defineEmits(['update:visible'])

// 状态定义
const dialogVisible = ref(false)
const shareLink = ref('')
const formatDate = ref('')

// 监听弹窗显隐
watch(() => props.visible, (val) => {
  dialogVisible.value = val
})
watch(() => dialogVisible.value, (val) => {
  emit('update:visible', val)
})

// 计算属性
const riskTitle = computed(() => {
  const map = {
    high: '高风险 · 疑似伪科普',
    middle: '中风险 · 需谨慎阅读',
    low: '低风险 · 可信科普内容'
  }
  return map[props.resultInfo.risk_level] || '未知风险'
})

const MAX_ORIGINAL_LEN = 560

function truncateText(s, max) {
  if (!s) return ''
  return s.length <= max ? s : `${s.slice(0, max)}…`
}

/** 与结果页「原始识别内容」对齐：纯文本用 input；图片/混合可带 OCR 文本 */
const originalSnippet = computed(() => {
  const info = props.resultInfo || {}
  const raw = info._raw || {}
  const input = String(info.content_text || raw.input_text || '').trim()
  const ocrTxt = String(raw.ocr?.text || '').trim()

  if (input && ocrTxt && input.replace(/\s/g, '') !== ocrTxt.replace(/\s/g, '')) {
    return truncateText(`【文本】${input}\n【图中文字】${ocrTxt}`, MAX_ORIGINAL_LEN)
  }
  const single = input || ocrTxt
  return single ? truncateText(single, MAX_ORIGINAL_LEN) : ''
})

// 初始化分享内容
const initShare = async () => {
  if (!props.contentId) return
  // 生成分享链接，根据实际域名修改
  shareLink.value = `${window.location.origin}/result/${props.contentId}`
  // 格式化日期
  formatDate.value = new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
  // 生成二维码
  await nextTick()
  await generateQRCode(shareLink.value, 'qrcode-canvas')
}

// 复制分享链接
const copyLink = async () => {
  try {
    await copyShareLink(shareLink.value)
    ElMessage.success('分享链接复制成功')
  } catch (error) {
    ElMessage.error('链接复制失败，请手动复制')
  }
}

// 下载分享图片
const downloadImage = async () => {
  const res = await generateShareImage('share-content')
  if (!res) {
    ElMessage.error('分享图片生成失败')
    return
  }
  // 创建下载链接
  const a = document.createElement('a')
  a.href = res.downloadUrl
  a.download = `伪科普识别结果_${props.contentId}.png`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(res.downloadUrl)
  ElMessage.success('分享图片下载成功')
}
</script>

<style scoped>
.share-content {
  width: 100%;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}
.share-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 2px solid #4080FF;
  margin-bottom: 20px;
}
.share-logo {
  font-size: 18px;
  font-weight: bold;
  color: #4080FF;
}
.share-time {
  font-size: 14px;
  color: #909399;
}
.share-result {
  margin-bottom: 20px;
}
.share-risk {
  padding: 16px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.share-risk.risk-high {
  background: #fef0f0;
  color: #F53F3F;
}
.share-risk.risk-middle {
  background: #fdf6ec;
  color: #FF7D00;
}
.share-risk.risk-low {
  background: #f0f9ff;
  color: #00B42A;
}
.risk-text {
  font-size: 18px;
  font-weight: bold;
}
.risk-score {
  font-size: 14px;
}
.share-human-review {
  margin: 10px 0 0;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.5;
  color: #606266;
  background: #f4f4f5;
  border-radius: 6px;
}
.share-original {
  margin-bottom: 18px;
  padding: 12px 14px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
.original-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px;
}
.original-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}
.basis-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
}
.basis-list {
  padding-left: 0;
  margin-bottom: 8px;
}
.basis-list li {
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  margin-bottom: 8px;
  list-style: none;
}
.basis-more {
  font-size: 12px;
  color: #909399;
  text-align: center;
}
.share-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
.qrcode-area {
  text-align: center;
}
.qrcode-area canvas {
  width: 80px;
  height: 80px;
}
.qrcode-area p {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}
.share-desc p {
  text-align: right;
  font-size: 14px;
  color: #4080FF;
  margin-bottom: 4px;
}
.share-footer-btn {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>