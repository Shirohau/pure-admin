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
import { onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import { useFieldPerms } from "@/utils/auth";

import createCrudOptions, { componentName } from "./crud";

defineOptions({
  name: componentName
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
onMounted(async () => {
  // 设置列权限
  const newOptions = await useFieldPerms(componentName, crudOptions);
  //重置crudBinding
  resetCrudOptions(newOptions);
  crudExpose.doRefresh();
});
</script>
