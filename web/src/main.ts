import App from "./App.vue";
import router from "./router";
import { setupStore } from "@/store";
import { hasOaLaunch, loginFromOa } from "@/utils/oaSso";
import { removeToken, setToken } from "@/utils/auth";
import { ElMessage } from "element-plus";
import { useI18n } from "@/plugins/i18n";

import { getPlatformConfig } from "./config";
import { MotionPlugin } from "@vueuse/motion";
// import { useEcharts } from "@/plugins/echarts";
import { createApp, type Directive } from "vue";
import { useElementPlus } from "@/plugins/elementPlus";
import { injectResponsiveStorage } from "@/utils/responsive";

// ===== 审批流 vForm3 设计器（暂未启用：designer.umd.js 会导致构建报错，功能开发时再放开）=====
// vForm3 UMD 包通过全局 Vue 获取 API，必须先挂载 window.Vue（动态导入见下方挂载流程）
// import * as Vue from "vue";
// (window as any).Vue = Vue;

import Table from "@pureadmin/table";
// import PureDescriptions from "@pureadmin/descriptions";

// import "@/lib/vForm/designer.style.css"; // 审批流 vForm3 设计器暂未启用

// 引入重置样式
import "./style/reset.scss";
// 导入公共样式
import "./style/index.scss";
// 一定要在main.ts中导入tailwind.css，防止vite每次hmr都会请求src/style/index.scss整体css文件导致热更新慢的问题
import "./style/tailwind.css";
import "element-plus/dist/index.css";
// 导入字体图标
import "./assets/iconfont/iconfont.js";
import "./assets/iconfont/iconfont.css";

// 引入 dayjs 和中文本地化
import dayjs from "dayjs";
import "dayjs/locale/zh-cn"; // 引入中文 locale
// 设置 dayjs 使用中文 locale
dayjs.locale("zh-cn");

// 处理时区
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
dayjs.extend(utc);
dayjs.extend(timezone);
const localTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
// 👇 关键：设置默认时区为用户本地时区（如 Asia/Shanghai）
dayjs.tz.setDefault(localTz);
// 如果你想确保即使浏览器时区不对，也强制用上海时间（更稳妥）：
// dayjs.tz.setDefault('Asia/Shanghai');

const app = createApp(App);

// 自定义指令
import * as directives from "@/directives";
Object.keys(directives).forEach(key => {
  app.directive(key, (directives as { [key: string]: Directive })[key]);
});

// 全局注册 $modal（AntFlow 组件使用 proxy.$modal.msgError 等）
import { Modal } from "@/utils/modal";
app.config.globalProperties.$modal = Modal;

// 全局注册@iconify/vue图标库
import {
  IconifyIconOffline,
  IconifyIconOnline,
  FontIcon
} from "./components/ReIcon";
app.component("IconifyIconOffline", IconifyIconOffline);
app.component("IconifyIconOnline", IconifyIconOnline);
app.component("FontIcon", FontIcon);

// 全局注册按钮级别权限组件
import { Auth } from "@/components/ReAuth";
import { Perms } from "@/components/RePerms";
app.component("Auth", Auth);
app.component("Perms", Perms);

// 全局注册vue-tippy
import "tippy.js/dist/tippy.css";
import "tippy.js/themes/light.css";
import VueTippy from "vue-tippy";
app.use(VueTippy);
// 引入 fast-crud
import { useFastCrud } from "./plugins/fast-crud";
// 引入 vue-plugin-hiprint
import { useVuePluginHiprint } from "./plugins/vue-plugin-hiprint";
getPlatformConfig(app).then(async config => {
  setupStore(app);
  if (hasOaLaunch) {
    // 新的工作台上下文必须重新核对身份，不沿用旧本地账号。
    removeToken();
    try {
      const account = await loginFromOa();
      if (account) setToken(account);
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : "OA 免登失败");
    }
  }
  // 动态加载 vForm3 UMD（审批流暂未启用：designer.umd.js 会导致构建报错，功能开发时再放开）
  // await import("@/lib/vForm/designer.umd.js");
  // const VForm3 = (window as any).VFormDesigner;
  app.use(router);
  await router.isReady();
  injectResponsiveStorage(app, config);
  app
    .use(MotionPlugin)
    .use(useI18n)
    .use(useElementPlus)
    .use(Table)
    .use(useFastCrud)
    .use(useVuePluginHiprint);
  // .use(VForm3); // 审批流 vForm3 设计器暂未启用
  // .use(PureDescriptions)
  // .use(useEcharts);
  app.mount("#app");
});
