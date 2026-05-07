<template>
  <div class="empty-container">
    <el-empty :description="description" :image-size="imageSize">
      <template #image>
        <img v-if="imageUrl" :src="imageUrl" alt="empty" />
      </template>
      <slot></slot>
    </el-empty>
  </div>
</template>

<script setup>
const props = defineProps({
  description: {
    type: String,
    default: '暂无数据'
  },
  imageSize: {
    type: Number,
    default: 120
  },
  imageUrl: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.empty-container {
  padding: 40px 0;
  width: 100%;
}
</style>