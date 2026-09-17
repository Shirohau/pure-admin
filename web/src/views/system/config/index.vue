<template>
  <div>
    <div class="mb-5 flex justify-between">
      <el-tag>系统配置:您可以对您的网站进行自定义配置</el-tag>
    </div>
    <el-tabs
      v-model="tabsValue"
      type="card"
      addable
      @tab-remove="removeTab"
      @tab-add="tabsDrawer = true"
    >
      <template #add-icon>
        <el-button
          type="primary"
          :icon="FolderAdd"
          @click="tabsDrawer = true"
        />
      </template>
      <el-tab-pane
        v-for="(item, index) in tabs"
        :key="index"
        :label="item.title"
        :closable="item.closable"
        :name="item.id"
      >
        <formContent :parent="item.id" />
      </el-tab-pane>
    </el-tabs>

    <el-drawer
      v-if="tabsDrawer"
      v-model="tabsDrawer"
      title="添加分组"
      direction="rtl"
      size="30%"
    >
      <addTabs />
    </el-drawer>
    <el-drawer
      v-if="contentDrawer"
      v-model="contentDrawer"
      title="添加内容"
      direction="rtl"
      size="30%"
    >
      <addContent />
    </el-drawer>
  </div>
</template>

<script lang="ts" setup>
//
const componentName = "ConfigView";
defineOptions({
  name: componentName
});
import { FolderAdd } from "@element-plus/icons-vue";
import { onMounted, ref } from "vue";
import addTabs from "./components/addTabs.vue";
import addContent from "./components/addContent.vue";
import formContent from "./components/formContent.vue";
const tabsDrawer = ref(false);
const contentDrawer = ref(false);

import { useConfig } from "./hooks/useConfig";
const { tabs, tabsValue, getTabs, removeTabs } = useConfig();

const removeTab = (targetName: number) => {
  removeTabs(targetName);
};

onMounted(() => {
  getTabs();
});
</script>
