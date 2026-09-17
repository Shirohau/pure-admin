<script setup lang="ts">
import { ref } from "vue";
import type { FilterInputExpose, FilterResult, InputProps } from "../../types";

defineOptions({ name: "TextInput" });

/** 文本输入：比较符下拉 + 关键词（lookup 场景固定操作符单值提交，不显示比较符） */

const props = defineProps<InputProps>();

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
}>();

/** 比较符选项：标签 → 后端 lookup（默认"包含"） */
const TEXT_OPERATOR_OPTIONS = [
  { label: "等于", value: "exact" },
  { label: "不等于", value: "not_exact" },
  { label: "开头是", value: "startswith" },
  { label: "结尾是", value: "endswith" },
  { label: "包含", value: "contains" },
  { label: "不包含", value: "not_contains" }
];

/** 文本关键词 */
const textValue = ref("");
/** 比较符（默认"包含"） */
const operator = ref("contains");

/** 重置内部状态（不触发事件，供 FilterArea 调用） */
const reset = () => {
  textValue.value = "";
  operator.value = "contains";
};

/**
 * 提交筛选：lookup 自定义操作符按 fieldName__lookup=value 提交；默认比较符 + 关键词
 */
const submit = () => {
  const value = textValue.value;
  if (!value) {
    emit("reset");
    return;
  }
  emit("filter", {
    cond1Operator: props.lookup || operator.value,
    cond1Value: value
  });
};

defineExpose<FilterInputExpose>({ reset, submit });
</script>

<template>
  <div class="text-input">
    <!-- 比较符下拉（lookup 场景操作符固定，不显示） -->
    <el-select
      v-if="!lookup"
      v-model="operator"
      class="operator-select"
      size="small"
      :teleported="false"
      :disabled="disabled"
    >
      <el-option
        v-for="op in TEXT_OPERATOR_OPTIONS"
        :key="op.value"
        :label="op.label"
        :value="op.value"
      />
    </el-select>
    <el-input
      v-model="textValue"
      size="small"
      clearable
      placeholder="请输入内容"
      :disabled="disabled"
      @keyup.enter="submit"
    />
  </div>
</template>

<style scoped>
.text-input {
  display: flex;
  align-items: center;
  gap: 6px;
}
/* 比较符下拉：紧凑宽度，与文本输入框并排 */
.operator-select {
  width: 76px;
  flex-shrink: 0;
}
/* 输入控件圆角（与面板风格一致） */
.text-input :deep(.el-input__wrapper) {
  border-radius: 6px;
}
</style>
