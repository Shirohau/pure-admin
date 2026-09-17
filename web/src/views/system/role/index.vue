<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
      <template v-if="!props.isSubTable" #pagination-left>
        <el-tooltip v-if="hasPerms.batchDestroy" content="批量删除">
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
defineExpose({
  crudOptions,
  resetCrudOptions,
  setSearchFormData: crudExpose.setSearchFormData,
  doRefresh: crudExpose.doRefresh
});
</script>
