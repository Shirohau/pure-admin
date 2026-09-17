<template>
  <div>
    <div class="mb-5 flex justify-between items-center">
      <el-tag>消息中心:查看您的系统通知和消息</el-tag>
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
        <el-button
          type="primary"
          :disabled="unreadCount === 0"
          @click="handleMarkAllRead"
        >
          全部标为已读
        </el-button>
      </el-badge>
    </div>
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom> <FilterTags /> </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import { ElMessage } from "element-plus";

import createCrudOptions, { componentName } from "./crud";
import { api } from "./api";

defineOptions({
  name: componentName
});

const unreadCount = ref(0);

const { crudRef, crudBinding, crudExpose } = useFsRef();
// 同步初始化crud
const { crudOptions, resetCrudOptions, FilterTags } = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions
});

// 获取未读消息数量
const fetchUnreadCount = async () => {
  try {
    const res = await api.GetUnreadCount();
    unreadCount.value = res.data?.count ?? 0;
  } catch {
    // ignore
  }
};

// 全部标为已读
const handleMarkAllRead = async () => {
  try {
    await api.MarkRead();
    ElMessage.success("已全部标为已读");
    unreadCount.value = 0;
    crudExpose.doRefresh();
  } catch {
    // ignore
  }
};

// 页面打开后获取列表数据
onMounted(async () => {
  resetCrudOptions(crudOptions);
  crudExpose.doRefresh();
  await fetchUnreadCount();
});
</script>
