<template>
  <div class="stat-card" :style="{ borderLeftColor: color }">
    <div class="stat-content">
      <div class="stat-info">
        <p class="stat-title">{{ title }}</p>
        <p class="stat-value">{{ value }}</p>
        <p class="stat-desc" v-if="desc">{{ desc }}</p>
      </div>
      <div class="stat-icon" :style="{ backgroundColor: color + '15' }">
        <el-icon :size="32" :color="color">
          <component :is="icon" />
        </el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  desc: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: '#1890ff'
  },
  icon: {
    type: String,
    default: 'DataLine'
  }
})
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}
.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-info {
  flex: 1;
}
.stat-title {
  font-size: 14px;
  color: #606266;
  margin: 0 0 8px 0;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 4px 0;
}
.stat-desc {
  font-size: 12px;
  color: #909399;
  margin: 0;
}
.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>