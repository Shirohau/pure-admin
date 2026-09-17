import type { FilterTypeConfig } from "../types";
import DateInput from "../components/inputs/DateInput.vue";

/** 日期筛选：面板内可切换 年/月/周/日 维度（默认日），支持单选与范围（周维度不支持范围） */
const dateConfig: FilterTypeConfig = {
  type: "date",
  inputComponent: DateInput,
  // 透传给 DateInput：mode=date 渲染维度切换器（年/月/周/日）
  inputProps: { mode: "date" },
  supportsRange: true
};

export default dateConfig;
