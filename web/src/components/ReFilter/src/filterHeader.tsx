import type { Ref } from "vue";
import ReFilter from "./index.vue";
import { applyFilter, clearFilter } from "./filterState";
import type { FilterModeImpl, FilterOptions, FilterResult } from "./types";

/**
 * 列头筛选渲染函数工厂（useFilter 的 createFilterHeader 实现）
 * 返回 Vue 渲染函数（用于 FastCrud 的 columnSlots.header），渲染 ReFilter 组件并绑定筛选/排序/重置事件
 */
export const createHeaderRenderer = (context: {
  /** 模式实现（refresh 分发到 server / local） */
  mode: FilterModeImpl;
  filterForm: Record<string, any>;
  sortMap: Record<string, string>;
  /** 字段名 → 中文标签（标签展示用） */
  fieldLabelMap: Record<string, string>;
  /** 字段名 → 固定操作符描述（标签展示用） */
  tagOperatorLabelMap: Record<string, string>;
  filterVersion: Ref<number>;
  clearedField: Ref<string | null>;
}) => {
  const {
    mode,
    filterForm,
    sortMap,
    fieldLabelMap,
    tagOperatorLabelMap,
    filterVersion,
    clearedField
  } = context;

  return (options: FilterOptions) => {
    const {
      type,
      columnLabel,
      tooltip,
      fieldName,
      doRefresh,
      selectList,
      useTimezone,
      lookup,
      hideEmpty,
      cascaderProps,
      tagOperatorLabel
    } = options;

    // 注册字段标签与固定操作符描述（供筛选标签展示）
    fieldLabelMap[fieldName] = columnLabel;
    if (tagOperatorLabel) {
      tagOperatorLabelMap[fieldName] = tagOperatorLabel;
    }
    // 注册刷新回调（server 模式生效；各列的刷新最终都指向同一 crudExpose.doRefresh）
    mode.registerRefresh(doRefresh);

    /** 解析 selectList：支持静态数组或 getter 函数 */
    const resolveSelectList = () => {
      if (typeof selectList === "function") {
        return selectList();
      }
      return selectList;
    };

    return () => (
      <ReFilter
        type={type}
        columnLabel={columnLabel}
        tooltip={tooltip}
        fieldName={fieldName}
        selectList={resolveSelectList()}
        useTimezone={useTimezone}
        lookup={lookup}
        hideEmpty={hideEmpty}
        cascaderProps={cascaderProps}
        filterVersion={filterVersion.value}
        clearedField={clearedField.value}
        onFilter={(result: FilterResult) => {
          applyFilter(filterForm, fieldName, result);
          mode.refresh();
        }}
        onReset={() => {
          clearFilter(filterForm, fieldName);
          mode.refresh();
        }}
        onSort={(direction: string | null) => {
          if (direction) {
            sortMap[fieldName] = direction;
          } else {
            delete sortMap[fieldName];
          }
          mode.refresh();
        }}
      />
    );
  };
};
