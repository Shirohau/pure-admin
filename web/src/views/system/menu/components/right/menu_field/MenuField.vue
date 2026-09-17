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
  name: "MenuField"
});

const { menuFieldExpose } = useMenuTree();

const { crudRef, crudBinding, context, crudExpose } = useFsRef();
//同步初始化crud

const { selectedData, FilterTags, handleBatchDelete } = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context,
  createCrudOptions
});
// 页面打开后获取列表数据
onMounted(() => {
  menuFieldExpose.value = crudExpose;
  // crudExpose.doRefresh();
});
</script>
