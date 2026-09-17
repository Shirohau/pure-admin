import { reactive, ref, unref } from "vue";
import type { CrudExpose } from "@fast-crud/fast-crud";
import { exportCsv, type CsvColumn } from "@/utils/downloadCsv";
import { parseIsnullFlag } from "./emptyFilter";
import { clearAllFilterState, removeRowsByReference } from "./filterState";
import type { ExportDataOptions, FilterModeImpl } from "./types";

// ==================== 前端筛选/排序计算 ====================

/**
 * 按后端 lookup 语义在前端复现匹配逻辑（key 格式与后端提交一致：field 或 field__lookup）
 * - 支持 exact / not_exact / contains / not_contains / startswith / endswith / gt / gte / lt / lte / in / isnull
 * - 跳过 __cascader / __select_labels 元数据键（仅用于标签展示）
 * - 级联字段（带 __cascader 元数据）按"行值包含任一提交路径"匹配
 */

/** 值是否为空（null / undefined / 空字符串） */
const isEmptyValue = (value: any) =>
  value === null || value === undefined || value === "";

/**
 * 数值/字符串双语义比较（gt/gte/lt/lte 共用）
 * - 双方均可转数值：按数值比较（避免 "9" > "10" 的字符串误判）
 * - 否则按字符串比较（ISO / YYYY-MM-DD 日期字典序有效）
 * - 任一侧为空：返回 null（空值不参与区间比较，对齐后端 NULL 语义）
 */
const compareValues = (rowValue: any, filterValue: any): number | null => {
  if (isEmptyValue(rowValue) || isEmptyValue(filterValue)) return null;
  const numA = Number(rowValue);
  const numB = Number(filterValue);
  if (!Number.isNaN(numA) && !Number.isNaN(numB)) {
    return numA === numB ? 0 : numA > numB ? 1 : -1;
  }
  const strA = String(rowValue);
  const strB = String(filterValue);
  return strA === strB ? 0 : strA > strB ? 1 : -1;
};

/** 操作符 → 行匹配函数（rowValue 行值，filterValue 提交值） */
const OPERATOR_MATCHERS: Record<
  string,
  (rowValue: any, filterValue: any) => boolean
> = {
  exact: (a, b) => String(a ?? "") === String(b ?? ""),
  not_exact: (a, b) => String(a ?? "") !== String(b ?? ""),
  contains: (a, b) => String(a ?? "").includes(String(b ?? "")),
  not_contains: (a, b) => !String(a ?? "").includes(String(b ?? "")),
  startswith: (a, b) => String(a ?? "").startsWith(String(b ?? "")),
  endswith: (a, b) => String(a ?? "").endsWith(String(b ?? "")),
  gt: (a, b) => {
    const result = compareValues(a, b);
    return result !== null && result > 0;
  },
  gte: (a, b) => {
    const result = compareValues(a, b);
    return result !== null && result >= 0;
  },
  lt: (a, b) => {
    const result = compareValues(a, b);
    return result !== null && result < 0;
  },
  lte: (a, b) => {
    const result = compareValues(a, b);
    return result !== null && result <= 0;
  },
  // select 多选：提交值为逗号拼接字符串（如 "1,2"）或数组，行值命中任一项即匹配
  in: (a, b) => {
    const list = Array.isArray(b) ? b : String(b ?? "").split(",");
    return list.some(item => String(item) === String(a ?? ""));
  },
  // 为空（true）/ 不为空（false）：与 emptyFilter 提交语义一致（NULL 或空字符串）
  isnull: (a, b) => (parseIsnullFlag(b) ? isEmptyValue(a) : !isEmptyValue(a))
};

/** 级联筛选路径匹配：提交值为多路径集（| 分隔路径、, 分隔层级），行值包含任一路径即匹配 */
const matchCascaderPath = (rowValue: any, filterValue: any): boolean => {
  const rowText = Array.isArray(rowValue)
    ? rowValue.join(",")
    : String(rowValue ?? "");
  if (!rowText) return false;
  return String(filterValue)
    .split("|")
    .some(path => path !== "" && rowText.includes(path));
};

/** 从 key 解析字段名与操作符（取最后一个 __ 分隔，支持字段名本身含 __；无后缀视为 exact） */
const parseFilterKey = (key: string) => {
  const lastSep = key.lastIndexOf("__");
  return lastSep === -1
    ? { fieldName: key, operator: "exact" }
    : { fieldName: key.slice(0, lastSep), operator: key.slice(lastSep + 2) };
};

/** 构建筛选断言列表（全部条件 AND；无有效条件时返回空数组） */
export const buildLocalConditions = (
  filterForm: Record<string, any>
): ((row: any) => boolean)[] => {
  const conditions: ((row: any) => boolean)[] = [];
  for (const [key, filterValue] of Object.entries(filterForm)) {
    if (key.endsWith("__cascader") || key.endsWith("__select_labels")) {
      continue;
    }
    if (isEmptyValue(filterValue)) continue;
    const { fieldName, operator } = parseFilterKey(key);
    // 级联筛选：以 __cascader 元数据键识别，提交值为路径集合（非普通比较符语义）
    if (filterForm[`${fieldName}__cascader`]) {
      conditions.push(row => matchCascaderPath(row[fieldName], filterValue));
      continue;
    }
    const matcher = OPERATOR_MATCHERS[operator] ?? OPERATOR_MATCHERS.exact;
    conditions.push(row => matcher(row[fieldName], filterValue));
  }
  return conditions;
};

/** 非空排序值比较：可转数值按数值比较，否则按 numeric 字符串比较（"2" < "10"） */
const compareSortValues = (a: any, b: any): number => {
  const numA = Number(a);
  const numB = Number(b);
  if (!Number.isNaN(numA) && !Number.isNaN(numB)) {
    return numA === numB ? 0 : numA > numB ? 1 : -1;
  }
  return String(a).localeCompare(String(b), "zh-CN", { numeric: true });
};

/** 多字段排序比较：按 orderKeys 顺序逐字段比较（空值始终排最后，不随升降序反转） */
export const compareRowsForSort = (
  a: any,
  b: any,
  orderKeys: [string, string][]
): number => {
  for (const [field, dir] of orderKeys) {
    const aEmpty = isEmptyValue(a[field]);
    const bEmpty = isEmptyValue(b[field]);
    if (aEmpty || bEmpty) {
      if (aEmpty && bEmpty) continue;
      return aEmpty ? 1 : -1;
    }
    const result = compareSortValues(a[field], b[field]);
    if (result !== 0) return dir === "desc" ? -result : result;
  }
  return 0;
};

/** 按筛选条件与排序计算展示数据（无任何条件时直接返回源数据，保持引用一致） */
export const computeLocalData = (
  sourceData: any[],
  filterForm: Record<string, any>,
  sortMap: Record<string, string>
): any[] => {
  const conditions = buildLocalConditions(filterForm);
  const orderKeys = Object.entries(sortMap).filter(([, dir]) => dir);
  let rows = sourceData;
  if (conditions.length) {
    rows = rows.filter(row => conditions.every(match => match(row)));
  }
  if (orderKeys.length) {
    rows = [...rows].sort((a, b) => compareRowsForSort(a, b, orderKeys));
  }
  return rows;
};

// ==================== 数据导出 ====================

/**
 * 从表格列配置收集导出列（跳过选择/序号/展开列与 exportable: false 的列）
 * CSV 文本生成与文件下载见公共工具 @/utils/downloadCsv
 */
export const collectExportColumns = (
  columnsMap: Record<string, any> | undefined,
  options?: Pick<ExportDataOptions, "onlyShow" | "columnFilter">
): CsvColumn[] => {
  const columns: CsvColumn[] = [];
  Object.values(columnsMap || {}).forEach(col => {
    if (!col?.key || col.key === "_index") return;
    const columnType = col.column?.type ?? col.type;
    if (
      columnType === "selection" ||
      columnType === "index" ||
      columnType === "expand"
    ) {
      return;
    }
    if (col.exportable === false) return;
    if (options?.columnFilter && options.columnFilter(col) === false) return;
    if (options?.onlyShow && unref(col.show) === false) return;
    columns.push({ key: col.key, title: col.title ?? col.key });
  });
  return columns;
};

// ==================== local 模式实现 ====================

/**
 * local 模式：仅首次加载与点击刷新按钮请求后端（全量数据自动登记为源数据），
 * 此后筛选/排序/分页/清除/删除均在本地源数据上操作，不再请求后端
 * - 启用前端分页（crudOptions.pagination 配置了 pageSize）：仅当前页切片写入表格，
 *   翻页/改页大小由内部自动接管（覆盖 fast-crud 默认的翻页刷新请求行为）
 * - 导出等超大页请求（页大小大于前端页大小）：本地返回筛选/排序后的全量行，不发请求
 */
export const createLocalMode = (options: {
  crudExpose?: CrudExpose;
  filterForm: Record<string, any>;
  sortMap: Record<string, string>;
  notifyReset: (field: string) => void;
}): FilterModeImpl => {
  const { crudExpose, filterForm, sortMap, notifyReset } = options;

  /** 全量源数据（数据加载时自动登记，筛选/排序均基于它计算） */
  let sourceData: any[] = [];
  /** 前端分页状态（启用与否及页大小由 syncLocalPagination 从分页配置动态读取） */
  const paginationState = reactive({ page: 1, pageSize: 0, total: 0 });
  /** 源数据版本号（登记/删除行时递增）：供依赖非响应式源数据的派生值（如统计文案）作响应式依赖重算 */
  const sourceVersion = ref(0);

  /** crudBinding 上的分页配置 */
  const getPagination = () => crudExpose?.crudBinding?.value?.pagination;

  /**
   * 从分页配置读取前端分页并接管翻页事件（幂等）
   * 启用条件：pagination 存在、show !== false 且 pageSize > 0（页大小配置即前端分页开关）
   * @returns 当前页大小；未启用返回 0
   */
  const syncLocalPagination = (): number => {
    const pagination = getPagination();
    if (!pagination || pagination.show === false) return 0;
    const pageSize = Number(pagination.pageSize) || 0;
    if (pageSize <= 0) return 0;
    if (pagination.onCurrentChange !== onPageChange) {
      pagination.onCurrentChange = onPageChange;
      pagination.onSizeChange = onPageSizeChange;
    }
    if (paginationState.pageSize !== pageSize) {
      paginationState.pageSize = pageSize;
    }
    return pageSize;
  };

  /** 回写翻页组件绑定值（element 适配器字段：currentPage/pageSize/total） */
  const syncPaginationState = () => {
    if (syncLocalPagination() <= 0) return;
    const pagination = getPagination();
    if (!pagination) return;
    pagination.currentPage = paginationState.page;
    pagination.pageSize = paginationState.pageSize;
    pagination.total = paginationState.total;
  };

  /**
   * 将筛选/排序结果写回表格（无条件下恢复全量源数据）
   * @param resetPage 启用前端分页时是否回到第一页（筛选/排序/清除场景传 true；删除行等仅收敛页码的场景不传）
   */
  const applyLocalFilter = (resetPage = false) => {
    if (!crudExpose) return;
    const result = computeLocalData(sourceData, filterForm, sortMap);
    let view = result;
    paginationState.total = result.length;
    const pageSize = syncLocalPagination();
    if (pageSize > 0) {
      // 启用前端分页：分页只作用于视图——表格仅写入当前页切片（total 已更新为筛选排序后的总行数）
      const maxPage = Math.max(1, Math.ceil(result.length / pageSize));
      paginationState.page = resetPage
        ? 1
        : Math.min(paginationState.page, maxPage);
      const start = (paginationState.page - 1) * pageSize;
      view = result.slice(start, start + pageSize);
      syncPaginationState();
    }
    // 结果与源数据同引用（无筛选/排序且未分页）时也回填浅拷贝新数组：
    // setTableData 赋同引用不触发响应式更新，会导致删除后表格不刷新（"没反应"）
    crudExpose.setTableData(view === sourceData ? [...view] : view);
  };

  /**
   * 页码变更（由 syncLocalPagination 自动接管到翻页组件；仅前端切片不发请求）
   * 注意需覆盖 fast-crud 默认翻页行为（默认翻页会触发 doRefresh 重新请求后端）
   */
  const onPageChange = (page: number) => {
    if (syncLocalPagination() <= 0) return;
    const maxPage = Math.max(
      1,
      Math.ceil(paginationState.total / paginationState.pageSize)
    );
    paginationState.page = Math.min(Math.max(1, Number(page) || 1), maxPage);
    applyLocalFilter();
  };

  /** 每页行数变更（由 syncLocalPagination 自动接管；回到第一页重新切片） */
  const onPageSizeChange = (size: number) => {
    if (syncLocalPagination() <= 0) return;
    const pageSize = Number(size) || paginationState.pageSize;
    paginationState.pageSize = pageSize;
    paginationState.page = 1;
    // 先回写分页配置，避免随后的 applyLocalFilter 读取旧配置值时把页大小覆盖回去
    const pagination = getPagination();
    if (pagination) pagination.pageSize = pageSize;
    applyLocalFilter();
  };

  /**
   * 登记全量源数据（数据加载时自动调用，通常无需手动）
   * 数据重新加载后清空全部筛选条件与排序（恢复全量展示），并通知各列面板重置状态
   */
  const setSourceData = (rows: any[]) => {
    sourceData = Array.isArray(rows) ? rows : [];
    clearAllFilterState(filterForm, sortMap);
    notifyReset("__ALL__");
    // 数据重新加载后回到第一页（启用前端分页时视图为新数据首页切片，由 getPageView 获取）
    paginationState.page = 1;
    paginationState.total = sourceData.length;
    sourceVersion.value++;
    syncPaginationState();
  };

  /**
   * 删除指定行（按行对象引用匹配，避免 rowKey 重复时误删）
   * 从登记的源数据中删除并重新应用筛选/排序刷新表格
   * （只删当前显示数据会导致"筛选下删除、取消筛选后已删行重新出现"）
   */
  const removeRows = (rows: any[]): number => {
    const removed = removeRowsByReference(sourceData, rows);
    if (removed) {
      sourceVersion.value++;
      // 仅收敛页码（末页删空时回退），不重置回第一页
      applyLocalFilter();
    }
    return removed;
  };

  /** 全量源数据（含被筛选隐藏的行，已删除行不在其中；供保存/提交场景使用） */
  const getSourceRows = (): any[] => sourceData;

  /** 当前页切片（数据刷新返回体使用；未启用前端分页时返回全量源数据） */
  const getPageView = (): any[] => {
    const pageSize = syncLocalPagination();
    if (pageSize <= 0) return sourceData;
    const start = (paginationState.page - 1) * pageSize;
    return sourceData.slice(start, start + pageSize);
  };

  /** 当前筛选/排序后的全量行（分页前；供表尾合计等全量统计场景使用） */
  const getFilteredRows = (): any[] =>
    computeLocalData(sourceData, filterForm, sortMap);

  /**
   * 导出筛选/排序/删除后的全量数据为 CSV 文件（本地生成下载，不请求后端）
   * 列与表格一致（跳过选择/序号列与 exportable: false 的列），值直接使用源数据原始值
   */
  const exportData = (options?: ExportDataOptions) => {
    const rows = getFilteredRows();
    const columns = collectExportColumns(
      crudExpose?.crudBinding?.value?.table?.columnsMap,
      options
    );
    exportCsv(columns, rows, options);
  };

  /**
   * 包装 crudExpose.search，在请求出口统一托管"全量登记 + 视图切片"：
   * - 常规请求（首次加载/刷新按钮）：pageRequest 返回全量数据后自动登记为源数据；
   *   启用前端分页时把返回给 doRefresh 的 records 替换为当前页切片、分页信息替换为前端分页状态
   * - 超大页请求（导出 dataFrom:"search" 以超大 pageSize 调用）：启用前端分页时直接本地返回
   *   筛选/排序后的全量行，不发后端请求、不改变分页状态
   */
  const wrapSearchForLocalPaging = () => {
    if (!crudExpose) return;
    const originalSearch = crudExpose.search.bind(crudExpose);
    crudExpose.search = (async (pageQuery?: any, searchOptions?: any) => {
      const localPageSize = syncLocalPagination();
      const limit = Number(pageQuery?.page?.pageSize) || 0;
      // 导出等超大页请求：本地返回筛选/排序后的全量行
      if (localPageSize > 0 && limit > localPageSize) {
        const rows = getFilteredRows();
        return {
          records: rows,
          currentPage: 1,
          pageSize: limit,
          total: rows.length
        };
      }
      const pageRes = await originalSearch(pageQuery, searchOptions);
      if (pageRes == null) return pageRes;
      // 常规请求：全量数据登记为源数据（清空筛选、回到第一页）
      setSourceData((pageRes.records as any[]) || []);
      if (localPageSize <= 0) return pageRes;
      // 启用前端分页：交由 doRefresh 写入的改为当前页切片
      return {
        ...pageRes,
        records: getPageView(),
        currentPage: paginationState.page,
        pageSize: paginationState.pageSize,
        total: paginationState.total
      };
    }) as typeof crudExpose.search;
  };

  return {
    /** 筛选/排序/清除条件变化：本地重算回填（一律回到第一页） */
    refresh: () => applyLocalFilter(true),
    registerRefresh: () => {
      /* local 模式不注册后端刷新回调 */
    },
    init: () => wrapSearchForLocalPaging(),
    api: {
      setSourceData,
      removeRows,
      getSourceRows,
      getPageView,
      getFilteredRows,
      paginationState,
      sourceVersion,
      onPageChange,
      onPageSizeChange,
      exportData
    }
  };
};
