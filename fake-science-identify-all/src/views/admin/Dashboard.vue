<template>
  <div class="dashboard-container">
    <h2 class="page-title">数据看板</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <StatCard
          title="今日识别量"
          :value="statsData.today_count || 0"
          desc="较昨日 +12%"
          color="#1890ff"
          icon="DataLine"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="高风险内容"
          :value="statsData.high_risk_count || 0"
          desc="占比 15.2%"
          color="#ff4d4f"
          icon="Warning"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="活跃用户数"
          :value="statsData.active_user_count || 0"
          desc="较昨日 +8%"
          color="#52c41a"
          icon="User"
        />
      </el-col>
      <el-col :span="6">
        <StatCard
          title="系统识别准确率"
          :value="(statsData.accuracy || 0) + '%'"
          desc="目标 90%"
          color="#faad14"
          icon="CircleCheck"
        />
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="16">
        <div class="base-card">
          <h3 class="card-title">识别量趋势</h3>
          <div ref="trendChartRef" class="chart-container"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="base-card">
          <h3 class="card-title">风险等级分布</h3>
          <div ref="pieChartRef" class="chart-container"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <div class="base-card">
      <h3 class="card-title">快捷操作</h3>
      <el-space wrap>
        <el-button type="primary" @click="goToAudit">内容批量审核</el-button>
        <el-button @click="goToUser">用户管理</el-button>
        <el-button @click="goToModel">模型配置</el-button>
      </el-space>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/admin/audit'
import * as echarts from 'echarts'
import StatCard from '@/components/StatCard.vue'
import { DataLine, Warning, User, CircleCheck } from '@element-plus/icons-vue'

const router = useRouter()
const auditStore = useAuditStore()

// 状态定义
const statsData = ref({})
const trendChartRef = ref()
const pieChartRef = ref()
let trendChart = null
let pieChart = null

// 初始化图表
const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '识别量',
        type: 'line',
        smooth: true,
        data: [120, 200, 150, 80, 70, 110, 130],
        areaStyle: { opacity: 0.1 }
      }
    ]
  }
  trendChart.setOption(option)
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%', left: 'center' },
    series: [
      {
        name: '风险等级',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' }
        },
        data: [
          { value: 1048, name: '高风险', itemStyle: { color: '#ff4d4f' } },
          { value: 735, name: '中风险', itemStyle: { color: '#faad14' } },
          { value: 5802, name: '低风险', itemStyle: { color: '#52c41a' } }
        ]
      }
    ]
  }
  pieChart.setOption(option)
}

// 页面跳转
const goToAudit = () => router.push('/content-audit')
const goToUser = () => router.push('/user-manage')
const goToModel = () => router.push('/model-manage')

// 窗口大小变化时重绘图表
const handleResize = () => {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(async () => {
  try {
    statsData.value = await auditStore.getStatsData()
  } catch (error) {
    console.error('获取统计数据失败', error)
  }
  
  await nextTick()
  initTrendChart()
  initPieChart()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时销毁图表
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  width: 100%;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 20px 0;
}
.stat-row {
  margin-bottom: 20px;
}
.chart-row {
  margin-bottom: 20px;
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 16px 0;
}
.chart-container {
  width: 100%;
  height: 300px;
}
</style>