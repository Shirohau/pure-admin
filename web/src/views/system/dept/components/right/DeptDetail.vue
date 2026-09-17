<template>
  <!-- 部门详情卡片：基本信息 + 成员范围切换 + 下级组织数 + 负责人信息 -->
  <el-card shadow="never" class="h-25">
    <div v-if="selectTreeNode">
      <div class="mb-2">
        <el-text tag="b">{{ selectTreeNode?.name }} ：</el-text>
        <el-text tag="b">{{ selectTreeNode?.code }}</el-text>
      </div>
      <!-- 成员范围切换 + 下级组织数 + 负责人信息，合并为一行展示 -->
      <div class="flex flex-wrap gap-6">
        <!-- 成员范围切换：直属成员（仅本部门）/ 隶属成员（含全部下级部门） -->
        <el-switch
          v-model="switchVlue"
          inline-prompt
          style="

--el-switch-on-color: #13ce66; --el-switch-off-color: #409eff"
          active-text="直属成员"
          inactive-text="隶属成员"
          @change="switchChange"
        />

        <!-- 分隔线 -->
        <div class="border-l border-gray-300 mx-2" />
        <!-- 下级组织数：由后端详情接口返回的 descendant_count -->
        <div class="flex items-center gap-1">
          <el-text>下级组织数：</el-text>
          <el-text>{{ selectTreeNode?.descendant_count }}</el-text>
        </div>
        <!-- 分隔线 -->
        <div class="border-l border-gray-300 mx-2" />
        <!-- 负责人信息：来自详情接口的 owner 用户对象（无负责人时显示 -） -->
        <div class="flex items-center gap-1">
          <el-text type="info">负责人：</el-text>
          <el-text>{{ selectTreeNode?.owner?.name || "-" }}</el-text>
        </div>
        <!-- 分隔线 -->
        <div class="border-l border-gray-300 mx-2" />
        <div class="flex items-center gap-1">
          <el-text type="info">联系电话：</el-text>
          <el-text>{{ selectTreeNode?.owner?.mobile || "-" }}</el-text>
        </div>
        <!-- 分隔线 -->
        <div class="border-l border-gray-300 mx-2" />
        <div class="flex items-center gap-1">
          <el-text type="info">邮箱：</el-text>
          <el-text>{{ selectTreeNode?.owner?.email || "-" }}</el-text>
        </div>
      </div>
    </div>
    <el-text v-else type="info">部门详情</el-text>
  </el-card>
  <!-- 员工成员表：随选中部门联动刷新 -->
  <UserTable />
</template>

<script setup lang="ts">
/**
 * 部门详情：展示当前选中部门的基本信息、下级组织数、负责人联系方式；
 * 并提供"直属成员/隶属成员"切换，控制下方员工表的查询范围。
 */
import UserTable from "./UserTable.vue";
import { useDeptTree } from "../../hooks/useDeptTree";
import { ref } from "vue";
const { selectTreeNode, refreshUserTable } = useDeptTree();
/** 成员范围开关：true=直属成员（仅当前部门），false=隶属成员（含全部下级部门） */
const switchVlue = ref(true);
/** 成员范围切换：按范围重新设置员工表查询条件并刷新 */
const switchChange = (val: boolean | string | number) => {
  if (val) {
    // 直属成员：按当前部门精确过滤
    refreshUserTable({
      dept: selectTreeNode.value?.id
    });
  } else {
    // 隶属成员：按当前部门及其全部后代部门过滤（children_ids 由后端详情接口一次性返回）
    refreshUserTable({
      dept__id__in: selectTreeNode.value?.children_ids.join(",")
    });
  }
};
</script>
