/**
 * @fileoverview 权限模块统一入口
 * @description 提供按钮权限和字段权限的完整解决方案
 *
 * ## 模块结构
 * - button.ts：按钮权限检查（checkButtonPerms, useButtonPerms）
 * - field.ts：字段权限应用（useFieldPerms）
 * - loader.ts：页面权限加载（loadPagePerms, resetPagePerms）
 *
 * ## 快速使用
 * ```ts
 * import {
 *   checkButtonPerms,  // 同步检查按钮权限（模板 v-if）
 *   useButtonPerms,    // 响应式按钮权限（crud.tsx 推荐）
 *   useFieldPerms,     // 应用字段权限到 crudOptions
 *   loadPagePerms,     // 加载页面权限
 *   resetPagePerms     // 重置权限缓存
 * } from "@/utils/permissions";
 * ```
 *
 * ## 嵌套子表场景
 * 1. 父表的 crud.tsx 使用 useButtonPerms 获取权限
 * 2. ReAsideTable.onMounted 调用 loadPagePerms 加载子表权限
 * 3. ReAsideTable.onMounted 调用 useFieldPerms 应用字段权限
 * 4. 子表的 crud.tsx 中 useButtonPerms 自动响应更新
 */

// 按钮权限
export { checkButtonPerms, useButtonPerms } from "./button";

// 字段权限
export { useFieldPerms, type FieldPermConfig } from "./field";

// 页面权限加载
export { loadPagePerms, resetPagePerms } from "./loader";
