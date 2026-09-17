<script setup lang="ts">
import { ref, watch } from "vue";
import type { PropType } from "vue";
import { IconifyIconOffline } from "@/components/ReIcon";
import sortUp from "~icons/bx/sort-up";
import sortDown from "~icons/bx/sort-down";

defineOptions({ name: "SortArea" });

const props = defineProps({
  /** 筛选版本号（外部清除时递增） */
  filterVersion: {
    type: Number,
    default: 0
  },
  /** 最近被清除的字段名（"__ALL__" 表示清除全部） */
  clearedField: {
    type: String as PropType<string | null>,
    default: null
  }
});

const emit = defineEmits<{
  /** 排序变更：'' 表示清除排序，'asc'/'desc' 表示升降序 */
  sort: [direction: string | null];
}>();

/** 当前排序方向：'' | 'asc' | 'desc' */
const sortOrder = ref("");

/** 外部清除全部时同步清除排序高亮（删除单个筛选 tag 不影响排序） */
watch(
  () => props.filterVersion,
  () => {
    if (props.clearedField === "__ALL__") {
      sortOrder.value = "";
    }
  }
);

/** 点击排序：再次点击同一方向取消排序，否则切换 */
const handleSort = (direction: string) => {
  if (sortOrder.value === direction) {
    sortOrder.value = "";
    emit("sort", "");
  } else {
    sortOrder.value = direction;
    emit("sort", direction);
  }
};
</script>

<template>
  <div class="sort-area">
    <el-button
      :class="{ 'is-active': sortOrder === 'asc' }"
      size="small"
      @click="handleSort('asc')"
    >
      <template #icon>
        <IconifyIconOffline :icon="sortUp" />
      </template>
      <span>升序</span>
    </el-button>
    <el-button
      :class="{ 'is-active': sortOrder === 'desc' }"
      size="small"
      @click="handleSort('desc')"
    >
      <template #icon>
        <IconifyIconOffline :icon="sortDown" />
      </template>
      <span>降序</span>
    </el-button>
  </div>
</template>

<style scoped>
.sort-area {
  display: flex;
  gap: 8px;
  margin-bottom: 2px;
}

.sort-area .el-button {
  flex: 1;
  margin: 0;
  border-radius: 6px;
  transition: all 0.2s ease;
}

/* 选中态：淡主色背景 + 主色文字与边框 */
.sort-area .el-button.is-active {
  color: #409eff;
  background: #ecf5ff;
  border-color: #a0cfff;
}
.sort-area .el-button.is-active:hover {
  color: #409eff;
  background: #d9ecff;
  border-color: #79bbff;
}

/* 未选中 hover：主色描边 */
.sort-area .el-button:not(.is-active):hover {
  color: #409eff;
  border-color: #a0cfff;
}

/* 图标与文字间距 */
.sort-area .el-button span {
  margin-left: 2px;
}
</style>
