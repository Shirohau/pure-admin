import type {
  CreateCrudOptions,
  DynamicallyCrudOptions
} from "@fast-crud/fast-crud";
import type { DialogOptions } from "../ReDialog/type";

export type ReAsideTableProps = {
  /** 创建 CRUD 选项 */
  createCrudOptions?: CreateCrudOptions;
  /** 动态修改 CRUD 选项 */
  crudOptionsOverride?: DynamicallyCrudOptions;
  /** 组件名称 */
  componentName?: string;
  /** 是否自动搜索 */
  autoSearch?: boolean;
  /** 透传给 createCrudOptions 的上下文 :context="{ queryParams: leftQueryParams }" */
  context?: Record<string, any>;
  /** 强制控制批量删除按钮显示：不传时按权限与选择列自动判断，传入 true/false 时强制显示/隐藏 */
  showBatchDelete?: boolean;
};

/** 子表弹窗确定按钮回调参数（继承 ReDialog `beforeSure` 的 ctx 参数，额外附加注入的弹窗内表格选中的数据） */
export type AsideTableSureContext = Parameters<
  NonNullable<DialogOptions["beforeSure"]>
>[1] & {
  /** 弹窗内表格选中的数据（统一数组口径：单选 0~1 行、多选 0~N 行） */
  selectedData: any[];
};

/** 子表弹窗配置（ dialogAsideTable 函数参数） */
export interface DialogAsideTableOptions extends DialogOptions {
  /** 内容区组件的 `props`，可通过 `defineProps` 接收 */
  props?: ReAsideTableProps;
  /** 是否多选 */
  multiple?: boolean;
  /**
   * 点击确定按钮的回调，会暂停 `Dialog` 的关闭，回调内执行 `done` 才会真正关闭
   * @description 在 ReDialog 的 `beforeSure` 回调参数基础上，额外注入弹窗内表格选中的数据 `selectedData`
   */
  beforeSure?: (done: Function, ctx: AsideTableSureContext) => void;
}
