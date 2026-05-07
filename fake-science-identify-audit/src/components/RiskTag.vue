<template>
  <el-tag :type="tagType" size="small">
    {{ tagText }}
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: {
    type: String,
    required: true
  }
})

const tagType = computed(() => {
  const map = {
    high: 'danger',
    middle: 'warning',
    low: 'success'
  }
  return map[props.level] || 'info'
})

const tagText = computed(() => {
  const map = {
    high: '高风险',
    middle: '中风险',
    low: '低风险'
  }
  return map[props.level] || '未知'
})
</script>