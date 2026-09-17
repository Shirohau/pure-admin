<script setup lang="ts">
import { ref, watch } from "vue";
import type { PropType } from "vue";
import type { FilterType, FilterResult } from "./types";
import { IconifyIconOffline } from "@/components/ReIcon";
import SortArea from "./components/SortArea.vue";
import FilterArea from "./components/FilterArea.vue";

import sortUp from "~icons/bx/sort-up";
import sortDown from "~icons/bx/sort-down";
import funnel from "~icons/qlementine-icons/funnel-16";

const props = defineProps({
  /** 筛选类型：text | number | select | date | datetime | cascader（配置见 registry/） */
  type: {
    type: String as PropType<FilterType>,
    default: "text"
  },
  /** 列标题 */
  columnLabel: {
    type: String,
    default: ""
  },
  /** 提示信息 */
  tooltip: {
    type: String,
    default: ""
  },
  /** 选项列表（select/cascader 类型使用） */
  selectList: {
    type: Array as PropType<{ label: string; value: any; children?: any[] }[]>,
    default: () => []
  },
  /** 日期筛选是否带时区 */
  useTimezone: {
    type: Boolean,
    default: false
  },
  /** 自定义筛选操作符（如 exact/contains/gt，提交 fieldName__lookup=value） */
  lookup: {
    type: String,
    default: ""
  },
  /** 是否隐藏空值筛选（空/非空 复选框） */
  hideEmpty: {
    type: Boolean,
    default: false
  },
  /** 级联选择器 props 覆盖（type="cascader" 时使用） */
  cascaderProps: {
    type: Object as PropType<Record<string, any>>,
    default: () => ({})
  },
  /** 筛选版本号（外部清除时递增，用于同步重置面板状态） */
  filterVersion: {
    type: Number,
    default: 0
  },
  /** 最近被清除的字段名（用于精确匹配重置） */
  clearedField: {
    type: String as PropType<string | null>,
    default: null
  },
  /** 字段名（用于匹配 clearedField） */
  fieldName: {
    type: String,
    default: ""
  }
});

const popoverVisible = ref(false);
/** 筛选激活（控制漏斗图标高亮） */
const filterActive = ref(false);
/** 排序方向：'' | 'asc' | 'desc' */
const sortOrder = ref("");

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
  sort: [direction: string | null];
}>();

defineOptions({ name: "ReFilter" });

const handleSortChange = (val: string | null) => {
  popoverVisible.value = false;
  sortOrder.value = val;
  emit("sort", val);
};

const handleFilter = (val: FilterResult) => {
  popoverVisible.value = false;
  filterActive.value = true;
  emit("filter", val);
};

const handleReset = () => {
  popoverVisible.value = false;
  filterActive.value = false;
  emit("reset");
};

/** 外部清除信号：__ALL__ 重置筛选+排序图标；匹配字段名仅重置筛选图标 */
watch(
  () => props.filterVersion,
  () => {
    if (props.clearedField === "__ALL__") {
      filterActive.value = false;
      sortOrder.value = "";
    } else if (props.clearedField === props.fieldName) {
      filterActive.value = false;
    }
  }
);
</script>

<template>
  <span class="flex justify-between">
    <div class="flex items-center gap-1">
      {{ props.columnLabel }}
      <el-tooltip
        v-if="props.tooltip"
        :content="props.tooltip"
        effect="dark"
        placement="top-start"
      >
        <el-icon><InfoFilled /></el-icon>
      </el-tooltip>
    </div>
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom"
      trigger="click"
      width="280"
      popper-style="padding: 12px 14px; border-radius: 10px; border: 1px solid #e4e7ed; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1)"
    >
      <!-- 触发元素：排序图标 + 漏斗图标 -->
      <template #reference>
        <div class="inline-flex items-center gap-0.5 cursor-pointer">
          <span style="font-size: 14px; color: #409eff">
            <IconifyIconOffline
              v-if="sortOrder !== ''"
              :icon="sortOrder === 'desc' ? sortDown : sortUp"
            />
          </span>
          <el-button link>
            <template #icon>
              <IconifyIconOffline
                :icon="funnel"
                :style="
                  filterActive ? { color: '#409eff' } : { color: '#909399' }
                "
              />
            </template>
          </el-button>
        </div>
      </template>
      <template #default>
        <div @click.stop>
          <SortArea
            :filter-version="props.filterVersion"
            :cleared-field="props.clearedField"
            @sort="handleSortChange"
          />
          <FilterArea
            :type="props.type"
            :column-label="props.columnLabel"
            :use-timezone="props.useTimezone"
            :select-list="props.selectList"
            :lookup="props.lookup"
            :hide-empty="props.hideEmpty"
            :cascader-props="props.cascaderProps"
            :filter-version="props.filterVersion"
            :field-name="props.fieldName"
            :cleared-field="props.clearedField"
            @filter="handleFilter"
            @reset="handleReset"
          />
        </div>
      </template>
    </el-popover>
  </span>
</template>
