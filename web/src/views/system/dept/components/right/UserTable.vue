<template>
  <!-- 部门下的员工成员表：复用用户管理页的 UserTable，作为子表嵌入 -->
  <user-table
    ref="userTableRef"
    class="h-[calc(100vh-250px)]"
    :isSubTable="true"
  />
</template>

<script lang="ts" setup>
/**
 * 部门成员表：复用用户管理模块的 UserTable 组件。
 * 挂载时把自身实例注册给 useDeptTree 的 deptUserTableRef，
 * 由树节点点击、成员范围切换驱动查询条件设置与刷新。
 */
import UserTable from "@/views/system/user/index.vue";
import { onMounted, ref } from "vue";

import { useDeptTree } from "../../hooks/useDeptTree";
const { deptUserTableRef, resetCrudOptions } = useDeptTree();

/** 子表组件实例引用（挂载后同步给 hooks） */
const userTableRef = ref();

onMounted(() => {
  // 注册子表实例（供树联动刷新），并按部门场景裁剪列配置
  deptUserTableRef.value = userTableRef.value;
  resetCrudOptions();
});
</script>
