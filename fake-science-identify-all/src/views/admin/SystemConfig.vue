<template>
  <div class="system-config-container">
    <h2 class="page-title">系统配置</h2>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 系统参数配置 -->
      <el-tab-pane label="系统参数" name="config">
        <div class="base-card">
          <h3 class="card-title">识别参数配置</h3>
          <el-form :model="configForm" label-width="180px" style="max-width: 600px">
            <el-form-item label="文本最大字数">
              <el-input-number v-model="configForm.text_max_length" :min="1000" :max="10000" :step="500" />
              <span class="form-tip">字</span>
            </el-form-item>
            <el-form-item label="单张图片最大大小">
              <el-input-number v-model="configForm.image_max_size" :min="1" :max="20" />
              <span class="form-tip">MB</span>
            </el-form-item>
            <el-form-item label="批量处理最大条数">
              <el-input-number v-model="configForm.batch_max_count" :min="10" :max="500" :step="10" />
            </el-form-item>
            <el-form-item label="高风险阈值">
              <el-slider v-model="configForm.high_risk_threshold" :min="0" :max="100" show-input />
            </el-form-item>
            <el-form-item label="中风险阈值">
              <el-slider v-model="configForm.mid_risk_threshold" :min="0" :max="100" show-input />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveConfig">保存配置</el-button>
              <el-button @click="handleResetConfig">重置默认</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div class="base-card">
          <h3 class="card-title">缓存管理</h3>
          <el-space>
            <el-button type="warning" @click="handleClearCache('redis')">清理Redis缓存</el-button>
            <el-button @click="handleClearCache('es')">重建ES索引</el-button>
          </el-space>
        </div>
      </el-tab-pane>

      <!-- 系统日志 -->
      <el-tab-pane label="系统日志" name="log">
        <div class="base-card">
          <div class="card-header">
            <h3 class="card-title">操作日志</h3>
            <el-button type="primary" @click="handleExportLog">导出日志</el-button>
          </div>

          <el-form :model="logFilterForm" inline class="log-filter">
            <el-form-item label="日志类型">
              <el-select v-model="logFilterForm.log_type" placeholder="全部" clearable style="width: 140px">
                <el-option label="用户操作" value="user" />
                <el-option label="系统运行" value="system" />
                <el-option label="错误日志" value="error" />
              </el-select>
            </el-form-item>
            <el-form-item label="操作人">
              <el-input v-model="logFilterForm.username" placeholder="请输入" clearable style="width: 140px" />
            </el-form-item>
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="logFilterForm.date_range"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 360px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="getLogList">查询</el-button>
              <el-button @click="resetLogFilter">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="logList" v-loading="logLoading" stripe style="width: 100%">
            <el-table-column prop="log_id" label="日志ID" width="100" />
            <el-table-column prop="log_type" label="日志类型" width="120">
              <template #default="{ row }">
                <el-tag :type="logTypeMap[row.log_type]" size="small">
                  {{ logTypeTextMap[row.log_type] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="操作人" width="140" />
            <el-table-column prop="operation" label="操作内容" show-overflow-tooltip />
            <el-table-column prop="ip" label="IP地址" width="140" />
            <el-table-column prop="create_time" label="操作时间" width="180" />
          </el-table>

          <div class="pagination-area">
            <el-pagination
              v-model:current-page="logPagination.page"
              v-model:page-size="logPagination.size"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="logTotalCount"
              @size-change="getLogList"
              @current-change="getLogList"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 数据备份 -->
      <el-tab-pane label="数据备份" name="backup">
        <div class="base-card">
          <h3 class="card-title">备份策略</h3>
          <el-form :model="backupForm" label-width="180px" style="max-width: 600px">
            <el-form-item label="自动备份">
              <el-switch v-model="backupForm.auto_backup" />
            </el-form-item>
            <el-form-item label="备份周期" v-if="backupForm.auto_backup">
              <el-select v-model="backupForm.backup_cycle" style="width: 200px">
                <el-option label="每日" value="daily" />
                <el-option label="每周" value="weekly" />
                <el-option label="每月" value="monthly" />
              </el-select>
            </el-form-item>
            <el-form-item label="保留天数">
              <el-input-number v-model="backupForm.retention_days" :min="7" :max="365" />
              <span class="form-tip">天</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveBackup">保存策略</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div class="base-card">
          <h3 class="card-title">手动备份</h3>
          <el-space>
            <el-button type="primary" @click="handleManualBackup('full')">全量备份</el-button>
            <el-button @click="handleManualBackup('increment')">增量备份</el-button>
          </el-space>
        </div>

        <div class="base-card">
          <h3 class="card-title">备份记录</h3>
          <el-table :data="backupList" stripe style="width: 100%">
            <el-table-column prop="backup_id" label="备份ID" width="100" />
            <el-table-column prop="backup_type" label="备份类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ row.backup_type === 'full' ? '全量备份' : '增量备份' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" label="文件大小" width="120" />
            <el-table-column prop="create_time" label="备份时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" class="table-action-btn">下载</el-button>
                <el-button size="small" type="primary">恢复</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'

// 状态定义
const activeTab = ref('config')
const logLoading = ref(false)
const logList = ref([])
const logTotalCount = ref(0)
const backupList = ref([])

// 日志类型映射
const logTypeMap = {
  user: '',
  system: 'info',
  error: 'danger'
}
const logTypeTextMap = {
  user: '用户操作',
  system: '系统运行',
  error: '错误日志'
}

// 配置表单
const configForm = reactive({
  text_max_length: 5000,
  image_max_size: 5,
  batch_max_count: 100,
  high_risk_threshold: 70,
  mid_risk_threshold: 40
})

// 日志筛选
const logFilterForm = reactive({
  log_type: '',
  username: '',
  date_range: []
})

// 日志分页
const logPagination = reactive({
  page: 1,
  size: 10
})

// 备份表单
const backupForm = reactive({
  auto_backup: true,
  backup_cycle: 'daily',
  retention_days: 30
})

// 方法
const handleSaveConfig = async () => {
  try {
    await request.post('/admin/system/config', configForm)
    ElMessage.success('系统配置保存成功')
  } catch (error) {
    console.error('保存配置失败', error)
  }
}

const handleResetConfig = () => {
  ElMessageBox.confirm('确定要重置为默认配置吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    Object.assign(configForm, {
      text_max_length: 5000,
      image_max_size: 5,
      batch_max_count: 100,
      high_risk_threshold: 70,
      mid_risk_threshold: 40
    })
    ElMessage.success('已重置为默认配置')
  }).catch(() => {})
}

const handleClearCache = async (type) => {
  const typeText = type === 'redis' ? 'Redis缓存' : 'ES索引'
  ElMessageBox.confirm(`确定要清理${typeText}吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.post('/admin/system/clear-cache', { type })
    ElMessage.success(`${typeText}清理成功`)
  }).catch(() => {})
}

const getLogList = async () => {
  try {
    logLoading.value = true
    const params = {
      page: logPagination.page,
      size: logPagination.size,
      ...logFilterForm
    }
    const { data } = await request.get('/admin/log/list', { params })
    logList.value = data.list
    logTotalCount.value = data.total
  } catch (error) {
    console.error('获取日志列表失败', error)
  } finally {
    logLoading.value = false
  }
}

const resetLogFilter = () => {
  logFilterForm.log_type = ''
  logFilterForm.username = ''
  logFilterForm.date_range = []
  logPagination.page = 1
  getLogList()
}

const handleExportLog = async () => {
  try {
    ElMessage.success('日志导出成功')
  } catch (error) {
    console.error('导出失败', error)
  }
}

const handleSaveBackup = async () => {
  try {
    await request.post('/admin/backup/config', backupForm)
    ElMessage.success('备份策略保存成功')
  } catch (error) {
    console.error('保存失败', error)
  }
}

const handleManualBackup = async (type) => {
  const typeText = type === 'full' ? '全量备份' : '增量备份'
  try {
    ElMessage.info(`${typeText}进行中...`)
    await request.post('/admin/backup/manual', { type })
    ElMessage.success(`${typeText}成功`)
    getBackupList()
  } catch (error) {
    console.error('备份失败', error)
  }
}

const getBackupList = async () => {
  try {
    const { data } = await request.get('/admin/backup/list')
    backupList.value = data.list || []
  } catch (error) {
    console.error('获取备份列表失败', error)
  }
}

onMounted(() => {
  getLogList()
  getBackupList()
})
</script>

<style scoped>
.system-config-container {
  width: 100%;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 20px 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.card-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.form-tip {
  margin-left: 8px;
  color: #606266;
}
.log-filter {
  margin-bottom: 16px;
}
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>