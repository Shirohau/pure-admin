<script setup lang="ts">
import { computed, ref } from "vue";
import type { FilterInputExpose, FilterResult, InputProps } from "../../types";

defineOptions({ name: "SelectInput" });

/**
 * 下拉输入组件（内嵌表格方案）
 * 不用 el-select：其弹窗会遮住"重置/确定"按钮；内嵌表格固定高度内滚动，不遮挡任何按钮
 * - 多选：checkbox 勾选或点击行切换（row-key + reserve-selection 保证搜索过滤时勾选不丢）
 * - lookup 单值：点击行选中/再点取消（行高亮用 row-class-name）
 */
const props = defineProps<InputProps>();

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
}>();

/** 表格实例引用（清除勾选） */
const tableRef = ref<any>(null);

/** 选中行对象列表（保存完整行以同时携带 value 与 label；多选为数组，lookup 场景也按数组维护，提交时取第一项） */
const selectedValue = ref<any[]>([]);

/** 搜索关键词（按 label 过滤选项） */
const keyword = ref("");

/** 是否 lookup 单值模式 */
const isLookup = computed(() => !!props.lookup);

/** 过滤后的选项列表（label 包含关键词） */
const filteredList = computed(() => {
  const list = props.selectList ?? [];
  const kw = keyword.value.trim();
  if (!kw) return list;
  return list.filter(item => String(item.label).includes(kw));
});

/** el-tag 合法类型集合（仅这些值作为标签类型渲染，避免非法值触发警告） */
const TAG_TYPES = ["primary", "success", "info", "warning", "danger"] as const;
type TagType = (typeof TAG_TYPES)[number];

/** 判断选项 color 是否为合法 el-tag 类型 */
const isValidTagType = (color: unknown): color is TagType =>
  TAG_TYPES.includes(color as TagType);

/** 重置内部状态（不触发事件，供 FilterArea 调用） */
const reset = () => {
  selectedValue.value = [];
  keyword.value = "";
  tableRef.value?.clearSelection();
};

/** 多选勾选变化：同步选中行对象列表（勾选列表包含被搜索过滤隐藏的已选项，提交完整集合） */
const handleSelectionChange = (rows: any[]) => {
  if (props.disabled) return;
  // 保存完整行对象（含 value/label），提交时 value 给后端、label 用于标签展示
  selectedValue.value = rows;
};

/**
 * 行点击：lookup 单值=点击选中/再点取消；多选=切换该行勾选（toggleRowSelection 触发
 * selection-change 自动同步选中列表，无需手动维护；搜索过滤后行对象引用稳定，仍可正确切换）
 */
const handleRowClick = (row: any, column: any) => {
  if (props.disabled) return;
  // 点击 checkbox 列本身会同时触发 selection-change，跳过避免重复切换
  if (column.type === "selection") return;
  if (isLookup.value) {
    selectedValue.value = selectedValue.value.some(i => i.value === row.value)
      ? []
      : [row];
  } else {
    const isSelected = selectedValue.value.some(i => i.value === row.value);
    tableRef.value?.toggleRowSelection(row, !isSelected);
  }
};

/** 行 class：lookup 单值模式高亮已选中行（选中值自行维护，过滤后重新渲染仍正确） */
const rowClassName = ({ row }: { row: any }) => {
  return isLookup.value && selectedValue.value.some(i => i.value === row.value)
    ? "selected-row"
    : "";
};

/** 清空所有已选值 */
const clearSelection = () => {
  reset();
};

/**
 * 提交筛选：lookup 按第一项单值提交（fieldName__lookup=value）；默认多选提交 in（值逗号拼接）
 */
const submit = () => {
  if (!selectedValue.value.length) {
    emit("reset");
    return;
  }
  const values = selectedValue.value.map(row => row.value);
  emit("filter", {
    cond1Operator: props.lookup || "in",
    // lookup 场景单值提交；多选场景逗号拼接（选项值可能为数字，join 后由后端统一按字符串解析）
    cond1Value: props.lookup ? values[0] : values.join(","),
    // label 元数据仅用于 FilterTags 标签展示，提交给后端的一律是 value
    cond1Labels: selectedValue.value.map(row => row.label)
  });
};

defineExpose<FilterInputExpose>({ reset, submit });
</script>

<template>
  <div class="table-select">
    <!-- 搜索行：搜索框 + 清空按钮（无选中时清空按钮禁用） -->
    <div class="search-row">
      <el-input
        v-model="keyword"
        size="small"
        placeholder="搜索选项"
        clearable
        :disabled="disabled"
      />
      <el-button
        link
        type="danger"
        size="small"
        :disabled="disabled || !selectedValue.length"
        @click="clearSelection"
        >清空</el-button
      >
    </div>

    <!-- 选项表格：固定高度内滚动，内嵌面板不悬浮、不遮挡操作按钮（disabled 时禁止交互，与 CascaderInput 禁用语义一致） -->
    <el-table
      ref="tableRef"
      :data="filteredList"
      size="small"
      height="200"
      row-key="value"
      :class="{ 'is-disabled': disabled }"
      :row-class-name="rowClassName"
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
    >
      <!-- reserve-selection：data 变化（搜索过滤）时保留勾选，需配合 row-key -->
      <el-table-column
        v-if="!isLookup"
        type="selection"
        width="36"
        reserve-selection
      />
      <el-table-column label="选项" prop="label" show-overflow-tooltip>
        <!-- 带 color 配置的选项渲染为彩色标签（如字典颜色），否则回退为普通文本 -->
        <template #default="{ row }">
          <el-tag
            v-if="isValidTagType(row.color)"
            :type="row.color"
            size="small"
          >
            {{ row.label }}
          </el-tag>
          <span v-else>{{ row.label }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
/* 整体纵向布局：搜索行 → 表格 */
.table-select {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
/* 搜索行：搜索框占满剩余宽度，清空按钮居右 */
.search-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.search-row .el-input {
  flex: 1;
}
/* 表格圆角边框（与 CascaderInput 树容器风格一致） */
.table-select :deep(.el-table) {
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  /* 裁剪内部背景与滚动条，保证圆角完整 */
  overflow: hidden;
}
/* 空值筛选选中（disabled）时禁止表格交互（el-table 无 disabled prop，用 pointer-events 拦截） */
.table-select :deep(.el-table.is-disabled) {
  pointer-events: none;
}
/* lookup 单值模式已选中行高亮（hover 时同样保持，避免被表格默认 hover 背景覆盖） */
.table-select :deep(.el-table .selected-row > td.el-table__cell),
.table-select :deep(.el-table .selected-row:hover > td.el-table__cell) {
  background-color: #ecf5ff;
}
</style>
