<template>
  <div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
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
      <template #form-body-bottom="scope">
        <el-tabs v-model="activeName" class="pb-10">
          <!-- 表达式 -->
          <el-tab-pane label="时间表达式" name="1">
            <CrontabExpression :cron="scope.getFormData()" />
          </el-tab-pane>
          <!-- 常用cron表达式例子 -->
          <el-tab-pane label="常用cron表达式例子" name="2">
            <CrontabNormal />
          </el-tab-pane>
          <!-- 最近20次运行时间 -->
          <el-tab-pane label="预计运行时间" name="3">
            <CrontabResult :cron="scope.getFormData()" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";

import {
  CrontabExpression,
  CrontabResult,
  CrontabNormal
} from "./component/index";
import createCrudOptions, { componentName } from "./crud";

defineOptions({
  name: componentName
});

const activeName = ref("1");

const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
const { hasPerms, selectedData, handleBatchDelete } = useFs({
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
