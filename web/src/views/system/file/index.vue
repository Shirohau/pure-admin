<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import createCrudOptions, { componentName } from "./crud";
defineOptions({
  name: componentName
});

import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";

const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
const { FilterTags } = useFs({
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
