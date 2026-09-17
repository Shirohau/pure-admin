<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #cell_$expand="scope">
        <el-table :data="scope.row.sessions" stripe style="width: 100%">
          <el-table-column prop="jti" label="jti" />
          <el-table-column prop="created_at" label="创建时间" />
          <el-table-column prop="expires_at" label="过期时间" />
        </el-table>
      </template>
    </fs-crud>
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
  context: {},
  createCrudOptions
});

// 页面打开后获取列表数据
onMounted(async () => {
  crudExpose.doRefresh();
});
</script>
