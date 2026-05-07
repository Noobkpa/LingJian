import { ElMessage } from 'element-plus'

// 文本字数限制，匹配文档5000字上限
export const TEXT_MAX_LENGTH = 5000
// 图片大小限制 5MB
export const IMAGE_MAX_SIZE = 5 * 1024 * 1024
// 支持的图片格式（MIME）；部分系统 MIME 为空时配合扩展名校验
export const IMAGE_ACCEPT = ['image/jpeg', 'image/jpg', 'image/png']
/** input accept：兼容 Windows 等资源管理器只认扩展名的情况 */
export const IMAGE_ACCEPT_HTML = 'image/jpeg,image/jpg,image/png,.jpg,.jpeg,.png'

// 手机号校验规则
export const phoneRule = (rule, value, callback) => {
  const reg = /^1[3-9]\d{9}$/
  if (!value) {
    callback(new Error('请输入手机号'))
  } else if (!reg.test(value)) {
    callback(new Error('请输入正确的手机号'))
  } else {
    callback()
  }
}

// 密码校验规则 8-20位，包含字母+数字+特殊字符
export const passwordRule = (rule, value, callback) => {
  const reg = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,20}$/
  if (!value) {
    callback(new Error('请输入密码'))
  } else if (value.length < 8) {
    callback(new Error('密码长度不能少于8位'))
  } else if (!reg.test(value)) {
    callback(new Error('密码需包含字母、数字和特殊字符'))
  } else {
    callback()
  }
}

/**
 * 图片校验：兼容 el-upload 的 before-upload（入参为原生 File）
 * 与 file-list 中的项（含 .raw）两种形态。
 */
export const validateImage = (file) => {
  const f = file?.raw ?? file
  if (!f || !(f instanceof Blob)) {
    ElMessage.error('无效的图片文件')
    return false
  }
  const name = f instanceof File && f.name ? f.name.toLowerCase() : ''
  const okByExt = /\.(jpe?g|png)$/.test(name)
  const mime = typeof f.type === 'string' ? f.type : ''
  const okByMime = mime !== '' && IMAGE_ACCEPT.includes(mime)
  const isAcceptType = okByMime || okByExt
  const isLtSize = f.size <= IMAGE_MAX_SIZE

  if (!isAcceptType) {
    ElMessage.error('仅支持 JPG、PNG 格式的图片')
    return false
  }
  if (!isLtSize) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

// 文本长度校验
export const validateTextLength = (text) => {
  if (!text || text.trim().length === 0) {
    ElMessage.error('请输入需要识别的文本内容')
    return false
  }
  if (text.length > TEXT_MAX_LENGTH) {
    ElMessage.error(`文本内容不能超过 ${TEXT_MAX_LENGTH} 字`)
    return false
  }
  return true
}