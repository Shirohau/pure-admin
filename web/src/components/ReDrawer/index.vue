<script setup lang="ts">
import { Close } from "@element-plus/icons-vue";
import { closeDrawer, drawerStore } from "./index";
import type { DrawerOptions } from "./type";

function handleClose(
  options: DrawerOptions,
  index: number,
  args = { command: "close" }
) {
  closeDrawer(options, index, args);
  options.close && options.close({ options, index });
}
</script>

<template>
  <el-drawer
    v-for="(options, index) in drawerStore"
    :key="index"
    v-bind="options"
    v-model="options.visible"
    class="pure-drawer"
    @closed="handleClose(options, index)"
  >
    <!-- header -->
    <template
      v-if="options?.headerRenderer"
      #header="{ close, titleId, titleClass }"
    >
      <component :is="options.headerRenderer({ close, titleId, titleClass })" />
    </template>
    <!-- body -->
    <div
      v-if="!options?.withHeader && options?.showClose !== false"
      class="pure-drawer__close"
      @click="handleClose(options, index)"
    >
      <el-icon><Close /></el-icon>
    </div>
    <component
      v-bind="options?.props"
      :is="options.contentRenderer({ options, index })"
      @close="args => handleClose(options, index, args)"
    />
  </el-drawer>
</template>

<style lang="scss">
.pure-drawer {
  & > .el-drawer__body {
    position: relative;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;

    & > * {
      flex: 1;
      min-height: 0;
    }

    .pure-drawer__close {
      position: absolute;
      top: 12px;
      right: 12px;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      font-size: 16px;
      color: var(--el-text-color-placeholder);
      cursor: pointer;
      border-radius: 50%;
      transition:
        color 0.2s,
        background-color 0.2s;

      &:hover {
        color: var(--el-color-primary);
        background-color: var(--el-fill-color-light);
      }
    }
  }
}
</style>
