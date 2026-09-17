/**
 * @fileoverview 字段权限模块
 * @description 提供字段级别的权限控制，根据权限等级过滤和修改列配置
 *
 * ## 权限等级说明（与后端 RoleMenuFieldModel.DATASCOPE_CHOICES 对齐）
 * | 等级 | 含义       | 列显示 | 表单状态 |
 * |------|------------|--------|----------|
 * | 0    | 禁止访问   | 隐藏   | 隐藏     |
 * | 1    | 只读       | 显示   | 禁用     |
 * | 2    | 可读写     | 显示   | 可编辑   |
 *
 * ## 默认行为
 * 未显式分配权限的字段默认等级为 2（可读写），与后端"未分配=默认全部权限"语义一致。
 *
 * ## 使用场景
 * - 页面组件 onMounted 中调用，应用字段权限到 crudOptions
 * - 嵌套子表在 ReAsideTable 中自动应用
 */

import { useUserStoreHook } from "@/store/modules/user";
import XEUtils from "xe-utils";

/** 默认权限等级（未显式分配时的默认值） */
const DEFAULT_PERMISSION_LEVEL = 2;

/**
 * 字段权限配置接口
 * @description 单个字段的权限配置信息
 */
export interface FieldPermConfig {
  /** 字段名称，对应 crudOptions.columns 中的 key */
  field_name: string;
  /** 权限等级：0-禁止访问，1-只读，2-可读写 */
  permission_level: number;
  /** 功能权限（可选），如 can_download 等 */
  func_permissions?: Record<string, boolean>;
}

/**
 * 应用字段权限到 crudOptions
 *
 * @description 从 store.fieldPerms 中读取指定组件的字段权限配置，
 * 根据权限等级处理 crudOptions.columns：
 * - 等级 0（禁止访问）：从 columns 中移除该字段
 * - 等级 1（只读）：禁用表单组件，列正常显示
 * - 等级 2（可读写）：保持原样
 *
 * ## 嵌套子表支持
 * 字段权限数据由 loadPagePerms 统一加载并缓存到 store.fieldPerms。
 * ReAsideTable.onMounted 会先调用 loadPagePerms 加载子表权限，
 * 然后调用本函数应用字段权限。
 *
 * @param componentName - 组件名称（与路由 name 一致，作为 fieldPerms 的缓存键）
 * @param crudOptions - 原始的 crudOptions 对象
 * @returns 应用字段权限后的 crudOptions（原地修改并返回）
 *
 * @example
 * ```ts
 * // 在页面组件 onMounted 中使用
 * onMounted(async () => {
 *   await loadPagePerms(componentName);
 *   const newOptions = useFieldPerms(componentName, crudOptions);
 *   resetCrudOptions(newOptions);
 * });
 * ```
 */
export const useFieldPerms = (componentName: string, crudOptions: any): any => {
  const store = useUserStoreHook();
  const { fieldPerms } = store;

  // 没有该页面的字段权限缓存，直接返回原配置（默认全部可见可编辑）
  const fields: FieldPermConfig[] = fieldPerms[componentName];
  if (!fields || fields.length === 0) return crudOptions;

  // 构建"字段名 → 权限配置"索引，避免逐列 find 遍历（O(n*m) → O(n+m)）
  const fieldPermMap = new Map(fields.map(f => [f.field_name, f]));

  const columns = crudOptions.columns;
  // 构建新的 columns 对象（避免遍历时修改原对象）
  const newColumns: Record<string, any> = {};

  XEUtils.objectEach(columns, (item, key) => {
    // 查找该字段的权限配置；未显式分配时默认拥有全部权限（可读写）
    const fieldPerm = fieldPermMap.get(key);
    const permissionLevel = fieldPerm
      ? fieldPerm.permission_level
      : DEFAULT_PERMISSION_LEVEL;

    // === 权限处理 ===
    // 等级 0：禁止访问 → 完全隐藏（不加入 newColumns）
    if (permissionLevel === 0) {
      return;
    }

    // 克隆列配置，避免修改原始 crudOptions 中的列对象
    const columnConfig = XEUtils.clone(item);

    // 等级 1：只读 → 禁用表单组件（列仍展示）
    if (permissionLevel === 1) {
      columnConfig.form ??= {};
      columnConfig.form.component ??= {};
      columnConfig.form.component.disabled = true;
    }

    // 等级 2（可读写）及其他取值 → 保持原样
    newColumns[key] = columnConfig;
  });

  // 替换 columns
  crudOptions.columns = newColumns;
  return crudOptions;
};
