/**
 * @fileoverview 按钮权限模块
 * @description 提供按钮级别的权限检查功能，支持同步检查和响应式检查两种方式
 *
 * ## 核心概念
 * - 权限字符串格式：`{ComponentName}:{Action}`，如 `UserView:Create`
 * - 超级权限：`*:*:*` 表示拥有所有权限
 *
 * ## 使用场景
 * - 同步检查（checkButtonPerms）：用于模板中的 v-if 判断，权限已加载时使用
 * - 响应式检查（useButtonPerms）：用于 crud.tsx 中的权限控制，支持权限动态加载
 *
 * ## 嵌套子表支持
 * 当父表嵌套子表时，子表的 crud.tsx 在创建时权限可能尚未加载。
 * 使用 useButtonPerms 返回 ComputedRef，权限加载后自动更新，按钮正确显示。
 */

import { computed, type ComputedRef } from "vue";
import { useUserStoreHook } from "@/store/modules/user";
import { isString, isIncludeAllChildren } from "@pureadmin/utils";

/** 超级权限标识，拥有全部按钮权限 */
const SUPER_PERMS = "*:*:*";

/**
 * 同步检查按钮权限（返回布尔值）
 *
 * @description 根据当前已加载的页面按钮权限进行判断，适用于：
 * - 模板中的 v-if 条件渲染
 * - 权限已确定加载完成的场景（如路由守卫后）
 *
 * @param value - 权限字符串或权限字符串数组
 *   - 字符串：检查是否拥有该单个权限
 *   - 数组：检查是否拥有数组中的所有权限（AND 逻辑）
 * @returns 是否拥有权限
 *
 * @example
 * ```vue
 * <!-- 模板中使用 -->
 * <el-button v-if="checkButtonPerms('UserView:Create')">新增</el-button>
 * ```
 */
export const checkButtonPerms = (value: string | Array<string>): boolean => {
  // 空值直接返回无权限
  if (!value) return false;

  const { permissions } = useUserStoreHook();

  // 权限列表为空，无权限
  if (!permissions || permissions.length === 0) return false;

  // 超级权限：拥有全部权限
  if (permissions.length === 1 && permissions[0] === SUPER_PERMS) {
    return true;
  }

  // 检查权限
  const hasAuth = isString(value)
    ? permissions.includes(value)
    : isIncludeAllChildren(value, permissions);

  return hasAuth;
};

/**
 * 响应式按钮权限检查（返回 ComputedRef）
 *
 * @description 返回一个计算属性，当 store.permissions 变化时自动重新计算。
 * 适用于 crud.tsx 中的权限控制，特别支持嵌套子表场景：
 *
 * ## 嵌套子表场景
 * 1. 父表进入时，路由守卫只加载父表的权限
 * 2. 子表的 crud.tsx 在创建时，子表权限尚未加载，useButtonPerms 返回 false
 * 3. ReAsideTable.onMounted 中调用 loadPagePerms 加载子表权限
 * 4. 权限加载完成后，ComputedRef 自动更新为 true，按钮显示
 *
 * @param value - 权限字符串或权限字符串数组
 * @returns ComputedRef<boolean> 响应式的权限检查结果
 *
 * @example
 * ```tsx
 * // crud.tsx 中使用
 * const hasPerms = {
 *   add: useButtonPerms(`${componentName}:Create`),
 *   edit: useButtonPerms(`${componentName}:Update`),
 * };
 *
 * // FastCRUD 会自动解包 ComputedRef
 * actionbar: {
 *   buttons: {
 *     add: { show: hasPerms.add }
 *   }
 * }
 * ```
 */
export const useButtonPerms = (
  value: string | Array<string>
): ComputedRef<boolean> => {
  return computed(() => checkButtonPerms(value));
};
