<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
      <template #pagination-left>
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

const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
const { hasPerms, selectedData, handleBatchDelete, FilterTags } = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions
});

// 页面打开后获取列表数据
onMounted(() => {
  crudExpose.doRefresh();
});
</script>

<style lang="scss" scoped>
.main-content {
  height: 100%;
  padding: 10px;
  margin: 0 !important;
  background-color: var(--el-bg-color);
}
</style>
