import type { Component } from "vue";
import type { FilterType } from "../types";

/**
 * 筛选输入组件实例协议（FilterArea 通过 ref 调用的公共接口）
 * 每个类型的输入组件必须通过 defineExpose 暴露这两个方法
 */
export interface FilterInputExpose {
  /** 清空面板内部所有输入状态（不触发任何事件，供"重置"与外部清除信号调用） */
  reset: () => void;
  /** 校验并提交快速筛选：构建 FilterResult 后 emit("filter")；无有效值时自行 emit("reset") 通知父组件 */
  submit: () => void;
}

/**
 * 筛选输入组件公共 props（FilterArea 渲染时统一注入，输入组件按需声明）
 */
export interface InputProps {
  /** 下拉/级联选项列表（select/cascader 类型使用） */
  selectList?: { label: string; value: any; children?: any[] }[];
  /** 级联选择器 props 覆盖（cascader 类型使用） */
  cascaderProps?: Record<string, any>;
  /** 日期筛选是否带时区（datetime 类型使用，开启时提交携带本地时区偏移的 ISO 字符串） */
  useTimezone?: boolean;
  /** 自定义操作符（lookup）：存在时按 fieldName__lookup=value 单值提交，不参与范围/多选逻辑 */
  lookup?: string;
  /** 是否禁用输入（勾选“空/非空”时由 FilterArea 统一置为 true） */
  disabled?: boolean;
}

/**
 * 筛选类型注册配置（registry/ 下每个类型一个配置文件）
 *
 * 新增筛选类型的步骤：
 * 1. 在 types.ts 的 FilterType 联合类型中追加类型名
 * 2. 在 components/inputs/ 下创建输入组件（实现 FilterInputExpose 协议）
 * 3. 在 registry/ 下创建配置文件（如 xxx.ts），导出本接口对象
 * 4. 在 registry/index.ts 中导入并注册
 */
export interface FilterTypeConfig {
  /** 类型名（与 FilterType 一一对应） */
  type: FilterType;
  /** 输入组件：负责面板输入区 UI 与快速筛选提交语义 */
  inputComponent: Component;
  /** 输入组件专属 props（如 DateInput 的 mode 区分日期/日期时间），渲染时 v-bind 透传 */
  inputProps?: Record<string, any>;
  /** 是否提供"范围"开关（单值 ↔ 区间切换，number/date/datetime 提供） */
  supportsRange?: boolean;
}
