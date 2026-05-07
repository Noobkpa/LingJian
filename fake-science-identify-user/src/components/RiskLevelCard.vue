<template>
  <div class="risk-card" :class="`risk-${riskLevel}`">
    <div class="risk-header">
      <div class="risk-icon" aria-hidden="true">
        <el-icon :size="48">
          <component :is="riskIconComponent" />
        </el-icon>
      </div>
      <div class="risk-info">
        <h2 class="risk-title">{{ riskTitle }}</h2>
        <p class="risk-score">综合风险得分：<span>{{ displayScore }}</span> 分</p>
      </div>
    </div>

    <div class="risk-basis">
      <h3 class="basis-title">判定依据</h3>
      <div class="basis-structured">
        <section class="dim-block">
          <h4 class="dim-title">逻辑谬误</h4>
          <p class="dim-body">{{ displayLogical }}</p>
        </section>
        <section class="dim-block">
          <h4 class="dim-title">科学事实错误</h4>
          <p class="dim-body">{{ displayScientific }}</p>
        </section>
        <section class="dim-block pillar-block">
          <h4 class="dim-title">为何仍可能成立 / 为何不直接否定</h4>
          <p class="dim-body">{{ displayWhySound }}</p>
        </section>
        <section class="dim-block pillar-block">
          <h4 class="dim-title">为何存在风险或问题</h4>
          <p class="dim-body">{{ displayWhyRisky }}</p>
        </section>
        <section class="dim-block pillar-block">
          <h4 class="dim-title">建议您怎么做</h4>
          <p class="dim-body">{{ displayReaderActions }}</p>
        </section>
        <section class="dim-block">
          <h4 class="dim-title">核心特征</h4>
          <div v-if="coreFeaturesList.length" class="feature-tags">
            <el-tag
              v-for="(tag, i) in coreFeaturesList"
              :key="i"
              :type="tagType"
              effect="plain"
              class="feat-tag"
            >
              {{ tag }}
            </el-tag>
          </div>
          <p v-else class="dim-body muted">暂无显性命中特征</p>
        </section>
        <section class="dim-block summary-block">
          <h4 class="dim-title">综合判定依据</h4>
          <p class="dim-body summary-text">{{ displaySummary }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { WarningFilled, Warning, CircleCheck, QuestionFilled } from '@element-plus/icons-vue'

const props = defineProps({
  riskLevel: {
    type: String,
    default: 'low',
    required: true
  },
  riskScore: {
    type: Number,
    default: 0,
    required: true
  },
  /** 标准输出：逻辑谬误说明 */
  logicalFallacy: { type: String, default: '' },
  /** 标准输出：科学事实错误 */
  scientificError: { type: String, default: '' },
  /** 相对可信或为何不直接否定的说明 */
  whySound: { type: String, default: '' },
  /** 风险与问题点的叙事说明 */
  whyRisky: { type: String, default: '' },
  /** 读者可执行建议 */
  readerActions: { type: String, default: '' },
  /** 标准输出：核心特征标签 */
  coreFeatures: { type: Array, default: () => [] },
  /** 综合判定段落（judgment_basis 全文） */
  judgmentSummary: { type: String, default: '' }
})

const riskTitle = computed(() => {
  const map = {
    high: '高风险 · 疑似伪科普',
    middle: '中风险 · 需谨慎阅读',
    low: '低风险 · 可信科普内容'
  }
  return map[props.riskLevel] || '未知风险'
})

const riskIconComponent = computed(() => {
  const map = {
    high: WarningFilled,
    middle: Warning,
    low: CircleCheck
  }
  return map[props.riskLevel] || QuestionFilled
})

const tagType = computed(() => {
  const map = {
    high: 'danger',
    middle: 'warning',
    low: 'success'
  }
  return map[props.riskLevel] || 'info'
})

const displayScore = computed(() => {
  const n = Number(props.riskScore)
  if (Number.isNaN(n)) return '0'
  const r = Math.round(n * 10) / 10
  return Number.isInteger(r) ? String(r) : r.toFixed(1)
})

const dash = '—'

const displayLogical = computed(() => {
  const s = String(props.logicalFallacy || '').trim()
  return s || dash
})

const displayScientific = computed(() => {
  const s = String(props.scientificError || '').trim()
  return s || dash
})

const displayWhySound = computed(() => {
  const s = String(props.whySound || '').trim()
  return s || dash
})

const displayWhyRisky = computed(() => {
  const s = String(props.whyRisky || '').trim()
  return s || dash
})

const displayReaderActions = computed(() => {
  const s = String(props.readerActions || '').trim()
  return s || dash
})

const coreFeaturesList = computed(() =>
  (props.coreFeatures || []).map((x) => String(x).trim()).filter(Boolean)
)

const displaySummary = computed(() => {
  const s = String(props.judgmentSummary || '').trim()
  return s || '暂无综合说明。'
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
  border-color: #f53f3f;
}
.risk-card.risk-middle {
  border-color: #ff7d00;
}
.risk-card.risk-low {
  border-color: #00b42a;
}
.risk-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 20px;
}
.risk-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}
.risk-high .risk-icon {
  color: #f53f3f;
}
.risk-middle .risk-icon {
  color: #ff7d00;
}
.risk-low .risk-icon {
  color: #00b42a;
}
.risk-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}
.risk-high .risk-title {
  color: #f53f3f;
}
.risk-middle .risk-title {
  color: #ff7d00;
}
.risk-low .risk-title {
  color: #00b42a;
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
  color: #f53f3f;
}
.risk-middle .risk-score span {
  color: #ff7d00;
}
.risk-low .risk-score span {
  color: #00b42a;
}
.basis-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 16px;
  color: #303133;
}
.basis-structured {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.dim-block {
  padding: 14px 0;
  border-bottom: 1px solid #ebeef5;
}
.dim-block:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.dim-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin: 0 0 8px;
}
.dim-body {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  color: #303133;
  white-space: pre-wrap;
}
.dim-body.muted {
  color: #909399;
}
.summary-block .dim-title {
  color: #303133;
}
.summary-text {
  font-size: 14px;
  line-height: 1.8;
}
.pillar-block .dim-title {
  color: #409eff;
}
.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.feat-tag {
  margin: 0;
}
</style>
