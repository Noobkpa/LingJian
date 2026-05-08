<template>
  <div class="model-manage-container">
    <h2 class="page-title">模型与Prompt管理</h2>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 模型配置 -->
      <el-tab-pane label="模型配置" name="model">
        <div class="base-card">
          <h3 class="card-title">大模型配置</h3>
          <el-form :model="modelForm" label-width="140px" style="max-width: 600px">
            <el-form-item label="当前模型版本">
              <el-select v-model="modelForm.model_version" style="width: 100%">
                <el-option label="通义千问 qwen-plus（外部 API）" value="qwen_v2" />
                <el-option label="本地 Qwen（历史兼容）" value="qwen_v1" />
              </el-select>
            </el-form-item>
            <el-form-item label="量化精度">
              <el-radio-group v-model="modelForm.quantization">
                <el-radio label="4bit">4bit (速度快)</el-radio>
                <el-radio label="8bit">8bit (平衡)</el-radio>
                <el-radio label="16bit">16bit (精度高)</el-radio>
              </el-radio-group>
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

        <div class="base-card">
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
                <span class="value">1,234</span>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="status-item">
                <span class="label">平均推理耗时</span>
                <span class="value">1.8s</span>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- Prompt模板管理 -->
      <el-tab-pane label="Prompt模板管理" name="prompt">
        <div class="base-card">
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

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

// 模型表单
const modelForm = reactive({
  model_version: 'qwen_v2',
  quantization: '8bit',
  confidence: 0.8
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
    await request.post('/admin/model/config', modelForm)
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
</style>
