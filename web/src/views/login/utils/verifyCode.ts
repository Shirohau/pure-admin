import type { FormInstance, FormItemProp } from "element-plus";
import { clone } from "@pureadmin/utils";
import { ref } from "vue";
import { api } from "../api";

const isDisabled = ref(false);
const timer = ref(null);
const text = ref("");

export const useVerifyCode = () => {
  /**
   * @param formEl 表单实例
   * @param props 需要校验的字段名 (例如 'phone' 或 'email')
   * @param time 倒计时时间，默认60秒
   */
  const start = async (
    formEl: FormInstance | undefined,
    props: FormItemProp,
    time = 60
  ) => {
    if (!formEl) return;

    const initTime = clone(time, true);

    // 先进行表单校验
    await formEl.validateField(props, async isValid => {
      if (!isValid) {
        // 校验失败，不发送请求
        return;
      }

      try {
        // 立即启动倒计时
        clearInterval(timer.value);
        isDisabled.value = true;
        text.value = `${time}`;

        timer.value = setInterval(() => {
          if (time > 0) {
            time -= 1;
            text.value = `${time}`;
          } else {
            text.value = "";
            isDisabled.value = false;
            clearInterval(timer.value);
            time = initTime;
          }
        }, 1000);

        // 从表单模型中获取手机号或邮箱
        const fieldValue = formEl.getField(props).fieldValue;
        const params: Record<string, any> = {
          type: String(props),
          [String(props)]: fieldValue
        };
        await api.sendCode(params);
        // ElMessage.success("验证码已发送");
      } catch (error: any) {
        // 请求失败处理
        console.error("发送验证码失败:", error);
        // 确保状态重置，允许用户重新点击
        isDisabled.value = false;
        text.value = "";
        clearInterval(timer.value);
      }
    });
  };

  const end = () => {
    text.value = "";
    isDisabled.value = false;
    clearInterval(timer.value);
  };

  return {
    isDisabled,
    timer,
    text,
    start,
    end
  };
};
