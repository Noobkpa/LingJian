<template>
  <div class="upload-container">
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
            <el-text type="info">支持纯文本内容识别，自动分析文本中的伪科普特征</el-text>
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
            :accept="IMAGE_ACCEPT.join(',')"
            :before-upload="beforeImageUpload"
            :on-exceed="handleExceed"
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">
            <el-text type="info">支持单张/多张图片上传，单张图片大小不超过5MB，仅支持JPG、PNG格式</el-text>
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
              :accept="IMAGE_ACCEPT.join(',')"
              :before-upload="beforeImageUpload"
              :on-exceed="handleExceed"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
          </div>
          <div class="upload-tip">
            <el-text type="info">同时上传文本和图片，系统将综合分析图文内容，精准识别图文不符类伪科普</el-text>
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useIdentifyStore } from '@/stores/user/identify'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  TEXT_MAX_LENGTH,
  IMAGE_ACCEPT,
  validateImage,
  validateTextLength
} from '@/utils/validate'

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
  IMAGE_ACCEPT
})

// 图片上传前校验
const beforeImageUpload = (file) => {
  return validateImage(file)
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

// 提交识别
const handleSubmit = async () => {
  const formData = new FormData()
  let validatePass = true

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
      formData.append('content_type', 'image')
      imageFileList.value.forEach(file => {
        formData.append('image_files', file.raw)
      })
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
      mixImageFileList.value.forEach(file => {
        formData.append('image_files', file.raw)
      })
    }
  }

  if (!validatePass) return

  // 提交接口
  try {
    submitting.value = true
    const res = await identifyStore.submitIdentify(formData)
    ElMessage.success('识别任务提交成功，正在分析中...')
    // 跳转到结果页
    router.push(`/user/result/${res.content_id}`)
  } catch (error) {
    console.error('识别提交失败', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.upload-container {
  width: 100%;
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