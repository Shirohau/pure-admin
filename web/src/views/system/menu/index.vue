<template>
  <div>
    <el-splitter>
      <el-splitter-panel :size="280">
        <MenuTree />
      </el-splitter-panel>
      <el-splitter-panel :min="200">
        <MenuPermission />
      </el-splitter-panel>
    </el-splitter>
  </div>
</template>

<script setup lang="ts">
// 菜单
const componentName = "MenuView";
defineOptions({
  name: componentName
});
import MenuTree from "./components/left/MenuTree.vue";
import MenuPermission from "./components/right/MenuPermission.vue";
</script>
