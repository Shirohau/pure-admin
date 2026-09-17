import type { FilterTypeConfig } from "../types";
import CascaderInput from "../components/inputs/CascaderInput.vue";

/** 级联筛选（省市县等树形结构）：多选，路径间 | 分隔、层级间 , 分隔，后端按路径 OR 匹配 */
const cascaderConfig: FilterTypeConfig = {
  type: "cascader",
  inputComponent: CascaderInput
};

export default cascaderConfig;
