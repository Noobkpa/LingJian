<template>
  <div class="upload-container">
    <div class="quick-demos" role="region" aria-label="快速体验示例">
      <p class="quick-demos-title">快速体验</p>
      <div class="demo-row">
        <span class="demo-cat">示例文案</span>
        <el-button
          v-for="item in DEMO_TEXT_SAMPLES"
          :key="item.id"
          size="small"
          type="primary"
          link
          :disabled="submitting"
          @click="runTextDemo(item)"
        >
          {{ item.title }}
        </el-button>
      </div>
      <div class="demo-row">
        <span class="demo-cat">示例图片</span>
        <el-button
          v-for="item in DEMO_IMAGE_SAMPLES"
          :key="item.id"
          size="small"
          type="primary"
          link
          :disabled="submitting"
          @click="runImageDemo(item)"
        >
          {{ item.title }}
        </el-button>
      </div>
    </div>

    <p class="domain-hint" role="note">
      识别<strong>侧重医疗、养生、科技</strong>三大类伪科普语境；提交后由系统自动匹配研判，无需手动选择场景。
    </p>

    <el-tabs v-model="activeTab" type="border-card" class="upload-tabs">
      <!-- 文本上传 -->
      <el-tab-pane label="文本识别" name="text">
        <div class="text-upload-area">
          <el-input
            v-model="textContent"
            type="textarea"
            :rows="8"
            :maxlength="TEXT_MAX_LENGTH"
            show-word-limit
            placeholder="请粘贴或输入需要识别的科普文本内容，支持最多5000字"
          />
          <div class="upload-tip">
            <el-text type="info">支持纯文本识别；结合医疗 / 养生 / 科技语境自动分析伪科普特征</el-text>
          </div>
        </div>
      </el-tab-pane>

      <!-- 图片上传 -->
      <el-tab-pane label="图片识别" name="image">
        <div class="image-upload-area">
          <el-upload
            ref="imageUploadRef"
            v-model:file-list="imageFileList"
            :limit="9"
            :accept="IMAGE_ACCEPT_HTML"
            :auto-upload="false"
            :on-exceed="handleExceed"
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">
            <el-text type="info">支持单张/多张图片上传（JPG、PNG，单张≤5MB）；OCR 提取文字后按医疗 / 养生 / 科技语境研判</el-text>
          </div>
        </div>
      </el-tab-pane>

      <!-- 图文混合上传 -->
      <el-tab-pane label="图文混合识别" name="mix">
        <div class="mix-upload-area">
          <div class="mix-text-area">
            <el-input
              v-model="mixTextContent"
              type="textarea"
              :rows="4"
              :maxlength="TEXT_MAX_LENGTH"
              show-word-limit
              placeholder="请输入配套的文本内容"
            />
          </div>
          <div class="mix-image-area">
            <el-upload
              ref="mixImageUploadRef"
              v-model:file-list="mixImageFileList"
              :limit="9"
              :accept="IMAGE_ACCEPT_HTML"
              :auto-upload="false"
              :on-exceed="handleExceed"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </div>
          <div class="upload-tip">
            <el-text type="info">图文联合分析；侧重医疗、养生、科技类伪科普及图文不符场景</el-text>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <div class="submit-area">
      <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
        立即识别
      </el-button>
      <el-button size="large" @click="handleReset">清空内容</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useIdentifyStore } from '@/stores/identify'
import { ElMessage, ElLoading } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  TEXT_MAX_LENGTH,
  IMAGE_ACCEPT,
  IMAGE_ACCEPT_HTML,
  validateImage,
  validateTextLength
} from '@/utils/validate'
import { DEMO_TEXT_SAMPLES, DEMO_IMAGE_SAMPLES } from '@/data/demoSamples'

const router = useRouter()
const identifyStore = useIdentifyStore()

// 状态定义
const activeTab = ref('text')
const submitting = ref(false)
// 文本上传
const textContent = ref('')
// 图片上传
const imageUploadRef = ref()
const imageFileList = ref([])
// 图文混合上传
const mixTextContent = ref('')
const mixImageUploadRef = ref()
const mixImageFileList = ref([])

// 常量导出
defineExpose({
  TEXT_MAX_LENGTH,
  IMAGE_ACCEPT,
  IMAGE_ACCEPT_HTML
})

/** 示例：填入训练集文案并立即识别（不走 Redis 推理缓存） */
const runTextDemo = async (item) => {
  activeTab.value = 'text'
  textContent.value = item.text
  await nextTick()
  await handleSubmit({ skipInferCache: true })
}

/** 示例：拉取 public 下示意配图并立即识别（不走 Redis 推理缓存） */
const runImageDemo = async (item) => {
  activeTab.value = 'image'
  imageFileList.value = []
  await nextTick()
  try {
    const res = await fetch(item.src)
    if (!res.ok) throw new Error(`加载示例图失败：${res.status}`)
    const blob = await res.blob()
    const baseName = item.src.split('/').pop() || 'demo.jpg'
    const file = new File([blob], baseName, {
      type: blob.type || 'image/jpeg'
    })
    const url = URL.createObjectURL(blob)
    imageFileList.value = [
      {
        uid: Date.now(),
        name: file.name,
        raw: file,
        url
      }
    ]
    await nextTick()
    await handleSubmit({ skipInferCache: true })
  } catch (e) {
    console.error(e)
    ElMessage.error(e?.message || '示例图片加载失败')
  }
}

// 超出文件数量限制
const handleExceed = () => {
  ElMessage.warning('最多只能上传9张图片')
}

// 表单重置
const handleReset = () => {
  if (activeTab.value === 'text') {
    textContent.value = ''
  } else if (activeTab.value === 'image') {
    imageFileList.value = []
  } else if (activeTab.value === 'mix') {
    mixTextContent.value = ''
    mixImageFileList.value = []
  }
}

// 提交识别；opts.skipInferCache：示例一键体验时跳过服务端 Redis 推理缓存
const handleSubmit = async (opts = {}) => {
  const formData = new FormData()
  let validatePass = true

  if (opts.skipInferCache) {
    formData.append('skip_infer_cache', '1')
  }

  // 按不同标签校验数据
  if (activeTab.value === 'text') {
    validatePass = validateTextLength(textContent.value)
    if (validatePass) {
      formData.append('content_type', 'text')
      formData.append('content_text', textContent.value.trim())
    }
  } else if (activeTab.value === 'image') {
    if (imageFileList.value.length === 0) {
      ElMessage.error('请上传需要识别的图片')
      validatePass = false
    } else {
      for (const item of imageFileList.value) {
        const blob = item.raw ?? item
        if (!(blob instanceof Blob) || !validateImage(blob)) {
          validatePass = false
          break
        }
      }
      if (validatePass) {
        formData.append('content_type', 'image')
        imageFileList.value.forEach((file) => {
          const blob = file.raw ?? file
          if (blob instanceof Blob) {
            formData.append('image_files', blob)
          }
        })
      }
    }
  } else if (activeTab.value === 'mix') {
    const hasText = mixTextContent.value.trim().length > 0
    const hasImage = mixImageFileList.value.length > 0
    if (!hasText && !hasImage) {
      ElMessage.error('请输入文本或上传图片')
      validatePass = false
    } else {
      formData.append('content_type', 'mix')
      if (hasText) formData.append('content_text', mixTextContent.value.trim())
      if (hasImage) {
        for (const item of mixImageFileList.value) {
          const blob = item.raw ?? item
          if (!(blob instanceof Blob) || !validateImage(blob)) {
            validatePass = false
            break
          }
        }
      }
      if (validatePass) {
        mixImageFileList.value.forEach((file) => {
          const blob = file.raw ?? file
          if (blob instanceof Blob) {
            formData.append('image_files', blob)
          }
        })
      }
    }
  }

  if (!validatePass) return

  // 提交接口
  let loadingInst = null
  try {
    submitting.value = true
    loadingInst = ElLoading.service({
      lock: true,
      text: '正在识别：首次加载大模型可能需数分钟，请耐心等待…',
      background: 'rgba(255, 255, 255, 0.85)'
    })
    const res = await identifyStore.submitIdentify(formData)
    ElMessage.success('识别完成')
    router.push(`/result/${res.content_id}`)
  } catch (error) {
    console.error('识别提交失败', error)
    // Axios 错误（含超时、4xx/5xx）已在 request 拦截器里提示；仅补充非 HTTP 异常
    if (!axios.isAxiosError(error)) {
      ElMessage.error(error?.message || '识别失败')
    }
  } finally {
    loadingInst?.close()
    submitting.value = false
  }
}
</script>

<style scoped>
.upload-container {
  width: 100%;
}
.domain-hint {
  margin: 0 0 16px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.55;
  color: #606266;
  text-align: center;
  background: linear-gradient(135deg, #f5f9ff 0%, #fafcff 100%);
  border: 1px solid #d9ecff;
  border-radius: 8px;
}
.domain-hint strong {
  color: #303133;
  font-weight: 600;
}
.quick-demos {
  margin-bottom: 20px;
  padding: 16px 18px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f0f7ff 0%, #f8fbff 100%);
  border: 1px solid #d9ecff;
}
.quick-demos-title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.demo-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin-bottom: 10px;
}
.demo-row:last-child {
  margin-bottom: 0;
}
.demo-cat {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  min-width: 4.5em;
}
.upload-tabs {
  margin-bottom: 24px;
}
.text-upload-area,
.image-upload-area,
.mix-upload-area {
  min-height: 200px;
}
.mix-text-area {
  margin-bottom: 16px;
}
.upload-tip {
  margin-top: 12px;
  padding-left: 4px;
}
.submit-area {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 16px 0;
}
</style>