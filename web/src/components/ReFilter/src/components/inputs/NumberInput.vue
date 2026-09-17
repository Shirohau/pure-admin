<script setup lang="ts">
import { ref, watch } from "vue";
import type { FilterInputExpose, FilterResult, InputProps } from "../../types";

defineOptions({ name: "NumberInput" });

/** 数值输入：范围模式（gte/lte 区间，可只填一边）与单值模式（比较符 + 数值）由"范围"开关切换 */

const props = withDefaults(
  defineProps<
    InputProps & {
      /** 范围模式开关（FilterArea v-model 管理）：true=范围（最小值+最大值），false=单值+比较符 */
      rangeMode?: boolean;
    }
  >(),
  { rangeMode: false }
);

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
}>();

/** 单值比较符选项：符号 → 后端 lookup（默认 =，提交 fieldName__lookup=value） */
const NUMBER_OPERATOR_OPTIONS = [
  { label: "等于", value: "exact" },
  { label: "不等于", value: "not_exact" },
  { label: "大于", value: "gt" },
  { label: "大于等于", value: "gte" },
  { label: "小于", value: "lt" },
  { label: "小于等于", value: "lte" }
];

/** 区间下限（最小值） */
const startValue = ref<any>(null);
/** 区间上限（最大值） */
const endValue = ref<any>(null);
/** 单值比较符（默认 =） */
const operator = ref("exact");

/** 范围模式切换（FilterArea 勾选控制）：清空已选值，避免单值与区间值串用 */
watch(
  () => props.rangeMode,
  () => {
    startValue.value = null;
    endValue.value = null;
  }
);

/** 重置内部状态（不触发事件，供 FilterArea 调用） */
const reset = () => {
  startValue.value = null;
  endValue.value = null;
  operator.value = "exact";
};

/** 判断值是否有效 */
const hasValue = (value: any) =>
  value !== null && value !== undefined && value !== "";

/**
 * 提交快速筛选：
 * - lookup 自定义操作符：按单值提交（fieldName__lookup=value）
 * - 范围模式：最小值 + 最大值区间（gte/lte），可只填一边
 * - 单值模式：比较符 + 单值（fieldName__lookup=value）
 */
const submit = () => {
  // lookup 自定义操作符：按单值提交
  if (props.lookup) {
    const value = startValue.value;
    if (!hasValue(value)) {
      emit("reset");
      return;
    }
    emit("filter", {
      cond1Operator: props.lookup,
      cond1Value: value
    });
    return;
  }

  // 范围模式：最小值 + 最大值区间（可只填一边）
  if (props.rangeMode) {
    const hasStart = hasValue(startValue.value);
    const hasEnd = hasValue(endValue.value);

    if (!hasStart && !hasEnd) {
      emit("reset");
      return;
    }

    emit("filter", {
      cond1Operator: hasStart ? "gte" : hasEnd ? "lte" : "",
      cond1Value: hasStart ? startValue.value : hasEnd ? endValue.value : "",
      cond2Operator: hasStart && hasEnd ? "lte" : "",
      cond2Value: hasStart && hasEnd ? endValue.value : ""
    });
    return;
  }

  // 单值模式：比较符 + 单值
  const value = startValue.value;
  if (!hasValue(value)) {
    emit("reset");
    return;
  }
  emit("filter", {
    cond1Operator: operator.value,
    cond1Value: value
  });
};

defineExpose<FilterInputExpose>({ reset, submit });
</script>

<template>
  <div class="number-input">
    <!-- 范围模式：最小值 + 最大值（同一行，可只填一边） -->
    <div v-if="!lookup && rangeMode" class="range-row">
      <el-input-number
        v-model="startValue"
        size="small"
        controls-position="right"
        placeholder="最小值"
        :disabled="disabled"
      />
      <span class="range-separator">至</span>
      <el-input-number
        v-model="endValue"
        size="small"
        controls-position="right"
        placeholder="最大值"
        :disabled="disabled"
      />
    </div>

    <!-- 单值模式：比较符下拉 + 单值输入（lookup 场景只显示单值输入，操作符固定） -->
    <div v-else class="range-row">
      <el-select
        v-if="!lookup"
        v-model="operator"
        class="operator-select"
        size="small"
        :teleported="false"
        :disabled="disabled"
      >
        <el-option
          v-for="op in NUMBER_OPERATOR_OPTIONS"
          :key="op.value"
          :label="op.label"
          :value="op.value"
        />
      </el-select>
      <el-input-number
        v-model="startValue"
        size="small"
        controls-position="right"
        placeholder="输入数值"
        :disabled="disabled"
      />
    </div>
  </div>
</template>

<style scoped>
.number-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.range-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
/* 范围模式最小值与最大值之间的"至"连接符 */
.range-separator {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}
.range-row .el-input-number {
  flex: 1;
}
/* 比较符下拉：紧凑宽度，与数值输入框并排 */
.operator-select {
  width: 100px;
  flex-shrink: 0;
}
.operator-select :deep(.el-input__wrapper) {
  border-radius: 6px;
}
/* 数值输入框圆角（与面板风格一致） */
.range-row :deep(.el-input__wrapper) {
  border-radius: 6px;
}
</style>
