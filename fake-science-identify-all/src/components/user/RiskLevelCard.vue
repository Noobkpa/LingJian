<template>
  <div class="risk-card" :class="`risk-${riskLevel}`">
    <div class="risk-header">
      <div class="risk-icon">
        <img :src="riskIcon" alt="风险等级" />
      </div>
      <div class="risk-info">
        <h2 class="risk-title">{{ riskTitle }}</h2>
        <p class="risk-score">综合风险得分：<span>{{ riskScore }}</span> 分</p>
      </div>
    </div>
    <div class="risk-basis">
      <h3 class="basis-title">判定依据</h3>
      <div class="basis-content" v-if="judgmentBasis && judgmentBasis.length">
        <div v-for="(item, index) in judgmentBasis" :key="index" class="basis-item">
          <el-tag :type="tagType" size="small" class="item-tag">{{ index + 1 }}</el-tag>
          <span class="item-text">{{ item }}</span>
        </div>
      </div>
      <el-empty v-else description="暂无判定依据" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 组件入参
const props = defineProps({
  riskLevel: {
    type: String,
    default: 'low', // high/middle/low
    required: true
  },
  riskScore: {
    type: Number,
    default: 0,
    required: true
  },
  judgmentBasis: {
    type: Array,
    default: () => []
  }
})

// 计算属性
const riskTitle = computed(() => {
  const map = {
    high: '高风险 · 疑似伪科普',
    middle: '中风险 · 需谨慎阅读',
    low: '低风险 · 可信科普内容'
  }
  return map[props.riskLevel] || '未知风险'
})

const riskIcon = computed(() => {
  const map = {
    high: new URL('@/assets/images/risk-high.png', import.meta.url).href,
    middle: new URL('@/assets/images/risk-middle.png', import.meta.url).href,
    low: new URL('@/assets/images/risk-low.png', import.meta.url).href
  }
  return map[props.riskLevel] || map.low
})

const tagType = computed(() => {
  const map = {
    high: 'danger',
    middle: 'warning',
    low: 'success'
  }
  return map[props.riskLevel] || 'info'
})
</script>

<style scoped>
.risk-card {
  width: 100%;
  border-radius: 12px;
  padding: 24px;
  background: #fff;
  border: 2px solid #ebeef5;
}
.risk-card.risk-high {
  border-color: #F53F3F;
}
.risk-card.risk-middle {
  border-color: #FF7D00;
}
.risk-card.risk-low {
  border-color: #00B42A;
}
.risk-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 20px;
}
.risk-icon img {
  width: 48px;
  height: 48px;
}
.risk-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}
.risk-high .risk-title {
  color: #F53F3F;
}
.risk-middle .risk-title {
  color: #FF7D00;
}
.risk-low .risk-title {
  color: #00B42A;
}
.risk-score {
  font-size: 14px;
  color: #606266;
}
.risk-score span {
  font-size: 18px;
  font-weight: bold;
}
.risk-high .risk-score span {
  color: #F53F3F;
}
.risk-middle .risk-score span {
  color: #FF7D00;
}
.risk-low .risk-score span {
  color: #00B42A;
}
.basis-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 12px;
  color: #303133;
}
.basis-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.basis-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.item-tag {
  flex-shrink: 0;
  margin-top: 2px;
}
.item-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}
</style>