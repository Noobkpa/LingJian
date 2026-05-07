// 手机号校验规则
export const phoneRule = /^1[3-9]\d{9}$/

// 密码校验规则（至少6位）
export const passwordRule = /^.{6,}$/

// 邮箱校验
export const emailRule = /^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/

// 验证手机号
export const validatePhone = (phone) => {
  return phoneRule.test(phone)
}

// 验证密码
export const validatePassword = (password) => {
  return passwordRule.test(password)
}