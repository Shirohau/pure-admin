<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
      <template #actionbar-right> <slot name="actionbar-right" /> </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import createCrudOptions, { componentName } from "./crud";

import { computed, onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";

defineOptions({
  name: componentName
});
// 添加 props
const props = defineProps({
  ids: {
    type: String,
    default: () => "" as string | undefined
  },
  lookup: {
    type: String,
    default: () => "" as string | undefined
  }
});
const { crudRef, crudBinding, crudExpose } = useFsRef();
const queryParams = computed(() => {
  return { [props.lookup]: props.ids || [] };
});
//同步初始化crud
const { selectedData, FilterTags, clearAllFilters } = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context: { queryParams },
  createCrudOptions
});

// 页面打开后获取列表数据
onMounted(() => {
  crudExpose.doRefresh();
});
// 暴露给父组件
// getBaseTableRef/getTableData 用于子表场景（授权用户双表）：操作后刷新会清空选中，
// 需按 id 匹配当前数据行恢复另一侧表格的选中状态
// clearAllFilters 用于穿梭操作后清除列头筛选/排序状态（筛选标签、面板输入、图标一并重置）
defineExpose({
  crudExpose,
  selectedData,
  clearAllFilters
});
</script>

<style lang="scss">
.user-roles-dialog {
  height: 100%;
}
</style>
