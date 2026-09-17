<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding" />
  </div>
</template>

<script lang="ts" setup>
import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";

import createCrudOptions, { componentName } from "./crud";

defineOptions({
  name: componentName
});

const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions
});

// 页面打开后获取列表数据
onMounted(async () => {
  crudExpose.doRefresh();
});
</script>
