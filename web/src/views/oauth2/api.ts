import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/oauth2/";

export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 获取第三方平台登录配置
   */
  getPlatformConfig(params?: object) {
    return http.request(
      "get",
      `${apiPrefix}get_config/`,
      { params },
      { skipToken: true }
    );
  },
  /**
   * 发送 OAuth 回调请求
   * @param data - 可选的请求体数据对象
   * @returns 返回 HTTP 请求的 Promise 结果
   */
  postOAuthCallback(data?: object) {
    return http.request(
      "post",
      `${apiPrefix}callback/`,
      { data },
      { skipToken: true }
    );
  }
};
