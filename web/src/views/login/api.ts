import { http } from "@/utils/http";

const apiPrefix = "/api/otp/";

export const api = {
  /**
   * 发送验证码
   * @param data - 可选的请求体数据对象
   * @returns 返回 HTTP 请求的 Promise 结果
   */
  sendCode(data?: object) {
    return http.request(
      "post",
      `${apiPrefix}send-code/`,
      { data },
      { skipToken: true }
    );
  },
  /**
   * 验证码登录
   * @param data - 可选的请求体数据对象
   * @returns 返回 HTTP 请求的 Promise 结果
   */
  login(data?: object) {
    return http.request(
      "post",
      `${apiPrefix}login/`,
      { data },
      { skipToken: true }
    );
  },
  /**
   * 验证码重置密码
   * @param data - 包含phone, code, new_password的对象
   * @returns 返回 HTTP 请求的 Promise 结果
   */
  resetPassword(data?: object) {
    return http.request("post", `${apiPrefix}reset-password/`, { data });
  },

  /**
   * 验证码注册
   * @param data - 包含phone, code, new_password的对象
   * @returns 返回 HTTP 请求的 Promise 结果
   */
  register(data?: object) {
    return http.request("post", `${apiPrefix}register/`, { data });
  }
};
