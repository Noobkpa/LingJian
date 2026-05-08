import { ElMessage } from 'element-plus'

export const TEXT_MAX_LENGTH = 5000
export const IMAGE_MAX_SIZE = 5 * 1024 * 1024
export const IMAGE_ACCEPT = ['image/jpeg', 'image/jpg', 'image/png']
export const IMAGE_ACCEPT_HTML = 'image/jpeg,image/jpg,image/png,.jpg,.jpeg,.png'

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

export const validatePhone = (phone) => /^1[3-9]\d{9}$/.test(phone)
export const validatePassword = (password) => /^.{6,}$/.test(password)
