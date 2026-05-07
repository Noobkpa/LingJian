import { md5 } from 'js-md5'

// MD5加密，匹配文档密码加密要求
export const md5Encrypt = (str) => {
  return md5(str)
}

// 敏感信息脱敏-手机号
export const phoneDesensitization = (phone) => {
  if (!phone) return ''
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 敏感信息脱敏-邮箱
export const emailDesensitization = (email) => {
  if (!email) return ''
  const [name, domain] = email.split('@')
  if (!name || !domain) return email
  const showName = name.length > 3 ? name.slice(0, 3) : name
  return `${showName}****@${domain}`
}