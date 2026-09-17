<template>
  <div>
    <!-- 部门操作按钮组：导入/导出/新增/编辑/上移/下移/删除（编辑、移动、删除依赖选中节点） -->
    <el-button-group class="dept-button">
      <el-button text type="primary" @click="importDept"> 导入 </el-button>

      <el-button text type="primary" @click="exportDept"> 导出 </el-button>

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

      <el-button text type="primary" :disabled="!isSelected" @click="delDept">
        删除
      </el-button>
    </el-button-group>
    <!-- 部门新增/编辑表单弹窗 -->
    <DeptForm />
  </div>
</template>

<script setup lang="ts">
/**
 * 部门操作按钮：提供导入导出、新增编辑、上移下移、删除入口，
 * 具体逻辑统一委托给 useDeptForm / useDeptTree hooks。
 */
import DeptForm from "./DeptForm.vue";
import { useDeptForm } from "../../hooks/useDeptForm";
import { useDeptTree } from "../../hooks/useDeptTree";
const { openFormDialog, delDept, importDept, exportDept } = useDeptForm();
const { isSelected, moveTreeNode } = useDeptTree();
</script>

<style scoped lang="scss">
.dept-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--el-button-size);
  padding-top: 5px;
  border-top: 1px solid var(--pure-border-color);
}
</style>
