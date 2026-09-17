<template>
  <fs-page>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom><FilterTags /></template>
      <template #pagination-left>
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
  </fs-page>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import createCrudOptions, { componentName } from "./crud";
import { useMenuTree } from "../../../hooks/useMenuTree";

defineOptions({
  name: componentName
});

const { menuButtonExpose } = useMenuTree();
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
  menuButtonExpose.value = crudExpose;
  // crudExpose.doRefresh();
});
</script>
