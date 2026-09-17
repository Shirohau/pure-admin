import { reactive, ref } from "vue";
import type { CrudExpose } from "@fast-crud/fast-crud";
import { clearAllFilterState, removeRowsByReference } from "./filterState";
import type { FilterModeImpl } from "./types";

/**
 * server 模式（默认）：筛选/排序/分页/清除/删除均作用于后端
 * - 条件变化（筛选/排序/清除）：filterForm + sortMap 同步到搜索表单数据（列表查询与导出自动携带），再请求后端
 * - 分页与删除由 fast-crud 默认行为携带参数请求后端，每次获取最新数据
 */
export const createServerMode = (options: {
  crudExpose?: CrudExpose;
  filterForm: Record<string, any>;
  sortMap: Record<string, string>;
  notifyReset: (field: string) => void;
}): FilterModeImpl => {
  const { crudExpose, filterForm, sortMap, notifyReset } = options;

  /** 刷新回调（各列的 doRefresh 最终都指向同一 crudExpose.doRefresh，只存首个注册） */
  let refreshCallback: (() => void) | null = null;
  /** 已同步到搜索表单数据的 key 集合（清除时先移除旧 key，避免残留） */
  const syncedKeys = new Set<string>();

  /** 将 filterForm + sortMap 同步到搜索表单数据（不触发额外搜索） */
  const syncToSearchForm = () => {
    if (!crudExpose) return;
    const params: Record<string, any> = {};
    Object.entries(filterForm).forEach(([key, val]) => {
      // __cascader / __select_labels 元数据仅用于标签展示，不参与提交
      if (key.endsWith("__cascader") || key.endsWith("__select_labels")) return;
      if (val !== undefined && val !== null && val !== "") {
        params[key] = val;
      }
    });
    // 排序 → ordering（如 "name,-age" 表示 name 升序、age 降序）
    const ordering = Object.entries(sortMap)
      .filter(([, dir]) => dir)
      .map(([field, dir]) => (dir === "desc" ? `-${field}` : field))
      .join(",");
    if (ordering) params.ordering = ordering;

    const form = { ...(crudExpose.getSearchFormData() || {}) };
    syncedKeys.forEach(key => delete form[key]);
    Object.assign(form, params);
    syncedKeys.clear();
    Object.keys(params).forEach(key => syncedKeys.add(key));
    crudExpose.setSearchFormData({
      form,
      mergeForm: false,
      triggerSearch: false
    });
  };

  return {
    refresh: () => {
      syncToSearchForm();
      return refreshCallback?.();
    },
    registerRefresh: callback => {
      if (!refreshCallback) {
        refreshCallback = callback ?? (() => crudExpose?.doRefresh());
      }
    },
    init: () => {
      /* server 模式无需初始化 */
    },
    api: {
      // 以下为 local 专属能力在 server 模式的兼容实现（保持 API 形状一致）
      setSourceData: () => {
        clearAllFilterState(filterForm, sortMap);
        notifyReset("__ALL__");
      },
      removeRows: rows =>
        removeRowsByReference(
          (crudExpose?.getTableData() as any[]) ?? [],
          rows
        ),
      getSourceRows: () => (crudExpose?.getTableData() as any[]) || [],
      getPageView: () => [],
      getFilteredRows: () => [],
      paginationState: reactive({ page: 1, pageSize: 0, total: 0 }),
      sourceVersion: ref(0),
      onPageChange: () => {
        /* local 专属，server 模式无操作 */
      },
      onPageSizeChange: () => {
        /* local 专属，server 模式无操作 */
      },
      exportData: () => {
        /* local 专属（本地源数据才有筛选排序删除后的全量语义），server 模式无操作 */
      }
    }
  };
};
