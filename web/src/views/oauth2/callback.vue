<template>
  <div>回调页面</div>
</template>

<script setup>
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { ElLoading } from "element-plus";
import { message } from "@/utils/message";
import { initRouter, getTopMenu } from "@/router/utils";
import { onMounted } from "vue";
import { api } from "./api";
import { useUserStoreHook } from "@/store/modules/user";
import { setToken } from "@/utils/auth";
const router = useRouter();
const { t } = useI18n();

/**
 * 登录
 */
const Login = data => {
  setToken(data);
  initRouter().then(() => {
    router.push(getTopMenu(true).path).then(() => {
      message(t("login.pureLoginSuccess"), { type: "success" });
    });
  });
};

/**
 * 绑定
 */
const Binding = () => {
  router.push("/account-settings?witchPane=oauth2");
};

onMounted(() => {
  // 获取登录页面传过来的回调参数
  const query = router.currentRoute.value.query;
  const code = query.code || query.auth_code;
  const stateStr = query.state;
  const state = JSON.parse(atob(stateStr));
  // 显示加载框
  const loading = ElLoading.service({
    lock: true,
    text: `正在调用${t(state.platform_name)}，请稍候……`
  });
  const data = {
    code,
    platform: state.platform,
    kind: state.kind,
    source: state.source,
    user_id: useUserStoreHook().id
  };
  // 向后端发送登录回调请求
  api
    .postOAuthCallback(data)
    .then(response => {
      switch (state.source) {
        case "binding":
          Binding();
          break;
        case "login":
          Login(response.data);
          break;
        default:
          console.warn("未知的操作来源:", state.source);
      }
    })
    .catch(response => {
      // 根据来源页面返回
      if (state.source === "binding") {
        Binding();
      } else {
        router.push("/login");
      }
    })
    .finally(() => {
      loading.close();
    });
});
</script>
