<template>
  <div class="flex flex-col h-[calc(100vh-150px)]">
    <el-input
      v-model="filterText"
      class="mb-2"
      placeholder="筛选菜单"
      clearable
      :prefix-icon="useRenderIcon('ep:search')"
    />

    <el-scrollbar class="flex-1">
      <el-tree
        ref="treeRef"
        node-key="id"
        highlight-current
        :data="treeData"
        :props="treeProps"
        :indent="treeIndent"
        :expand-on-click-node="false"
        :filter-node-method="treeFilter"
        :default-expanded-keys="treeExpandedKeys"
        @node-click="treeNodeClick"
        @node-expand="setTreeExpandedKeys($event, 'expand')"
        @node-collapse="setTreeExpandedKeys($event, 'collapse')"
      >
        <template v-slot:default="{ node, data }">
          <element-tree-line
            :node="node"
            :showLabelLine="false"
            :indent="treeIndent"
          >
            <template v-slot:node-label>
              <div class="flex gap-1 items-center">
                <component :is="useRenderIcon(toRaw(data.icon ?? undefined))" />
                <el-text v-if="data.showLink">{{ node.label }}</el-text>
                <el-text v-else type="warning">{{ node.label }}</el-text>
                <component
                  :is="useRenderIcon(toRaw(data.extraIcon ?? undefined))"
                />
              </div>
            </template>
          </element-tree-line>
        </template>
      </el-tree>
    </el-scrollbar>
    <MenuButton />
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref, toRaw } from "vue";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import MenuButton from "./MenuButton.vue";
import type { TreeInstance } from "element-plus";

const treeIndent = 30;

import { useMenuTree } from "../../hooks/useMenuTree";
const {
  menuTreeRef,
  filterText,
  treeData,
  setTreeData,
  treeProps,
  treeFilter,
  treeExpandedKeys,
  treeNodeClick,
  setTreeExpandedKeys
} = useMenuTree();

const treeRef = ref<TreeInstance>();

onMounted(() => {
  menuTreeRef.value = treeRef.value;
  setTreeData();
});
</script>
