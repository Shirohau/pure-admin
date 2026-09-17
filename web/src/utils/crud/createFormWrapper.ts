import { compute, useMerge, type FormWrapperProps } from "@fast-crud/fast-crud";
import type { Ref } from "vue";

/** createFormWrapper 工厂函数参数（与抽屉默认配置深合并，调用方优先） */
export type CreateFormWrapperOptions = {
  /** 当前激活分组名的响应式引用（与 group.onTabChange 联动） */
  groupTab: Ref<string>;
  /** 抽屉配置 */
  formWrapperOverride?: FormWrapperProps;
};
const { merge } = useMerge();

/**
 * 全屏抽屉表单 wrapper 配置（配合 groupType: "tabs" 分组使用）
 * @description 表单以 100% 宽 el-drawer 展示；抽屉底部操作按钮
 * （ok/cancel/reset/copy/paste）仅在 "base" 分组时显示，
 * 打开抽屉时自动重置到 "base" 分组。
 * 如需覆盖默认配置，可传入 options 覆盖，如：
 * `createFormWrapper({ groupTab, formWrapperOverride: { size: "80%" } })`
 * @param groupTab - 当前激活分组名的响应式引用（与 group.onTabChange 联动）
 * @param formWrapperOverride - 可选覆盖配置（与默认配置深合并，调用方优先）
 * @returns 可直接配置到 form.wrapper 的抽屉配置对象
 */
export function createFormWrapper(
  options?: CreateFormWrapperOptions
): FormWrapperProps {
  const { groupTab, formWrapperOverride } = options;
  // 工厂默认配置（优先级最低），可被调用方 options 覆盖
  const defaultWrapper = {
    is: "el-drawer",
    size: "100%",
    appendToBody: true,
    buttons: {
      ok: { show: compute(() => groupTab.value == "base") },
      cancel: { show: compute(() => groupTab.value == "base") },
      reset: { show: compute(() => groupTab.value == "base") },
      copy: { show: compute(() => groupTab.value == "base") },
      paste: { show: compute(() => groupTab.value == "base") }
    },
    onOpen() {
      groupTab.value = "base";
    }
  };
  // 合并顺序：工厂默认配置 < 调用方 options（调用方优先）
  return merge(defaultWrapper, formWrapperOverride);
}
