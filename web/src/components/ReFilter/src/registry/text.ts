import type { FilterTypeConfig } from "../types";
import TextInput from "../components/inputs/TextInput.vue";

/** 文本筛选：比较符（等于/不等于/开头是/结尾是/包含/不包含）+ 关键词 */
const textConfig: FilterTypeConfig = {
  type: "text",
  inputComponent: TextInput
};

export default textConfig;
