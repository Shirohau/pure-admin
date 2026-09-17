/**
 * 校验中国大陆手机号
 * @param rule 表单校验规则（Element Plus 传入）
 * @param value 用户输入的值
 * @param callback 回调函数，校验失败时传入 Error
 */
export const validateMobile = (
  rule: any,
  value: string,
  callback: (error?: Error) => void
) => {
  const mobileRegex = /^1[3-9]\d{9}$/;
  if (!mobileRegex.test(value)) {
    return callback(new Error("请输入正确的手机号码"));
  }
  callback(); // 校验通过
};

/**
 * 校验邮箱格式
 * @param rule 表单规则（Element Plus 传入）
 * @param value 用户输入的值
 * @param callback 回调函数
 */
export const validateEmail = (
  rule: any,
  value: string,
  callback: (error?: Error) => void
) => {
  // RFC 5322 简化版正则，适用于大多数场景
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(value)) {
    return callback(new Error("请输入正确的邮箱格式"));
  }
  callback(); // 校验通过
};
