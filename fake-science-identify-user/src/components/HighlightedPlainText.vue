<template>
  <p class="highlight-plain">
    <template v-for="(seg, i) in segments" :key="i">
      <mark v-if="seg.mark" class="risk-mark">{{ seg.text }}</mark>
      <template v-else>{{ seg.text }}</template>
    </template>
  </p>
</template>

<script setup>
import { computed } from 'vue'
import { buildRiskHighlightSegments } from '@/utils/riskHighlight'

const props = defineProps({
  text: { type: String, default: '' },
  coreFeatures: { type: Array, default: () => [] },
  bertLabels: { type: Array, default: () => [] }
})

const segments = computed(() =>
  buildRiskHighlightSegments(props.text, {
    core_features: props.coreFeatures,
    bert_labels: props.bertLabels
  })
)
</script>

<style scoped>
.highlight-plain {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.risk-mark {
  background: transparent;
  color: #f53f3f;
  font-weight: 600;
  padding: 0 1px;
}
</style>
