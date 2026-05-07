<template>
  <div class="user-manage-container">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" @click="showAddDialog = true">新增用户</el-button>
    </div>

    <!-- 筛选区 -->
    <div class="base-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="用户账号">
          <el-input v-model="filterForm.username" placeholder="请输入" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="账号状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="正常" :value="1" />
            <el-option label="冻结" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item label="注册时间">
          <el-date-picker
            v-model="filterForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 280px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="getUserList">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格区 -->
    <div class="base-card">
      <el-table
        :data="userList"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="user_id" label="用户ID" width="100" />
        <el-table-column prop="username" label="账号" width="140" />
        <el-table-column prop="nickname" label="昵称" width="140" />
        <el-table-column prop="phone" label="手机号" width="140">
          <template #default="{ row }">
            {{ row.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'admin' ? 'danger' : ''">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '正常' : '冻结' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="register_time" label="注册时间" width="180" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" class="table-action-btn" @click="handleEdit(row)">编辑</el-button>
            <el-button
              size="small"
              class="table-action-btn"
              :type="row.status === 1 ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '冻结' : '解冻' }}
            </el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-area">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalCount"
          @size-change="getUserList"
          @current-change="getUserList"
        />
      </div>
    </div>

    <!-- 新增/编辑用户弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
      @close="resetUserForm"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户账号" prop="username">
          <el-input v-model="userForm.username" :disabled="isEdit" placeholder="请设置登录账号" />
        </el-form-item>
        <el-form-item label="用户昵称" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请设置昵称" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="用户角色" prop="role" v-if="!isEdit">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="登录密码" prop="password" v-if="!isEdit">
          <el-input v-model="userForm.password" type="password" placeholder="请设置密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmitUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import request from '@/utils/request'

// 状态定义
const loading = ref(false)
const submitLoading = ref(false)
const showAddDialog = ref(false)
const isEdit = ref(false)
const userFormRef = ref()
const userList = ref([])
const totalCount = ref(0)

// 筛选表单
const filterForm = reactive({
  username: '',
  status: '',
  date_range: []
})

// 分页
const pagination = reactive({
  page: 1,
  size: 10
})

// 用户表单
const userForm = reactive({
  user_id: '',
  username: '',
  nickname: '',
  phone: '',
  role: 'user',
  password: ''
})

const userRules = {
  username: [
    { required: true, message: '请输入用户账号', trigger: 'blur' }
  ],
  nickname: [
    { required: true, message: '请输入用户昵称', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请设置登录密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 方法
const getUserList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filterForm
    }
    const { data } = await request.get('/admin/user/list', { params })
    userList.value = data.list
    totalCount.value = data.total
  } catch (error) {
    console.error('获取用户列表失败', error)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.username = ''
  filterForm.status = ''
  filterForm.date_range = []
  pagination.page = 1
  getUserList()
}

const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(userForm, row)
  showAddDialog.value = true
}

const handleToggleStatus = async (row) => {
  const action = row.status === 1 ? '冻结' : '解冻'
  ElMessageBox.confirm(`确定要${action}该用户吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.post('/admin/user/toggle-status', {
      user_id: row.user_id,
      status: row.status === 1 ? 0 : 1
    })
    ElMessage.success(`${action}成功`)
    getUserList()
  }).catch(() => {})
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该用户吗？删除后无法恢复', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    confirmButtonClass: 'el-button--danger'
  }).then(async () => {
    await request.delete('/admin/user/delete', { data: { user_id: row.user_id } })
    ElMessage.success('删除成功')
    getUserList()
  }).catch(() => {})
}

const resetUserForm = () => {
  userFormRef.value?.resetFields()
  isEdit.value = false
  Object.assign(userForm, {
    user_id: '',
    username: '',
    nickname: '',
    phone: '',
    role: 'user',
    password: ''
  })
}

const handleSubmitUser = async () => {
  if (!userFormRef.value) return
  const valid = await userFormRef.value.validate()
  if (!valid) return

  try {
    submitLoading.value = true
    if (isEdit.value) {
      await request.put('/admin/user/update', userForm)
      ElMessage.success('编辑成功')
    } else {
      await request.post('/admin/user/add', userForm)
      ElMessage.success('新增成功')
    }
    showAddDialog.value = false
    getUserList()
  } catch (error) {
    console.error('提交失败', error)
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  getUserList()
})
</script>

<style scoped>
.user-manage-container {
  width: 100%;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}
.pagination-area {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>