<template>
  <!-- 部门新增/编辑弹窗 -->
  <el-dialog v-model="formDialogShow">
    <div class="p-4">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <!-- 上级部门：树形选择器，check-strictly 允许选择任意层级（不强制联动父子） -->
        <el-form-item label="上级部门">
          <el-tree-select
            v-model="formData.parentId"
            check-strictly
            clearable
            filterable
            show-checkbox
            node-key="id"
            :data="treeData"
            :props="treeProps"
          />
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="编号" prop="code">
          <el-input v-model="formData.code" />
        </el-form-item>
        <!-- 负责人：fs-table-select 用户表格选择弹窗（参考 user/crud.tsx 中 selectUser 的写法） -->
        <el-form-item label="负责人">
          <fs-table-select
            v-model="formData.owner"
            :multiple="false"
            :create-crud-options="userCrudOptions"
            :crud-options-override="crudOptionsOverride"
            :dict="userDict"
            class="w-full"
            clearable
            placeholder="请选择负责人"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.status" />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button type="primary" @click="formSubmit(formRef)"> 保存 </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
/**
 * 部门新增/编辑表单弹窗
 * - 上级部门：el-tree-select 树形选择，可选中根节点或任意子节点
 * - 负责人：fs-table-select 用户表格选择弹窗（单选），选中值存用户 id，回填标签由 userDict 提供
 * - 状态：el-switch 启停开关
 */
import { ref } from "vue";
import { FormInstance } from "element-plus";
import { dict } from "@fast-crud/fast-crud";
import { useDeptForm } from "../../hooks/useDeptForm";
import { useDeptTree } from "../../hooks/useDeptTree";
import { api as userApi } from "@/views/system/user/api";
import userCrudOptions from "@/views/system/user/crud";

const { formDialogShow, formRules, formData, formSubmit } = useDeptForm();
const { treeData, treeProps } = useDeptTree();

const formRef = ref<FormInstance>();

// 负责人字典回填配置：选中值存用户 id、标签显示用户 name；
// 回填时按 id__in 批量查询用户，避免逐个请求（参考 user/crud.tsx 中 selectUser 的写法）
const userDict = dict({
  value: "id",
  label: "name",
  getNodesByValues: async (values: any[]) => {
    const query = ["id", "name"];
    const params = {
      id__in: values.join(","),
      limit: values.length,
      paginate: false,
      query: `{${query.join(",")}}`
    };
    const { data } = await userApi.GetList(params);
    return data;
  }
});

// 选择弹窗 UI 裁剪：隐藏工具栏/新增/行操作/多选列，弱化为"单选人员选择器"
const crudOptionsOverride = {
  toolbar: { show: false },
  actionbar: { show: false },
  rowHandle: { show: false },
  columns: {
    $checked: {
      column: {
        show: false
      }
    }
  }
};
</script>
