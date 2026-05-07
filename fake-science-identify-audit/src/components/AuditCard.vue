<template>
  <div class="audit-card" @click="handleClick">
    <div class="card-header">
      <div class="header-left">
        <el-tag size="small" :type="contentTypeTag">
          {{ content_type === 'text' ? '文本' : '图片' }}
        </el-tag>
        <RiskTag :level="risk_level" class="ml-2" />
      </div>
      <div class="header-right">
        <span class="score-badge">AI得分：{{ llm_score }}</span>
      </div>
    </div>

    <div class="card-body">
      <p class="content-preview">{{ content_text }}</p>
    </div>

    <div class="card-footer">
      <span class="footer-item">
        <el-icon><User /></el-icon>
        {{ upload_user }}
      </span>
      <span class="footer-item">
        <el-icon><Clock /></el-icon>
        {{ upload_time }}
      </span>
      <el-button type="primary" size="small" class="audit-btn">
        开始审核
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import RiskTag from './RiskTag.vue'
import { User, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  content_id: {
    type: [Number, String],
    required: true
  },
  content_type: {
    type: String,
    default: 'text'
  },
  content_text: {
    type: String,
    default: ''
  },
  risk_level: {
    type: String,
    required: true
  },
  llm_score: {
    type: Number,
    default: 0
  },
  upload_user: {
    type: String,
    default: ''
  },
  upload_time: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['click'])

// 计算属性
const contentTypeTag = computed(() => {
  return props.content_type === 'text' ? '' : 'warning'
})

// 截断长文本
const contentPreview = computed(() => {
  const text = props.content_text || ''
  return text.length > 100 ? text.slice(0, 100) + '...' : text
})

// 事件
const handleClick = () => {
  emit('click', props.content_id)
}
</script>

<style scoped>
.audit-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.audit-card:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: center;
}

.ml-2 {
  margin-left: 8px;
}

.score-badge {
  font-size: 14px;
  font-weight: bold;
  color: #409eff;
}

.card-body {
  margin-bottom: 12px;
}

.content-preview {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.audit-btn {
  margin-left: auto;
}
</style>