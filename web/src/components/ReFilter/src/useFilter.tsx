import { reactive, ref } from "vue";
import { createActiveFilters, createFilterTags } from "./components/FilterTags";
import { createHeaderRenderer } from "./filterHeader";
import { clearAllFilterState, clearFilter } from "./filterState";
import { createLocalMode } from "./localFilter";
import { createServerMode } from "./serverFilter";
import type { ActiveFilterItem, UseFilterOptions } from "./types";

/**
 * 列头筛选组合式函数（筛选/排序状态管理，供 FastCrud 列表页使用）
 *
 * 两种筛选模式（见 UseFilterOptions.mode，实现分别在 serverFilter.ts / localFilter.ts）：
 * - server（默认）：筛选/排序/分页/清除/删除均作用于后端，参数经搜索表单提交，每次获取最新数据
 * - local：仅首次加载与刷新请求后端（全量数据自动登记），此后筛选/排序/分页/删除均在本地操作
 *
 * 对外提供（解构使用）：
 * - `createFilterHeader` 生成列头筛选渲染函数（columnSlots.header）
 * - `FilterTags` 筛选标签组件（模板中直接 `<FilterTags />`）
 * - `clearAllFilters` / `removeFilterKey` 清除筛选条件
 * - `removeRows` / `getSourceRows` / `getFilteredRows` / `exportData` / `paginationState` 等 local 场景数据能力
 *
 * @example
 * // server 模式（默认）：筛选参数随列表查询提交后端
 * const { createFilterHeader, FilterTags } = useFilter({ crudExpose });
 * // local 模式（前端筛选）：pageRequest 正常返回全量数据即可，筛选/排序/分页在浏览器内完成
 * const { createFilterHeader, FilterTags } = useFilter({ mode: "local", crudExpose });
 * // 列配置：columns: { name: { column: { columnSlots: { header: createFilterHeader({ type: "text", ... }) } } } }
 * // 模板中渲染筛选标签：<template #header-bottom><FilterTags /></template>
 */
export function useFilter(options: UseFilterOptions) {
  const isLocalMode = (options?.mode ?? "server") === "local";
  /**
   * crudExpose 实例（必传）
   * 运行时可能为空：createRelation 提取默认列配置时会静态调用其他模块的 createCrudOptions，
   * 此时无真实 crudExpose，所有能力降级为 no-op（不注册/不刷新/不回填），避免崩溃
   */
  const crudExpose = options?.crudExpose;

  // ==================== 共享筛选状态 ====================

  /** 筛选表单（key 格式：field 或 field__lookup） */
  const filterForm = reactive<Record<string, any>>({});
  /** 多列排序映射，{ fieldName: "asc" | "desc" } */
  const sortMap = reactive<Record<string, string>>({});
  /** 字段名 → 中文标签 / 固定操作符描述（标签展示用） */
  const fieldLabelMap = reactive<Record<string, string>>({});
  const tagOperatorLabelMap = reactive<Record<string, string>>({});
  /** 筛选版本号（清除筛选时递增，通知各列面板同步重置内部状态） */
  const filterVersion = ref(0);
  /** 最近被清除的字段名（"__ALL__" 表示清除全部，供 ReFilter watch 匹配） */
  const clearedField = ref<string | null>(null);

  /** 通知各列面板重置内部状态 */
  const notifyReset = (field: string) => {
    clearedField.value = field;
    filterVersion.value++;
  };

  // ==================== 模式实现（server / local） ====================

  const mode = isLocalMode
    ? createLocalMode({ crudExpose, filterForm, sortMap, notifyReset })
    : createServerMode({ crudExpose, filterForm, sortMap, notifyReset });

  /** 活跃筛选条件列表（供 FilterTags 渲染 tag） */
  const activeFilters = createActiveFilters({
    filterForm,
    fieldLabelMap,
    tagOperatorLabelMap
  });

  // ==================== 对外能力 ====================

  /** 删除单个筛选条件（清除该字段的所有筛选 key，覆盖单条件/区间/级联场景） */
  const removeFilterKey = (item: ActiveFilterItem) => {
    clearFilter(filterForm, item.fieldName);
    notifyReset(item.fieldName);
    mode.refresh();
  };

  /** 清除所有筛选条件及排序；返回刷新结果（server 模式为刷新 Promise），便于调用方等待完成后继续处理 */
  const clearAllFilters = () => {
    clearAllFilterState(filterForm, sortMap);
    notifyReset("__ALL__");
    return mode.refresh();
  };

  /** 列头筛选渲染函数（列配置 columnSlots.header 使用） */
  const createFilterHeader = createHeaderRenderer({
    mode,
    filterForm,
    sortMap,
    fieldLabelMap,
    tagOperatorLabelMap,
    filterVersion,
    clearedField
  });

  /** 筛选标签渲染组件（内部创建完成，模板中直接 <FilterTags /> 渲染） */
  const FilterTags = createFilterTags({
    getItems: () => activeFilters.value,
    onRemove: removeFilterKey,
    onClearAll: clearAllFilters
  });

  // local 模式：包装 crudExpose.search 托管"全量登记 + 视图切片"（分页配置就绪后自动接管翻页事件）
  mode.init();

  return {
    createFilterHeader,
    FilterTags,
    activeFilters,
    filterForm,
    filterVersion,
    sortMap,
    removeFilterKey,
    clearAllFilters,
    ...mode.api
  };
}
