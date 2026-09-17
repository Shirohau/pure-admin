<template>
  <el-tabs
    v-model="menuRightActive"
    class="h-full p-2"
    @tab-change="refreshRightTable"
  >
    <el-scrollbar class="h-full">
      <el-tab-pane label="按钮配置" name="button">
        <MenuButton />
      </el-tab-pane>

      <el-tab-pane label="字段配置" name="field">
        <MenuField />
      </el-tab-pane>
    </el-scrollbar>
  </el-tabs>
</template>

<script setup lang="ts">
import MenuButton from "./menu_button/MenuButton.vue";
import MenuField from "./menu_field/MenuField.vue";

import { useMenuTree } from "../../hooks/useMenuTree";
const { menuRightActive, refreshRightTable } = useMenuTree();
</script>
