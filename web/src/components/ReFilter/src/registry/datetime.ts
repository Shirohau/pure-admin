import type { FilterTypeConfig } from "../types";
import DateInput from "../components/inputs/DateInput.vue";

/** 日期时间筛选：精确到时分秒（useTimezone 开启时提交带本地时区偏移的 ISO 字符串），支持单选与范围 */
const datetimeConfig: FilterTypeConfig = {
  type: "datetime",
  inputComponent: DateInput,
  // 透传给 DateInput：mode=datetime 不渲染维度切换器，直接精确到时分秒
  inputProps: { mode: "datetime" },
  supportsRange: true
};

export default datetimeConfig;
