import type { App } from "vue";
import { hiPrintPlugin, disAutoConnect } from "vue-plugin-hiprint";
disAutoConnect(); // 取消自动连接客户端
export function useVuePluginHiprint(app: App) {
  // 安装 UI 组件库
  app.use(hiPrintPlugin);
  // console.log("disAutoConnect"); // 为了检验执行顺序
}
