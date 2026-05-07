<template>
  <div class="dashboard-container">
    <h2 class="page-title">数据看板</h2>

    <!-- 统计卡片：含今日识别次数、平均推理耗时（与 /admin/stats/model-runtime 一致） -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="8" :lg="4">
        <StatCard
          title="今日识别次数"
          :value="statsData.today_analyze_calls ?? 0"
          desc="当日产生 analyze_results 条数"
          color="#1890ff"
          icon="DataLine"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="4">
        <StatCard
          title="平均推理耗时"
          :value="avgInferenceDisplay"
          desc="含 meta.elapsed_ms 的样本均值"
          color="#722ed1"
          icon="Timer"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="4">
        <StatCard
          title="高风险内容"
          :value="statsData.high_risk_count || 0"
          desc="累计研判含「高」档"
          color="#ff4d4f"
          icon="Warning"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="4">
        <StatCard
          title="活跃用户数"
          :value="statsData.active_user_count || 0"
          desc="注册用户数"
          color="#52c41a"
          icon="User"
        />
      </el-col>
      <el-col :xs="24" :sm="12" :md="8" :lg="8">
        <StatCard
          title="系统识别准确率"
          :value="accuracyDisplay"
          :desc="accuracyDesc"
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
import { ref, onMounted, nextTick, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditStore } from '@/stores/audit'
import * as echarts from 'echarts'
import StatCard from '@/components/StatCard.vue'

const router = useRouter()
const auditStore = useAuditStore()

// 状态定义
const statsData = ref({})

const accuracyDisplay = computed(() => {
  const v = statsData.value?.accuracy
  if (typeof v === 'number' && !Number.isNaN(v)) {
    return `${v}%`
  }
  return '—'
})

const avgInferenceDisplay = computed(() => {
  const s = statsData.value?.avg_inference_sec
  if (s == null || s === '') return '—'
  const n = Number(s)
  if (!Number.isFinite(n)) return '—'
  return `${n}s`
})

const accuracyDesc = computed(() => {
  const n = statsData.value?.accuracy_review_count ?? 0
  if (typeof statsData.value?.accuracy === 'number' && n > 0) {
    return `已终审 ${n} 条：与列表一致的风险档位（高/中 vs 低）对比人工是否认定伪科普`
  }
  return '暂无已终审样本；终审后可统计'
})

function padLocalDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const trendChartRef = ref()
const pieChartRef = ref()
let trendChart = null
let pieChart = null

// 初始化图表（数据来自 /admin/stats/daily 与 risk_buckets）
const initTrendChart = () => {
  if (!trendChartRef.value) return
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
  trendChart = echarts.init(trendChartRef.value)
  const seriesMap = statsData.value?.daily_series || {}
  const labels = []
  const values = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setHours(0, 0, 0, 0)
    d.setDate(d.getDate() - i)
    const key = padLocalDate(d)
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`)
    values.push(Number(seriesMap[key]) || 0)
  }
  const option = {
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: labels
    },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        name: '识别量',
        type: 'line',
        smooth: true,
        data: values,
        areaStyle: { opacity: 0.1 }
      }
    ]
  }
  trendChart.setOption(option)
}

const initPieChart = () => {
  if (!pieChartRef.value) return
  if (pieChart) {
    pieChart.dispose()
    pieChart = null
  }
  pieChart = echarts.init(pieChartRef.value)
  const b = statsData.value?.risk_buckets?.buckets || {}
  const hi = Number(b['高']) || 0
  const mid = Number(b['中']) || 0
  const low = Number(b['低']) || 0
  const data = [
    { value: hi, name: '高风险', itemStyle: { color: '#ff4d4f' } },
    { value: mid, name: '中风险', itemStyle: { color: '#faad14' } },
    { value: low, name: '低风险', itemStyle: { color: '#52c41a' } }
  ]
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
        data
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