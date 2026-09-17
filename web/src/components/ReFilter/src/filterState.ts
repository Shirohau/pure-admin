import { toRaw } from "vue";
import type { FilterResult } from "./types";

/**
 * 共享筛选状态操作（filterForm / sortMap / 行删除），供 useFilter 与两种模式实现复用
 */

/**
 * 将 FilterResult 映射写入 filterForm（先清除该字段全部旧条件）
 * - 级联筛选：fieldName 直接提交路径拼接值，__cascader 元数据仅用于标签展示
 * - 条件1按操作符显式提交（exact 也携带 __exact 后缀，与后端 lookup 语义一致）
 * - 条件2为范围区间上限（操作符与条件1必然不同，key 不会冲突）
 */
export const applyFilter = (
  filterForm: Record<string, any>,
  fieldName: string,
  result: FilterResult
) => {
  const { cond1Operator, cond1Value, cond2Operator, cond2Value } = result;

  clearFilter(filterForm, fieldName);

  if (result.cascaderLabels) {
    filterForm[fieldName] = cond1Value;
    filterForm[`${fieldName}__cascader`] = result.cascaderLabels;
    return;
  }

  if (cond1Operator) {
    filterForm[`${fieldName}__${cond1Operator}`] = cond1Value;
  } else if (cond1Value !== undefined && cond1Value !== null) {
    filterForm[fieldName] = cond1Value;
  }

  if (cond2Operator) {
    filterForm[`${fieldName}__${cond2Operator}`] = cond2Value;
  }

  // select 选项 label 元数据：仅用于标签展示（提交给后端的仍是 value）
  if (result.cond1Labels) {
    filterForm[`${fieldName}__select_labels`] = result.cond1Labels;
  }
};

/** 清除某字段的所有筛选 key（含 field__xxx 与级联/select 元数据键） */
export const clearFilter = (
  filterForm: Record<string, any>,
  fieldName: string
) => {
  Object.keys(filterForm).forEach(key => {
    if (key === fieldName || key.startsWith(fieldName + "__")) {
      delete filterForm[key];
    }
  });
};

/** 清空全部筛选与排序条件 */
export const clearAllFilterState = (
  filterForm: Record<string, any>,
  sortMap: Record<string, string>
) => {
  Object.keys(filterForm).forEach(key => delete filterForm[key]);
  Object.keys(sortMap).forEach(key => delete sortMap[key]);
};

/**
 * 按行对象引用从数组删除指定行（倒序遍历避免索引错位），返回实际删除行数
 * - 按引用匹配（而非 rowKey）避免 rowKey 重复时误删；比较前经 toRaw 归一化
 *   （表格数据为 Vue 响应式代理，与源数据原始对象引用不同，直接比较会匹配失败导致"删除没反应"）
 */
export const removeRowsByReference = (
  sourceData: any[],
  rows: any[]
): number => {
  if (!Array.isArray(sourceData) || !rows?.length) return 0;
  const rowSet = new Set(rows.map(row => toRaw(row)));
  let removed = 0;
  for (let i = sourceData.length - 1; i >= 0; i--) {
    if (rowSet.has(toRaw(sourceData[i]))) {
      sourceData.splice(i, 1);
      removed++;
    }
  }
  return removed;
};
