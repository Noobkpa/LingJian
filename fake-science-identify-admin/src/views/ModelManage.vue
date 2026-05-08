<template>
  <div class="model-manage-container">
    <h2 class="page-title">模型与Prompt管理</h2>

    <div class="base-card runtime-card">
      <h3 class="card-title">模型运行状态</h3>
      <el-row :gutter="16">
        <el-col :span="8">
          <div class="status-item">
            <span class="label">模型状态</span>
            <el-tag type="success">运行正常</el-tag>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <span class="label">今日调用次数</span>
            <span class="value">{{ formatInt(modelRuntime.today_calls) }}</span>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="status-item">
            <span class="label">平均推理耗时</span>
            <span class="value">{{ formatAvgLatency(modelRuntime.avg_elapsed_sec) }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 模型配置 -->
      <el-tab-pane label="模型配置" name="model">
        <div class="base-card">
          <h3 class="card-title">大模型配置</h3>
          <el-form :model="modelForm" label-width="140px" style="max-width: 600px">
            <el-form-item label="当前模型版本">
              <el-select v-model="modelForm.model_version" style="width: 100%">
                <el-option label="通义千问 qwen-plus" value="qwen_v2" />
                <el-option label="本地 Qwen（历史兼容）" value="qwen_v1" />
              </el-select>
            </el-form-item>
            <el-form-item label="生效 Prompt 场景">
              <el-select v-model="modelForm.prompt_scene" placeholder="与下方模板列表中的「适用场景」对应" style="width: 100%">
                <el-option label="通用类 general" value="general" />
                <el-option label="养生类 health" value="health" />
                <el-option label="医疗类 medical" value="medical" />
                <el-option label="科技类 tech" value="tech" />
              </el-select>
              <el-alert
                class="scene-hint"
                type="info"
                :closable="false"
                show-icon
                title="关闭「按文本自动选场景」时，固定使用此处场景；若不想走 general，请选择 health/medical/tech 且确保下方对应场景模板为启用状态后保存。开启自动时，系统按正文与 BERT 摘要推断 medical/health/tech/general。"
              />
            </el-form-item>
            <el-form-item label="按文本自动选场景">
              <div class="auto-scene-row">
                <el-switch
                  v-model="modelForm.auto_prompt_scene"
                  inline-prompt
                  active-text="开"
                  inactive-text="关"
                />
                <span class="auto-scene-desc">
                  开启后每次识别按内容选模板场景；关闭则固定使用上一项「生效 Prompt 场景」。
                </span>
              </div>
            </el-form-item>
            <el-form-item label="推理权重量化">
              <el-radio-group v-model="modelForm.quantization">
                <el-radio label="8bit">8bit（省显存，需 bitsandbytes）</el-radio>
                <el-radio label="16bit">16bit FP16（更稳）</el-radio>
              </el-radio-group>
              <div class="auto-scene-desc">仅影响 GPU；CPU 始终为 float32。若 8bit 报错请改 16bit 并保存。</div>
            </el-form-item>
            <el-form-item label="推理置信度阈值">
              <el-slider v-model="modelForm.confidence" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveModel">保存配置</el-button>
              <el-button @click="handleTestModel">测试模型</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- Prompt模板管理 -->
      <el-tab-pane label="Prompt模板管理" name="prompt">
        <div class="base-card">
          <el-alert
            v-if="duplicateEnabledScenes.length"
            class="prompt-dup-alert"
            type="warning"
            :closable="false"
            show-icon
          >
            <template #title>
              以下场景有多条「启用」模板，推理会优先用其中<strong>最近更新</strong>的一条；不需要的请禁用或改场景以免混淆：
              {{ duplicateEnabledScenes.join('、') }}
            </template>
          </el-alert>
          <div class="card-header">
            <h3 class="card-title">Prompt模板列表</h3>
            <el-button type="primary" @click="showPromptDialog = true">新增模板</el-button>
          </div>

          <el-table :data="promptList" stripe style="width: 100%">
            <el-table-column prop="prompt_id" label="模板ID" width="100" />
            <el-table-column prop="prompt_name" label="模板名称" width="180" />
            <el-table-column prop="prompt_scene" label="适用场景" width="140">
              <template #default="{ row }">
                <el-tag size="small">{{ sceneMap[row.prompt_scene] }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="prompt_content" label="模板内容" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                  {{ row.status === 1 ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="创建时间" width="180" />
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button size="small" class="table-action-btn" @click="handleEditPrompt(row)">编辑</el-button>
                <el-button
                  size="small"
                  class="table-action-btn"
                  :type="row.status === 1 ? 'warning' : 'success'"
                  @click="handleTogglePromptStatus(row)"
                >
                  {{ row.status === 1 ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="primary" @click="handleTestPrompt(row)">测试</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- Prompt编辑弹窗 -->
        <el-dialog
          v-model="showPromptDialog"
          :title="isEditPrompt ? '编辑模板' : '新增模板'"
          width="600px"
          @close="resetPromptForm"
        >
          <el-form
            ref="promptFormRef"
            :model="promptForm"
            :rules="promptRules"
            label-width="100px"
          >
            <el-form-item label="模板名称" prop="prompt_name">
              <el-input v-model="promptForm.prompt_name" placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="适用场景" prop="prompt_scene">
              <el-select v-model="promptForm.prompt_scene" placeholder="请选择适用场景" style="width: 100%">
                <el-option label="养生类伪科普" value="health" />
                <el-option label="医疗类伪科普" value="medical" />
                <el-option label="科技类伪科普" value="tech" />
                <el-option label="通用类" value="general" />
              </el-select>
            </el-form-item>
            <el-form-item label="模板内容" prop="prompt_content">
              <el-input
                v-model="promptForm.prompt_content"
                type="textarea"
                :rows="8"
                placeholder="请输入Prompt模板内容"
              />
            </el-form-item>
            <el-form-item label="输出格式要求" prop="output_format">
              <el-input
                v-model="promptForm.output_format"
                type="textarea"
                :rows="3"
                placeholder="请输入输出格式要求（JSON格式）"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="showPromptDialog = false">取消</el-button>
            <el-button type="primary" :loading="submitLoading" @click="handleSubmitPrompt">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { V1 } from '@/api/v1/endpoints'

// 状态定义
const activeTab = ref('model')
const submitLoading = ref(false)
const showPromptDialog = ref(false)
const isEditPrompt = ref(false)
const promptFormRef = ref()
const promptList = ref([])

// 场景映射
const sceneMap = {
  health: '养生类',
  medical: '医疗类',
  tech: '科技类',
  general: '通用类'
}

/** 同一场景多条「启用」时用于页内提醒（推理侧已按最近更新优先选一条） */
const duplicateEnabledScenes = computed(() => {
  const list = promptList.value || []
  const counts = new Map()
  for (const row of list) {
    if (!row || Number(row.status) !== 1) continue
    const s = String(row.prompt_scene || '').toLowerCase().trim() || 'general'
    counts.set(s, (counts.get(s) || 0) + 1)
  }
  const out = []
  for (const [scene, n] of counts) {
    if (n <= 1) continue
    const label = sceneMap[scene]
    out.push(label ? `${label}（${scene}）` : scene)
  }
  return out
})

const enabledPromptScenes = computed(() => {
  const scenes = new Set()
  for (const row of promptList.value || []) {
    if (!row || Number(row.status) !== 1) continue
    scenes.add(String(row.prompt_scene || '').toLowerCase().trim() || 'general')
  }
  return scenes
})

const modelRuntime = reactive({
  today_calls: 0,
  avg_elapsed_sec: null
})

function formatInt(n) {
  const x = Number(n)
  if (!Number.isFinite(x)) return '—'
  return new Intl.NumberFormat('zh-CN').format(Math.max(0, Math.floor(x)))
}

/** 今日成功样本上有 meta.elapsed_ms 时才有均值；否则提示暂无 */
function formatAvgLatency(sec) {
  if (sec == null || sec === '') return '—'
  const s = Number(sec)
  if (!Number.isFinite(s)) return '—'
  return `${s}s`
}

const loadModelRuntime = async () => {
  try {
    const { data } = await request.get(V1.ADMIN_STATS_MODEL_RUNTIME)
    if (data && typeof data === 'object') {
      modelRuntime.today_calls = data.today_calls ?? 0
      modelRuntime.avg_elapsed_sec = data.avg_elapsed_sec ?? null
    }
  } catch (e) {
    console.error('加载模型运行统计失败', e)
  }
}

// 模型表单
const modelForm = reactive({
  model_version: 'qwen_v2',
  quantization: '8bit',
  confidence: 0.8,
  prompt_scene: 'general',
  auto_prompt_scene: true
})

// Prompt表单
const promptForm = reactive({
  prompt_id: '',
  prompt_name: '',
  prompt_scene: 'general',
  prompt_content: '',
  output_format: ''
})

const promptRules = {
  prompt_name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  prompt_scene: [
    { required: true, message: '请选择适用场景', trigger: 'change' }
  ],
  prompt_content: [
    { required: true, message: '请输入模板内容', trigger: 'blur' }
  ]
}

const loadModelSettings = async () => {
  try {
    const { data } = await request.get('/admin/model/settings')
    if (data && typeof data === 'object') {
      Object.assign(modelForm, data)
      modelForm.auto_prompt_scene = coerceBool(modelForm.auto_prompt_scene, true)
      if (!modelForm.quantization) modelForm.quantization = '8bit'
    }
  } catch (e) {
    console.error('加载模型配置失败', e)
  }
}

function coerceBool(v, defaultVal = true) {
  if (v === undefined || v === null) return defaultVal
  if (typeof v === 'boolean') return v
  if (typeof v === 'number') return v !== 0
  const s = String(v).toLowerCase().trim()
  if (['0', 'false', 'no', 'off'].includes(s)) return false
  if (['1', 'true', 'yes', 'on'].includes(s)) return true
  return defaultVal
}

// 方法
const getPromptList = async () => {
  try {
    const { data } = await request.get('/admin/prompt/list')
    promptList.value = data.list || []
  } catch (error) {
    console.error('获取Prompt列表失败', error)
  }
}

const handleSaveModel = async () => {
  try {
    if (!modelForm.auto_prompt_scene && !enabledPromptScenes.value.has(modelForm.prompt_scene)) {
      ElMessage.warning('当前生效 Prompt 场景没有启用模板，请先启用对应模板或换一个场景')
      return
    }
    const payload = {
      ...modelForm,
      prompt_scene: String(modelForm.prompt_scene || 'general').toLowerCase().trim(),
      auto_prompt_scene: coerceBool(modelForm.auto_prompt_scene, true)
    }
    await request.post('/admin/model/config', payload)
    modelForm.auto_prompt_scene = payload.auto_prompt_scene
    modelForm.prompt_scene = payload.prompt_scene
    ElMessage.success('模型配置保存成功')
  } catch (error) {
    console.error('保存配置失败', error)
  }
}

const handleTestModel = async () => {
  ElMessage.info('模型测试中...')
  try {
    await request.post('/admin/model/test')
    ElMessage.success('模型测试成功，运行正常')
  } catch (error) {
    console.error('测试失败', error)
  }
}

const handleEditPrompt = (row) => {
  isEditPrompt.value = true
  Object.assign(promptForm, row)
  showPromptDialog.value = true
}

const handleTogglePromptStatus = async (row) => {
  try {
    await request.post('/admin/prompt/toggle-status', {
      prompt_id: row.prompt_id,
      status: row.status === 1 ? 0 : 1
    })
    ElMessage.success('状态更新成功')
    getPromptList()
  } catch (error) {
    console.error('更新失败', error)
  }
}

const handleTestPrompt = async (row) => {
  ElMessage.info('Prompt测试中...')
  try {
    await request.post('/admin/prompt/test', { prompt_id: row.prompt_id })
    ElMessage.success('Prompt测试成功')
  } catch (error) {
    console.error('测试失败', error)
  }
}

const resetPromptForm = () => {
  promptFormRef.value?.resetFields()
  isEditPrompt.value = false
  Object.assign(promptForm, {
    prompt_id: '',
    prompt_name: '',
    prompt_scene: 'general',
    prompt_content: '',
    output_format: ''
  })
}

const handleSubmitPrompt = async () => {
  if (!promptFormRef.value) return
  const valid = await promptFormRef.value.validate()
  if (!valid) return

  try {
    submitLoading.value = true
    if (isEditPrompt.value) {
      await request.put('/admin/prompt/update', promptForm)
      ElMessage.success('编辑成功')
    } else {
      await request.post('/admin/prompt/add', promptForm)
      ElMessage.success('新增成功')
    }
    showPromptDialog.value = false
    getPromptList()
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadModelSettings()
  loadModelRuntime()
  getPromptList()
})
</script>

<style scoped>
.model-manage-container {
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
.runtime-card {
  margin-bottom: 16px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.status-item .label {
  font-size: 14px;
  color: #606266;
}
.status-item .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
.scene-hint {
  margin-top: 10px;
}
.auto-scene-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}
.auto-scene-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  max-width: 420px;
}
.prompt-dup-alert {
  margin-bottom: 16px;
}
</style>
