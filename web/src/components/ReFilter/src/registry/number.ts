import type { FilterTypeConfig } from "../types";
import NumberInput from "../components/inputs/NumberInput.vue";

/** 数值筛选：单值（比较符）与范围（最小值/最大值）由"范围"开关切换 */
const numberConfig: FilterTypeConfig = {
  type: "number",
  inputComponent: NumberInput,
  supportsRange: true
};

export default numberConfig;
