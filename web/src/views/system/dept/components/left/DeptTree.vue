<template>
  <!-- 部门树面板：状态筛选 + 关键字过滤 + 树形展示 + 操作按钮 -->
  <div class="flex flex-col h-[calc(100vh-150px)]">
    <!-- 状态筛选：全部/启用/禁用，切换后按状态重新加载树 -->
    <el-radio-group v-model="radio" class="mb-2" @change="handleRadioChange">
      <el-radio value="null">全部</el-radio>
      <el-radio value="True">启用</el-radio>
      <el-radio value="False">禁用</el-radio>
    </el-radio-group>
    <!-- 关键字过滤：输入时实时过滤树节点 -->
    <el-input
      v-model="filterText"
      class="mb-2"
      placeholder="筛选部门"
      clearable
      :prefix-icon="useRenderIcon('ep:search')"
    />
    <el-scrollbar class="flex-1">
      <!-- 部门树：点击节点联动右侧详情与成员表；停用部门名称以橙色高亮 -->
      <el-tree
        ref="treeRef"
        node-key="id"
        highlight-current
        :data="treeData"
        :props="treeProps"
        :expand-on-click-node="false"
        :filter-node-method="treeFilter"
        :default-expanded-keys="treeExpandedKeys"
        @node-click="treeNodeClick"
        @node-expand="setTreeExpandedKeys($event, 'expand')"
        @node-collapse="setTreeExpandedKeys($event, 'collapse')"
      >
        <template #default="{ node, data }">
          <span
            :style="{ color: data.status === false ? '#E6A23C' : 'inherit' }"
          >
            <span>{{ node.label }}</span>
          </span>
        </template>
      </el-tree>
    </el-scrollbar>
    <DeptButton />
  </div>
</template>

<script lang="ts" setup>
/**
 * 部门树组件：状态筛选、关键字过滤、树形展示与操作按钮的组合面板。
 * 数据与交互逻辑统一委托给 useDeptTree hooks，本组件仅负责视图绑定。
 */
import { onMounted, ref } from "vue";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import DeptButton from "./DeptButton.vue";
import { useDeptTree } from "../../hooks/useDeptTree";
import type { TreeInstance } from "element-plus";
const {
  dept_status,
  deptTreeRef,
  filterText,
  treeData,
  setTreeData,
  treeProps,
  treeFilter,
  treeExpandedKeys,
  treeNodeClick,
  setTreeExpandedKeys
} = useDeptTree();

/** el-tree 组件实例引用（挂载后同步给 hooks，供其他组件复用） */
const treeRef = ref<TreeInstance>();
/** 状态筛选值："null"=全部 / "True"=启用 / "False"=禁用（字符串值对应后端查询参数） */
const radio = ref("null");
/** 状态筛选切换：更新筛选条件并重新加载树数据 */
const handleRadioChange = (value: string | number | boolean) => {
  dept_status.value = value;
  setTreeData();
};
onMounted(() => {
  // 将树实例注册到 hooks（供树操作/过滤等复用），随后首次加载树数据
  deptTreeRef.value = treeRef.value;
  setTreeData();
});
</script>
