/**
 * @fileoverview 页面权限加载器
 * @description 按页面增量加载按钮权限和字段权限，统一管理加载状态和缓存
 *
 * ## 核心功能
 * - loadPagePerms：加载指定页面的按钮权限和字段权限
 * - resetPagePerms：重置所有权限缓存（退出登录时调用）
 *
 * ## 工作流程
 * 1. 路由守卫检测到用户访问某页面
 * 2. 调用 loadPagePerms(componentName) 加载该页面的权限
 * 3. 后端返回按钮权限列表和字段权限配置
 * 4. 按钮权限合并到 store.permissions（全局共享）
 * 5. 字段权限缓存到 store.fieldPerms[componentName]（按页面隔离）
 *
 * ## 嵌套子表支持
 * - 父表进入时，路由守卫只加载父表权限
 * - 子表嵌入时，ReAsideTable.onMounted 调用 loadPagePerms 加载子表权限
 * - 子表的 crud.tsx 使用 useButtonPerms，权限加载后自动更新
 */

import { useUserStoreHook } from "@/store/modules/user";
import { getPagePerms } from "@/api/routes";

/** 已加载过权限的页面名称集合（用于去重，避免重复请求） */
const loadedPagePerms = new Set<string>();

/** 正在加载中的 Promise 缓存（用于并发请求合并） */
const loadingPagePerms = new Map<string, Promise<void>>();

/**
 * 加载页面权限（按钮权限 + 字段权限）
 *
 * @description 调用后端 API 获取指定页面的权限配置，并存储到 store：
 * - 按钮权限：合并到 store.permissions（全局共享，增量添加）
 * - 字段权限：缓存到 store.fieldPerms[componentName]（按页面隔离）
 *
 * ## 防重复请求
 * - 同一页面多次调用只会发起一次请求
 * - 并发调用会共享同一个 Promise
 *
 * ## 嵌套子表场景
 * - 父表的路由守卫加载父表权限
 * - ReAsideTable.onMounted 加载子表权限
 * - 子表的 useButtonPerms 自动响应权限变化
 *
 * @param componentName - 组件名称（与路由 name 一致）
 * @returns Promise<void> 权限加载完成
 *
 * @example
 * ```ts
 * // 路由守卫中使用
 * router.beforeEach(async (to) => {
 *   if (to.name && to.meta?.backstage) {
 *     await loadPagePerms(to.name as string);
 *   }
 * });
 * ```
 *
 * @example
 * ```ts
 * // ReAsideTable 中使用
 * onMounted(async () => {
 *   if (componentName) {
 *     await loadPagePerms(componentName);
 *   }
 * });
 * ```
 */
export const loadPagePerms = async (componentName: string): Promise<void> => {
  // 组件名为空或已加载完成，直接返回
  if (!componentName || loadedPagePerms.has(componentName)) return;

  // 检查是否有正在进行的请求，避免并发重复
  const pendingRequest = loadingPagePerms.get(componentName);
  if (pendingRequest) return pendingRequest;

  // 发起权限加载请求
  const request = (async () => {
    try {
      const data = await getPagePerms(componentName);

      // 合并按钮权限到全局 store（增量添加，去重）
      useUserStoreHook().MERGE_PERMS(data.buttons ?? []);

      // 缓存字段权限到指定 component 的 slot（按页面隔离）
      useUserStoreHook().SET_FIELD_PERMS(componentName, data.fields ?? []);

      // 标记为已加载
      loadedPagePerms.add(componentName);
    } catch {
      // 权限加载失败时保持静默，使用 store 中的默认值
      // 默认行为：无按钮权限（按钮不显示），全部字段可读写
    } finally {
      // 清理加载中的 Promise 缓存
      loadingPagePerms.delete(componentName);
    }
  })();

  // 缓存正在加载的 Promise
  loadingPagePerms.set(componentName, request);

  return request;
};

/**
 * 重置权限缓存
 *
 * @description 清空所有已加载的权限记录，用于：
 * - 用户退出登录时清理状态
 * - 切换用户身份时重置权限
 *
 * ## 调用时机
 * - store/modules/user.ts 的 logOut 方法中调用
 *
 * @example
 * ```ts
 * // 用户退出登录
 * const logOut = () => {
 *   resetPagePerms();
 *   removeToken();
 *   router.push("/login");
 * };
 * ```
 */
export const resetPagePerms = (): void => {
  loadedPagePerms.clear();
  loadingPagePerms.clear();
};
