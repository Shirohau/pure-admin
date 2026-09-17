import type { FilterType, FilterTypeConfig } from "../types";
import textConfig from "./text";
import numberConfig from "./number";
import selectConfig from "./select";
import dateConfig from "./date";
import datetimeConfig from "./datetime";
import cascaderConfig from "./cascader";

/**
 * 筛选类型注册表（新增筛选类型的步骤）：
 * 1. 在 types.ts 的 FilterType 中追加类型名
 * 2. 在 components/inputs/ 下创建输入组件（实现 FilterInputExpose：reset / submit）
 * 3. 在本目录创建类型配置文件（如 xxx.ts）
 * 4. 在下方注册表导入并注册
 */
const registry = new Map<FilterType, FilterTypeConfig>([
  [textConfig.type, textConfig],
  [numberConfig.type, numberConfig],
  [selectConfig.type, selectConfig],
  [dateConfig.type, dateConfig],
  [datetimeConfig.type, datetimeConfig],
  [cascaderConfig.type, cascaderConfig]
]);

/** 获取类型配置；未注册的类型回退为 text 配置（保证渲染兜底） */
export const getTypeConfig = (type: FilterType): FilterTypeConfig =>
  registry.get(type) ?? textConfig;
