<script setup lang="ts">
import { computed, ref, watch } from "vue";
import dayjs from "dayjs";
import type { FilterInputExpose, FilterResult, InputProps } from "../../types";
import { getUnitDateRange } from "../../dateUtils";

defineOptions({ name: "DateInput" });

/** 日期输入组件（date / datetime 共用）：date 模式可切 年/月/周/日 维度，datetime 模式精确到时分秒；均支持单选↔范围 */

/** 日期维度：year | month | week | date（仅 date 模式可切换） */
type DateDimension = "year" | "month" | "week" | "date";

/** 输入模式：date=日期（可切维度）；datetime=日期时间（精确到时分秒） */
const props = withDefaults(
  defineProps<
    InputProps & {
      /** 输入模式：date（可切维度）/ datetime（精确到时分秒） */
      mode?: "date" | "datetime";
      /** 范围模式开关（FilterArea v-model 管理）：true=范围选择，false=单值 */
      rangeMode?: boolean;
    }
  >(),
  { mode: "date", rangeMode: false }
);

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
  "update:rangeMode": [value: boolean];
  /** 当前维度是否支持范围（周维度不支持）：供 FilterArea 隐藏/显示“范围”勾选 */
  "update:rangeSupported": [value: boolean];
}>();

// ==================== 快捷项配置 ====================

/** 日维度单值快捷项（点击直接选中该日期） */
const dateShortcuts = [
  { text: "今天", value: () => dayjs().toDate() },
  { text: "昨天", value: () => dayjs().subtract(1, "day").toDate() }
];

/**
 * 日维度范围快捷项（仅日维度范围模式提供）：
 * 本周至今/本月至今/本年至今（起始~今天）、上周/上月/上年（完整时段）
 * 周以周一为一周起点
 */
const rangeShortcuts = [
  {
    text: "本周至今",
    value: () => {
      const dow = dayjs().day();
      const start = dayjs()
        .subtract(dow === 0 ? 6 : dow - 1, "day")
        .startOf("day");
      return [start.toDate(), dayjs().endOf("day").toDate()];
    }
  },
  {
    text: "本月至今",
    value: () => [
      dayjs().startOf("month").toDate(),
      dayjs().endOf("day").toDate()
    ]
  },
  {
    text: "本年至今",
    value: () => [
      dayjs().startOf("year").toDate(),
      dayjs().endOf("day").toDate()
    ]
  },
  {
    text: "上周",
    value: () => {
      const dow = dayjs().day();
      const start = dayjs()
        .subtract(dow === 0 ? 6 : dow - 1, "day")
        .subtract(1, "week")
        .startOf("day");
      return [start.toDate(), start.add(6, "day").endOf("day").toDate()];
    }
  },
  {
    text: "上月",
    value: () => {
      const base = dayjs().subtract(1, "month");
      return [base.startOf("month").toDate(), base.endOf("month").toDate()];
    }
  },
  {
    text: "上年",
    value: () => {
      const base = dayjs().subtract(1, "year");
      return [base.startOf("year").toDate(), base.endOf("year").toDate()];
    }
  }
];

/** 日/日期时间单值比较符选项：标签 → 后端 lookup（默认 =，提交 fieldName__lookup=value） */
const DATE_OPERATOR_OPTIONS = [
  { label: "等于", value: "exact" },
  { label: "大于", value: "gt" },
  { label: "大于等于", value: "gte" },
  { label: "小于", value: "lt" },
  { label: "小于等于", value: "lte" }
];

// ==================== 本地状态 ====================

/** 当前日期维度（仅 date 模式可切换，默认日） */
const activeDimension = ref<DateDimension>("date");
/** 单值模式选中值（date/week/month/year 的值为单位起始日期字符串） */
const startValue = ref<any>(null);
/** 范围模式选中值（range picker 的 [起始, 结束] 数组） */
const rangeValue = ref<any[]>([]);
/** 日/日期时间单值比较符（默认 =；切换维度或重置时恢复默认） */
const operator = ref("exact");

// ==================== 计算属性 ====================

/** 当前实际生效的类型（datetime 模式固定为 datetime；date 模式跟随面板维度） */
const effectiveType = computed<"date" | "datetime" | DateDimension>(() =>
  props.mode === "datetime" ? "datetime" : activeDimension.value
);

/** 是否为固定日期单位筛选（week/month/year 单选时扩展为完整区间提交） */
const isUnitType = computed(() =>
  ["week", "month", "year"].includes(effectiveType.value)
);

/** 是否为范围模式（开启范围开关且当前维度可范围选择；周维度不提供范围） */
const isRangePick = computed(
  () => props.rangeMode && effectiveType.value !== "week"
);

/** 当前维度是否支持范围（周维度不支持，其余维度及 datetime 均支持） */
const rangeSupported = computed(() => effectiveType.value !== "week");

/** 是否显示比较符下拉：日/日期时间单值模式（范围模式/周月年/lookup 场景均不显示） */
const showOperatorSelect = computed(
  () =>
    ["date", "datetime"].includes(effectiveType.value) &&
    !isRangePick.value &&
    !props.lookup
);

/** 范围选择器类型（yearrange/monthrange/datetimerange/daterange） */
const rangePickerType = computed<
  "yearrange" | "monthrange" | "datetimerange" | "daterange"
>(() => {
  switch (effectiveType.value) {
    case "year":
      return "yearrange";
    case "month":
      return "monthrange";
    case "datetime":
      return "datetimerange";
    default:
      return "daterange";
  }
});

/** 单值选择器类型（week/month/year 显示单位面板） */
const pickerType = computed<"date" | "datetime" | "week" | "month" | "year">(
  () => {
    if (
      effectiveType.value === "datetime" ||
      effectiveType.value === "week" ||
      effectiveType.value === "month" ||
      effectiveType.value === "year"
    )
      return effectiveType.value;
    return "date";
  }
);

/** 范围模式快捷项：仅日维度提供（本周至今/本月至今/本年至今/上周/上月/上年） */
const rangePickerShortcuts = computed(() =>
  effectiveType.value === "date" ? rangeShortcuts : undefined
);

/** 单值模式快捷项：仅日维度提供（今天/昨天） */
const singleDateShortcuts = computed(() =>
  effectiveType.value === "date" ? dateShortcuts : undefined
);

/** 单值选择器占位符（按维度区分） */
const inputPlaceholder = computed(() => {
  switch (effectiveType.value) {
    case "date":
      return "选择日期";
    case "datetime":
      return "选择时间";
    case "week":
      return "选择周";
    case "month":
      return "选择月份";
    case "year":
      return "选择年份";
    default:
      return "选择日期";
  }
});

/** 范围模式起始占位符 */
const rangeStartPlaceholder = computed(() => {
  switch (effectiveType.value) {
    case "year":
      return "起始年份";
    case "month":
      return "起始月份";
    case "datetime":
      return "开始时间";
    default:
      return "开始日期";
  }
});

/** 范围模式结束占位符 */
const rangeEndPlaceholder = computed(() => {
  switch (effectiveType.value) {
    case "year":
      return "结束年份";
    case "month":
      return "结束月份";
    case "datetime":
      return "结束时间";
    default:
      return "结束日期";
  }
});

/** 选择器输入框显示格式（datetime 含时分秒，year/month 显示单位，week 显示周数） */
const dateDisplayFormat = computed(() => {
  switch (effectiveType.value) {
    case "year":
      return "YYYY";
    case "month":
      return "YYYY-MM";
    case "datetime":
      return "YYYY-MM-DD HH:mm:ss";
    case "week":
      return "[第] ww [周]";
    default:
      return "YYYY-MM-DD";
  }
});

/** 选择器值格式（datetime 含时分秒，其余 YYYY-MM-DD） */
const dateValueFormat = computed(() =>
  effectiveType.value === "datetime" ? "YYYY-MM-DD HH:mm:ss" : "YYYY-MM-DD"
);

/**
 * 日期值格式化：
 * - useTimezone 开启时转为携带本地时区偏移的 ISO 字符串（如 2026-07-31T10:30:00+08:00）
 * - week/month/year 提交的是扩展后的日期区间字符串（YYYY-MM-DD），无时区概念，保持原值
 */
const formatDateValue = (value: any) => {
  if (value === null || value === undefined || value === "") return value;
  if (isUnitType.value) return value;
  return props.useTimezone ? dayjs(value).format() : value;
};

// ==================== 状态同步 ====================

/** 范围模式切换（FilterArea 开关控制）：清空已选值，避免单值与区间值串用 */
watch(
  () => props.rangeMode,
  () => {
    startValue.value = null;
    rangeValue.value = [];
  }
);

/** 范围支持状态变化（切到周维度时）：上报给 FilterArea 隐藏“范围”勾选 */
watch(rangeSupported, val => {
  emit("update:rangeSupported", val);
});

/**
 * 切换日期维度：仅清空已选值，避免不同粒度的值串用；
 * 周维度不提供范围，切到周时同步取消“范围”勾选，其余维度（年/月/日）间切换保留勾选
 */
const handleDimensionChange = (val: string | number | boolean) => {
  activeDimension.value = val as DateDimension;
  startValue.value = null;
  rangeValue.value = [];
  operator.value = "exact";
  if (val === "week") {
    emit("update:rangeMode", false);
  }
};

/** 重置内部状态（不触发事件，供 FilterArea 调用） */
const reset = () => {
  activeDimension.value = "date";
  startValue.value = null;
  rangeValue.value = [];
  operator.value = "exact";
};

/**
 * 提交筛选（按当前维度与范围模式分发）：
 * - lookup：单值提交 fieldName__lookup=value
 * - 范围模式：起始单位首日 + 结束单位末日（如 2024 ~ 2026 → gte 2024-01-01 + lte 2026-12-31）
 * - 周/月/年单值：扩展为完整日期区间；日/日期时间单值：按所选比较符提交（默认 exact）
 */
const submit = () => {
  // lookup 自定义操作符：按单值提交
  if (props.lookup) {
    const value = startValue.value;
    if (value === null || value === undefined || value === "") {
      emit("reset");
      return;
    }
    emit("filter", {
      cond1Operator: props.lookup,
      cond1Value: value
    });
    return;
  }

  // 1. 范围模式：起始单位首日 + 结束单位末日（如 2024 ~ 2026 → gte 2024-01-01 + lte 2026-12-31）
  if (isRangePick.value) {
    const [startUnit, endUnit] = rangeValue.value || [];
    if (!startUnit || !endUnit) {
      emit("reset");
      return;
    }
    // datetime 范围：值已是完整日期时间，直接作为 gte/lte 提交
    if (effectiveType.value === "datetime") {
      emit("filter", {
        cond1Operator: "gte",
        cond1Value: formatDateValue(startUnit),
        cond2Operator: "lte",
        cond2Value: formatDateValue(endUnit)
      });
      return;
    }
    // 年/月/日范围：起始单位首日 + 结束单位末日
    const startRange = getUnitDateRange(startUnit, effectiveType.value);
    const endRange = getUnitDateRange(endUnit, effectiveType.value);
    if (!startRange || !endRange) {
      emit("reset");
      return;
    }
    emit("filter", {
      cond1Operator: "gte",
      cond1Value: startRange.start,
      cond2Operator: "lte",
      cond2Value: endRange.end
    });
    return;
  }

  // 2. 日/日期时间单值：按所选比较符提交（默认 exact）
  if (effectiveType.value === "date" || effectiveType.value === "datetime") {
    const value = startValue.value;
    if (value === null || value === undefined || value === "") {
      emit("reset");
      return;
    }
    emit("filter", {
      cond1Operator: operator.value,
      cond1Value: formatDateValue(value)
    });
    return;
  }

  // 3. 周/月/年单值：扩展为完整日期区间
  const range = getUnitDateRange(startValue.value, effectiveType.value);
  if (!range) {
    emit("reset");
    return;
  }
  emit("filter", {
    cond1Operator: "gte",
    cond1Value: range.start,
    cond2Operator: "lte",
    cond2Value: range.end
  });
};

defineExpose<FilterInputExpose>({ reset, submit });
</script>

<template>
  <div class="date-input">
    <!-- 日期维度切换（仅 date 模式；radio-group 按钮自带选中态，无滑块挂载动画） -->
    <div v-if="mode === 'date'" class="dimension-switch">
      <el-radio-group
        :model-value="activeDimension"
        size="small"
        @update:model-value="handleDimensionChange"
      >
        <el-radio-button value="year">年</el-radio-button>
        <el-radio-button value="month">月</el-radio-button>
        <el-radio-button value="week">周</el-radio-button>
        <el-radio-button value="date">日</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 输入区：范围模式 → 单个 range 选择器；单值模式 → 单个日期/时间选择器 -->
    <div v-if="isRangePick" class="range-row">
      <el-date-picker
        :key="'range-' + rangePickerType"
        v-model="rangeValue"
        :type="rangePickerType"
        size="small"
        :start-placeholder="rangeStartPlaceholder"
        :end-placeholder="rangeEndPlaceholder"
        range-separator="至"
        :format="dateDisplayFormat"
        :value-format="dateValueFormat"
        :shortcuts="rangePickerShortcuts"
        :teleported="false"
        :disabled="disabled"
      />
    </div>
    <div v-else class="range-row">
      <!-- 比较符下拉：日/日期时间单值模式显示（默认 =） -->
      <el-select
        v-if="showOperatorSelect"
        v-model="operator"
        class="operator-select"
        size="small"
        :teleported="false"
        :disabled="disabled"
      >
        <el-option
          v-for="op in DATE_OPERATOR_OPTIONS"
          :key="op.value"
          :label="op.label"
          :value="op.value"
        />
      </el-select>
      <el-date-picker
        :key="'single-' + pickerType"
        v-model="startValue"
        :type="pickerType"
        size="small"
        :placeholder="inputPlaceholder"
        :format="dateDisplayFormat"
        :value-format="dateValueFormat"
        :shortcuts="singleDateShortcuts"
        :teleported="false"
        :disabled="disabled"
      />
    </div>
  </div>
</template>

<style scoped>
.date-input {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dimension-switch :deep(.el-radio-group) {
  display: flex;
  width: 100%;
}
.dimension-switch :deep(.el-radio-button) {
  flex: 1;
}
.dimension-switch :deep(.el-radio-button__inner) {
  width: 100%;
  text-align: center;
}
/* 维度切换按钮组圆角（首尾圆角，与面板风格一致） */
.dimension-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 6px 0 0 6px;
}
.dimension-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 6px 6px 0;
}
.range-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
/* 选择器根元素为 .el-date-editor：单值/范围均占满行宽（日维度与比较符并排时占剩余空间） */
.range-row :deep(.el-date-editor) {
  flex: 1;
}
/* 比较符下拉：紧凑宽度，与日期选择器并排 */
.operator-select {
  width: 100px;
  flex-shrink: 0;
}
.operator-select :deep(.el-input__wrapper) {
  border-radius: 6px;
}
/* 日期选择器输入框圆角 */
.range-row :deep(.el-input__wrapper) {
  border-radius: 6px;
}
</style>
