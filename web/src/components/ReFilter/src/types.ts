import type { Component, Ref } from "vue";
import type { CrudExpose } from "@fast-crud/fast-crud";
import type { CsvExportOptions } from "@/utils/downloadCsv";

/**
 * 筛选类型（registry/ 下每种类型一个配置文件，新增类型创建对应文件并注册即可）
 * text 文本 / number 数值 / select 下拉（多选）/ date 日期 / datetime 日期时间 / cascader 级联
 */
export type FilterType =
  | "text"
  | "number"
  | "select"
  | "date"
  | "datetime"
  | "cascader";

/** 筛选结果（输入组件校验后提交的荷载） */
export interface FilterResult {
  /** 条件1操作符 */
  cond1Operator: string;
  /** 条件1值 */
  cond1Value: any;
  /** 条件2操作符（范围区间上限，如 lte；操作符与条件1必然不同） */
  cond2Operator?: string;
  /** 条件2值 */
  cond2Value?: any;
  /** select 选项 label 列表（与 cond1Value 一一对应，仅用于标签展示） */
  cond1Labels?: any[];
  /** 级联选中路径的 label 列表（仅用于标签展示，提交仍用 cond1Value） */
  cascaderLabels?: any[];
}

/** 活跃筛选条件项（表格上方 tag 展示） */
export interface ActiveFilterItem {
  /** filterForm 中的 key，如 "name__contains" */
  key: string;
  /** 字段名 */
  fieldName: string;
  /** 字段中文标签 */
  fieldLabel: string;
  /** 操作符中文标签（单条件时使用） */
  operatorLabel: string;
  /** 筛选值 */
  value: any;
  /** 区间上限 key（有值表示这是一个区间 tag） */
  endKey?: string;
  /** 区间上限值 */
  endValue?: any;
}

/** 筛选输入组件实例协议（FilterArea 通过 ref 调用） */
export interface FilterInputExpose {
  /** 清空面板内部输入状态（不触发事件，供"重置"调用） */
  reset: () => void;
  /** 校验并提交筛选；无有效值时自行 emit("reset") */
  submit: () => void;
}

/** 筛选输入组件公共 props（FilterArea 渲染时统一注入，按需声明） */
export interface InputProps {
  /** 下拉/级联选项列表 */
  selectList?: { label: string; value: any; children?: any[] }[];
  /** 级联选择器 props 覆盖（如自定义字段映射 { value: "id", label: "title" }） */
  cascaderProps?: Record<string, any>;
  /** 日期筛选是否带时区（datetime 开启时提交携带本地时区偏移的 ISO 字符串） */
  useTimezone?: boolean;
  /** 自定义操作符：按 fieldName__lookup=value 单值提交，不参与范围/多选逻辑 */
  lookup?: string;
  /** 是否禁用输入（勾选"空/非空"时由 FilterArea 置为 true） */
  disabled?: boolean;
}

/** 筛选类型注册配置（registry/ 下每种类型一个配置文件） */
export interface FilterTypeConfig {
  /** 类型名（与 FilterType 一一对应） */
  type: FilterType;
  /** 输入组件（实现 FilterInputExpose 协议） */
  inputComponent: Component;
  /** 输入组件专属 props（渲染时 v-bind 透传，如 DateInput 的 mode） */
  inputProps?: Record<string, any>;
  /** 是否提供"范围"开关（number/date/datetime 支持） */
  supportsRange?: boolean;
}

/** useFilter 配置项 */
export interface UseFilterOptions {
  /** crudExpose（必传，从 createCrudOptions 参数中直接传入） */
  crudExpose: CrudExpose;
  /**
   * 筛选模式：
   * - "server"（默认）：筛选/排序同步到搜索表单并刷新后端，分页/删除由 fast-crud 携带参数请求后端
   * - "local"：仅首次加载与刷新请求后端（全量数据自动登记为源数据），筛选/排序/分页/删除均在本地操作
   */
  mode?: "server" | "local";
}

/** createFilterHeader 参数选项 */
export interface FilterOptions {
  /** 筛选类型 */
  type: FilterType;
  /** 列标题（列头展示 + 标签展示） */
  columnLabel: string;
  /** 提示信息 */
  tooltip?: string;
  /** 字段名（filterForm 的 key 前缀） */
  fieldName: string;
  /** 刷新回调（server 模式生效；缺省回退到 crudExpose 的 doRefresh） */
  doRefresh?: () => void;
  /** 日期筛选是否带时区 */
  useTimezone?: boolean;
  /** 可用值列表（静态数组或 getter 函数，getter 用于异步数据场景） */
  selectList?:
    | { label: string; value: any; children?: any[] }[]
    | (() => { label: string; value: any; children?: any[] }[]);
  /** 自定义筛选操作符，提交 fieldName__lookup=value（如 name__contains=张三） */
  lookup?: string;
  /** 是否隐藏空值筛选（是否为空：是 / 否，默认 false 即显示） */
  hideEmpty?: boolean;
  /** 固定操作符描述（如"包含"、"开头是"），用于标签展示 */
  tagOperatorLabel?: string;
  /** 级联树字段映射覆盖（默认 { value: "value", label: "label", children: "children" }） */
  cascaderProps?: Record<string, any>;
}

/** 模式对外 API（server / local 实现一致；server 模式下为兼容占位实现） */
export interface FilterModeApi {
  /** 登记全量源数据（local 数据加载时自动调用，通常无需手动） */
  setSourceData: (rows: any[]) => void;
  /** 删除行并返回实际删除数（local：同步删除源数据并刷新视图；server：删除当前表格数据） */
  removeRows: (rows: any[]) => number;
  /** 全量剩余行（local：登记的源数据；server：当前表格数据） */
  getSourceRows: () => any[];
  /** 当前页切片（local 未启用前端分页时返回全量源数据） */
  getPageView: () => any[];
  /** 筛选排序后的全量行（分页前，供表尾合计等全量统计场景） */
  getFilteredRows: () => any[];
  /** 前端分页状态（page 当前页 / pageSize 每页行数 / total 筛选排序后总行数） */
  paginationState: { page: number; pageSize: number; total: number };
  /** 源数据版本号（登记/删除行时递增，供派生值作响应式依赖） */
  sourceVersion: Ref<number>;
  /** 页码变更（已由内部自动接管到翻页组件） */
  onPageChange: (page: number) => void;
  /** 每页行数变更（已由内部自动接管到翻页组件） */
  onPageSizeChange: (size: number) => void;
  /** 导出数据（local：筛选/排序/删除后的全量数据导出为 CSV 文件；server：无操作） */
  exportData: (options?: ExportDataOptions) => void;
}

/** 筛选模式实现（useFilter 装配用：server 见 serverFilter.ts，local 见 localFilter.ts） */
export interface FilterModeImpl {
  /** 条件变化后的刷新：server 同步搜索表单并请求后端；local 本地重算回填（回第一页） */
  refresh: () => void | Promise<any>;
  /** 注册后端刷新回调（server 模式记录首个注册；local 模式忽略） */
  registerRefresh: (callback?: () => void) => void;
  /** 初始化（local：包装 crudExpose.search 托管全量数据与切片；server：无操作） */
  init: () => void;
  /** 对外 API */
  api: FilterModeApi;
}

/** local 模式数据导出配置（exportData）：在公共 CSV 配置（@/utils/downloadCsv）基础上增加表格列收集选项 */
export interface ExportDataOptions extends CsvExportOptions {
  /** 是否仅导出显示中的列（show !== false），默认 false（与表格列一致） */
  onlyShow?: boolean;
  /** 列过滤器（返回 false 跳过该列） */
  columnFilter?: (col: Record<string, any>) => boolean;
}
