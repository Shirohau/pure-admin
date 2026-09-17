<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
      <template #actionbar-right> <slot name="actionbar-right" /> </template>
      <template
        v-if="hasPerms.batchDestroy && !props.isSubTable"
        #pagination-left
      >
        <el-tooltip content="批量删除">
          <fs-button
            type="danger"
            icon="ion:trash-outline"
            :disabled="selectedData.length == 0"
            @click="handleBatchDelete"
          />
        </el-tooltip>
      </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import createCrudOptions, { componentName } from "./crud";

import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";

defineOptions({
  name: componentName
});
// 添加 props
const props = defineProps({
  isSubTable: {
    type: Boolean,
    default: false
  }
});
const { crudRef, crudBinding, crudExpose } = useFsRef();

//同步初始化crud
const {
  hasPerms,
  selectedData,
  crudOptions,
  resetCrudOptions,
  handleBatchDelete,
  FilterTags
} = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions
});

// 页面打开后获取列表数据
onMounted(() => {
  if (!props.isSubTable) {
    crudExpose.doRefresh();
  }
});
// 暴露给父组件
// getBaseTableRef/getTableData 用于子表场景（授权用户双表）：操作后刷新会清空选中，
// 需按 id 匹配当前数据行恢复另一侧表格的选中状态
defineExpose({
  crudExpose,
  crudOptions,
  resetCrudOptions,
  setSearchFormData: crudExpose.setSearchFormData,
  doRefresh: crudExpose.doRefresh,
  setTableData: crudExpose.setTableData,
  getBaseTableRef: crudExpose.getBaseTableRef,
  getTableData: crudExpose.getTableData,
  selectedData
});
</script>

<style lang="scss">
.user-roles-dialog {
  height: 100%;
}
</style>
