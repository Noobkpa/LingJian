// 文本字数限制，匹配文档5000字上限
export const TEXT_MAX_LENGTH = 5000
// 图片大小限制 5MB
export const IMAGE_MAX_SIZE = 5 * 1024 * 1024
// 支持的图片格式
export const IMAGE_ACCEPT = ['image/jpeg', 'image/jpg', 'image/png']

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

// 图片文件校验
export const validateImage = (file) => {
  const isAcceptType = IMAGE_ACCEPT.includes(file.raw.type)
  const isLtSize = file.raw.size <= IMAGE_MAX_SIZE

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