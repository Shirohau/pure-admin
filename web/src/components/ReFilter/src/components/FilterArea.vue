<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { PropType } from "vue";
import { resolveNextEmptyMode, toIsnullResult } from "../emptyFilter";
import type { EmptyFilterMode } from "../emptyFilter";
import { getTypeConfig } from "../registry";
import type { FilterInputExpose, FilterResult, FilterType } from "../types";

defineOptions({ name: "FilterArea" });

/**
 * 筛选面板骨架（注册表驱动）：标题行（列名 + 空/非空）→ 输入区（按类型配置渲染输入组件）→ 操作行（范围开关 + 重置/确定）
 * 输入组件统一实现 FilterInputExpose 协议，本组件负责编排空值筛选、重置与提交转发
 */

const props = defineProps({
  /** 筛选类型：text | number | select | date | datetime | cascader */
  type: { type: String as () => FilterType, default: "text" },
  /** 列标题（筛选面板标题展示） */
  columnLabel: { type: String, default: "" },
  /** 日期筛选是否带时区（datetime 类型开启时提交携带本地时区偏移的 ISO 字符串） */
  useTimezone: { type: Boolean, default: false },
  /** 下拉/级联选项列表 */
  selectList: {
    type: Array as () => Array<{ label: string; value: any; children?: any[] }>,
    default: () => []
  },
  /** 自定义筛选操作符（lookup）：如 "exact"、"contains"、"gt" 等，提交 fieldName__lookup=value */
  lookup: {
    type: String,
    default: ""
  },
  /** 是否隐藏空值筛选（空/非空 复选框，默认 false 即显示） */
  hideEmpty: {
    type: Boolean,
    default: false
  },
  /** 级联选择器 props 覆盖（type="cascader" 时使用，如自定义字段映射 { value: 'id', label: 'title' }） */
  cascaderProps: {
    type: Object as () => Record<string, any>,
    default: () => ({})
  },
  /** 筛选版本号（外部 tag 清除时递增，配合 clearedField 精确匹配后重置面板状态） */
  filterVersion: { type: Number, default: 0 },
  /** 字段名（用于匹配 clearedField，仅清除本字段时重置面板） */
  fieldName: { type: String, default: "" },
  /** 最近被清除的字段名（"__ALL__" 表示清除全部，null 表示无清除） */
  clearedField: {
    type: String as PropType<string | null>,
    default: null
  }
});

const emit = defineEmits<{
  reset: [];
  filter: [result: FilterResult];
}>();

// ==================== 类型配置（注册表驱动） ====================

/** 当前类型的注册配置（决定输入组件、范围开关等） */
const config = computed(() => getTypeConfig(props.type));

/** 是否显示"范围"开关：类型支持范围切换、非 lookup 场景，且当前维度支持范围 */
const showRangeSwitch = computed(
  () => !props.lookup && !!config.value.supportsRange && rangeSupported.value
);

// ==================== 本地状态 ====================

/** 当前输入组件的实例引用（调用其 reset / submit 协议方法） */
const inputRef = ref<FilterInputExpose | null>(null);
/** 空值筛选模式（undefined/"" 未选；"isnull" 为空；"notnull" 不为空，勾选时禁用输入并提交 isnull 筛选） */
const emptyMode = ref<EmptyFilterMode | undefined>("");
/** 范围模式开关（date/datetime 的单值 ↔ 区间切换，与输入组件 v-model 同步） */
const rangeMode = ref(false);

/** 当前维度是否支持范围（由输入组件上报：如周维度不支持，隐藏"范围"勾选；默认 true） */
const rangeSupported = ref(true);

// ==================== 重置逻辑 ====================

/** 重置面板内部所有状态（不触发任何事件） */
const resetInternal = () => {
  emptyMode.value = "";
  rangeMode.value = false;
  rangeSupported.value = true;
  inputRef.value?.reset();
};

/**
 * 监听外部 tag 清除信号（useFilter 的 removeFilterKey / clearAllFilters）：
 * 仅清除全部或本字段时才重置面板，避免删除其他字段 tag 时误清空本面板的输入
 */
watch(
  () => props.filterVersion,
  () => {
    if (
      props.clearedField === "__ALL__" ||
      props.clearedField === props.fieldName
    ) {
      resetInternal();
    }
  }
);

/** 重置筛选：清空本地状态并通知父组件 */
const resetFilters = () => {
  resetInternal();
  emit("reset");
};

// ==================== 输入组件回调 ====================

/** 输入组件提交筛选：透传结果 */
const handleInputFilter = (result: FilterResult) => {
  emit("filter", result);
};

/** 输入组件内部判定无有效值（提交时自行触发）：清空状态并通知父组件清除该字段筛选 */
const handleInputReset = () => {
  resetInternal();
  emit("reset");
};

/**
 * 空值复选框切换（互斥 + 可取消，目标状态由 resolveNextEmptyMode 推导）：
 * - 勾选时清空输入并禁用输入控件；取消勾选则恢复输入（等待点击确定后再触发筛选）
 */
const toggleEmptyMode = (mode: Exclude<EmptyFilterMode, "">) => {
  emptyMode.value = resolveNextEmptyMode(emptyMode.value, mode);
  if (emptyMode.value) {
    inputRef.value?.reset();
  }
};

// ==================== 提交逻辑 ====================

/** 确定：空值筛选优先（为空/不为空），否则委托输入组件提交（输入组件内部处理各类型的提交语义） */
const handleConfirm = () => {
  if (emptyMode.value) {
    // 为空 → isnull=true（NULL + 空字符串）；不为空 → isnull=false（非 NULL 且非空字符串）
    emit("filter", toIsnullResult(emptyMode.value));
    return;
  }
  inputRef.value?.submit();
};
</script>

<template>
  <div class="filter-panel">
    <el-divider style="margin: 8px 0" />
    <!-- 标题行：列名 + 空值筛选（空/非空 复选框，互斥、再点取消） -->
    <div class="filter-title-row">
      <span class="filter-title">{{ props.columnLabel }}</span>
      <div v-if="!props.hideEmpty" class="empty-mode-wrap">
        <el-checkbox
          :model-value="emptyMode === 'isnull'"
          size="small"
          @update:model-value="toggleEmptyMode('isnull')"
          >空</el-checkbox
        >
        <el-checkbox
          :model-value="emptyMode === 'notnull'"
          size="small"
          @update:model-value="toggleEmptyMode('notnull')"
          >非空</el-checkbox
        >
      </div>
    </div>

    <!-- 输入区：按类型注册表动态渲染输入组件（mode/rangeMode 由配置与状态注入） -->
    <div class="filter-body">
      <component
        :is="config.inputComponent"
        ref="inputRef"
        v-bind="config.inputProps"
        :select-list="props.selectList"
        :cascader-props="props.cascaderProps"
        :use-timezone="props.useTimezone"
        :lookup="props.lookup"
        :disabled="!!emptyMode"
        :range-mode="config.supportsRange ? rangeMode : undefined"
        @update:range-mode="rangeMode = !!$event"
        @update:range-supported="rangeSupported = $event"
        @filter="handleInputFilter"
        @reset="handleInputReset"
      />
    </div>

    <!-- 操作按钮行：范围开关（number/date/datetime）在左，重置/确定在右 -->
    <div class="filter-actions">
      <div class="left-actions">
        <!-- 范围筛选开关：勾选=范围，取消勾选=单值；勾选空/非空时禁用（空值筛选不区分单值/范围） -->
        <el-checkbox
          v-if="showRangeSwitch"
          :model-value="rangeMode"
          size="small"
          :disabled="!!emptyMode"
          @update:model-value="rangeMode = !!$event"
          >范围</el-checkbox
        >
      </div>
      <div class="right-actions">
        <el-button size="small" @click="resetFilters">重置</el-button>
        <el-button size="small" type="primary" @click="handleConfirm"
          >确定</el-button
        >
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 标题行：列名 + 空值筛选标签，简单布局，不做背景修饰 */
.filter-title-row {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

/* 空值筛选区域：两个互斥复选框（空/非空），整体不随列名收缩 */
.empty-mode-wrap {
  display: flex;
  flex-shrink: 0;
  gap: 16px;
  align-items: center;
}

/* 空值筛选复选框：重置 Element Plus 默认右间距（统一由 gap 控制，再点已勾选的可取消） */
.empty-mode-wrap .el-checkbox {
  margin-right: 0;
}

.filter-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.filter-body {
  margin-bottom: 4px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.filter-actions .left-actions {
  display: flex;
}

.filter-actions .right-actions {
  display: flex;
}

/* 按钮圆角统一（与面板 10px 圆角呼应） */
.filter-actions .el-button {
  border-radius: 6px;
}
</style>
