<template>
  <div class="flex justify-between">
    <!-- <el-button text type="primary" @click="importMenu"> 导入 </el-button> -->

    <!-- <el-button text type="primary" @click="exportMenu"> 导出 </el-button> -->

    <el-button text type="primary" @click="openFormDialog('add')">
      新增
    </el-button>

    <el-button
      text
      type="primary"
      :disabled="!isSelected"
      @click="openFormDialog('edit')"
    >
      编辑
    </el-button>

    <el-button
      text
      type="primary"
      :disabled="!isSelected"
      @click="moveTreeNode('up')"
    >
      上移
    </el-button>

    <el-button
      text
      type="primary"
      :disabled="!isSelected"
      @click="moveTreeNode('down')"
    >
      下移
    </el-button>

    <el-button text type="primary" :disabled="!isSelected" @click="delMenu">
      删除
    </el-button>
  </div>
  <MenuForm />
</template>

<script setup lang="ts">
import MenuForm from "./MenuForm.vue";
import { useMenuForm } from "../../hooks/useMenuForm";
import { useMenuTree } from "../../hooks/useMenuTree";
const { openFormDialog, delMenu, importMenu, exportMenu } = useMenuForm();
const { isSelected, moveTreeNode } = useMenuTree();
</script>
