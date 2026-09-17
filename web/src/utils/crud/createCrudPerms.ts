import type { ComputedRef } from "vue";
import { loadPagePerms, useButtonPerms } from "@/utils/auth";

/**
 * Crud 页面通用按钮权限映射：hasPerms 属性名 → 权限动作码
 * 所有 crud 页面均拥有的基础权限（print / historyRecover 等页面级权限通过 extraPerms 扩展）
 */
const DEFAULT_PERMS: Record<string, string> = {
  /** 新增 */
  add: "Create",
  /** 查看 */
  view: "Retrieve",
  /** 修改 */
  edit: "Update",
  /** 删除 */
  remove: "Destroy",
  /** 批量删除 */
  batchDestroy: "BatchDestroy",
  /** 导出 */
  export: "SyncExport",
  /** 导入 */
  import: "SyncImport"
};

/**
 * 创建 Crud 页面按钮权限集合
 *
 * 统一封装 crud.tsx 中的按钮权限初始化：
 * - 懒加载本页按钮权限（fire-and-forget）：选择器/详情抽屉等非路由场景下渲染本 crud 时，
 *   权限尚未加载，此处补加载后 useButtonPerms 的 computed 会自动更新；
 *   正常页面访问时路由守卫已加载，loadPagePerms 内部去重直接返回
 * - 返回的每个权限均为 ComputedRef：FastCRUD 的 show 配置自动解包，
 *   权限加载完成后按钮自动显示；模板 v-if 中也会自动解包
 *
 * @param componentName - 组件名（权限码前缀），如 "AuthorView"
 * @param extraPerms - 页面级额外按钮权限（属性名 → 权限动作码），
 *   如 { print: "Print" } / { historyRecover: "HistoryRecover" }，与通用权限合并返回
 * @returns 按钮权限集合，如 hasPerms.add / hasPerms.print
 *
 * @example
 * ```tsx
 * // 仅通用权限（add / view / edit / remove / batchDestroy / export / import）
 * const hasPerms = createCrudPerms(componentName);
 * // 通用权限 + 打印权限
 * const hasPerms = createCrudPerms(componentName, { print: "Print" });
 * ```
 */
export function createCrudPerms(
  componentName: string,
  extraPerms?: Record<string, string>
): Record<string, ComputedRef<boolean>> {
  // 懒加载本页按钮权限（fire-and-forget）
  loadPagePerms(componentName);

  /** 权限控制 */
  const hasPerms: Record<string, ComputedRef<boolean>> = {};

  // 通用按钮权限
  Object.entries(DEFAULT_PERMS).forEach(([key, action]) => {
    hasPerms[key] = useButtonPerms(`${componentName}:${action}`);
  });

  // 页面级额外按钮权限
  Object.entries(extraPerms ?? {}).forEach(([key, action]) => {
    hasPerms[key] = useButtonPerms(`${componentName}:${action}`);
  });

  return hasPerms;
}
