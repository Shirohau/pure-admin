import { ref } from "vue";
import { api } from "./api";
import type { ThirdParty } from "../login/utils/enums";
// 定义第三方登录平台的数据结构接口

export const thirdLogin = (platform: ThirdParty, source: string) => {
  const params = { platform: platform.platform, kind: "PC" };
  api.getPlatformConfig(params).then((response: ApiResponse) => {
    const info = response.data;
    const authorize_uri = info["authorize_uri"]; // 认证地址
    const client_id = info["client_id"]; // 应用ID client_id
    const redirect_uri = encodeURIComponent(info["redirect_uri"]); // 重定向地址

    // 在回调时携带额外信息
    const state = btoa(
      JSON.stringify({
        platform_name: platform.title,
        source,
        ...params
      })
    );
    const url = ref("");
    if (platform.platform == "wecom") {
      // 企业微信登录需要特殊处理，使用微信的授权地址
      const appid = info["appid"]; // 企业ID
      const agentid = info["agentid"]; // 自建应用ID

      url.value = `${authorize_uri}?login_type=CorpApp&appid=${appid}&agentid=${agentid}&redirect_uri=${redirect_uri}&state=${state}`;
    } else {
      url.value = `${authorize_uri}?response_type=code&client_id=${client_id}&redirect_uri=${redirect_uri}&state=${state}`;
    }
    window.location.href = url.value;
  });
};
