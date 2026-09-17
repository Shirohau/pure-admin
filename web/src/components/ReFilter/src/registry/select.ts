import type { FilterTypeConfig } from "../types";
import SelectInput from "../components/inputs/SelectInput.vue";

/** 下拉筛选：支持多选（提交 in，后端按逗号分隔解析） */
const selectConfig: FilterTypeConfig = {
  type: "select",
  inputComponent: SelectInput
};

export default selectConfig;
