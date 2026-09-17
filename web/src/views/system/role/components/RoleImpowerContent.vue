<template>
  <div v-loading="loading" class="role-impower-content">
    <div class="impower-header">
      <span>当前授权角色：</span>
      <el-tag type="primary">{{ roleInfo?.name }}</el-tag>
      <span>已授权人员：</span>
      <el-button :icon="UserFilled" @click="dialogVisible = true">{{
        roleInfo?.users.length
      }}</el-button>
    </div>
    <!-- 角色详情加载完成后再渲染授权面板，保证子组件挂载时 roleInfo.menus 已就绪 -->
    <el-splitter v-if="!loading" class="impower-splitter">
      <!-- 左侧：菜单树 -->
      <el-splitter-panel :size="200" :min="100">
        <AuthorizedMenu />
      </el-splitter-panel>
      <!-- 右侧：按钮/字段授权 -->
      <el-splitter-panel :min="200">
        <div class="impower-right">
          <el-segmented
            v-model="activeName"
            :options="tabOptions"
            class="impower-tabs__header"
            @change="getPermission"
          />
          <div v-show="activeName === 'button'" class="impower-pane">
            <AuthorizedMenuButton />
          </div>
          <div v-show="activeName === 'field'" class="impower-pane">
            <AuthorizedMenuField />
          </div>
        </div>
      </el-splitter-panel>
    </el-splitter>

    <AuthorizedUser v-model:dialogVisible="dialogVisible" />
  </div>
</template>

<script setup lang="ts">
/**
 * 角色授权内容组件
 * @description 角色授权抽屉的主体内容：
 * 1. 作为授权上下文的提供者，为子组件提供每实例状态（provide/inject，多抽屉并存互不干扰）
 * 2. 布局：头部（角色名 + 已授权人员入口）+ 左侧菜单树 + 右侧按钮/字段授权页签
 * 3. props 接收 roleId，打开时异步加载角色详情，并展示加载态
 * 说明：左右两栏使用 el-splitter 分割面板，面板内部 flex:1 撑满高度，
 * 表格面板独立滚动、分页器固定在面板底部，不受组件内部高度链影响
 */
import { computed, onMounted, provide, ref } from "vue";
import { UserFilled } from "@element-plus/icons-vue";
import AuthorizedUser from "./AuthorizedUser.vue";
import AuthorizedMenu from "./AuthorizedMenu.vue";
import AuthorizedMenuButton from "./AuthorizedMenuButton.vue";
import AuthorizedMenuField from "./AuthorizedMenuField.vue";

import { impowerKey, useImpower } from "../hooks/useImpower";

const props = defineProps<{ roleId: number }>();

// 创建当前抽屉实例的授权上下文，并向子组件提供（多抽屉并存互不干扰）
const impower = useImpower();
provide(impowerKey, impower);
const { roleInfo, activeName, getPermission, menuInfo } = impower;

// 右侧页签配置：未选中菜单前，按钮/字段授权页签均禁用
const tabOptions = computed(() => [
  { label: "授权按钮", value: "button", disabled: menuInfo.id == undefined },
  { label: "授权字段", value: "field", disabled: menuInfo.id == undefined }
]);

const dialogVisible = ref(false);
const loading = ref(true);

// 加载角色详情，数据就绪后再展示内容，保证子组件能拿到 menus/users 等数据
onMounted(async () => {
  await impower.loadRole(props.roleId);
  loading.value = false;
});
</script>

<style scoped lang="scss">
.role-impower-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.impower-header {
  display: flex;
  gap: 8px;
  align-items: center;
  padding-bottom: 12px;
}

/* 主体：左右两栏使用分割面板布局，面板高度由 flex 计算，需自身成为 flex 容器子元素才能撑满 */
.impower-splitter {
  flex: 1;
  height: 100%;
  min-height: 0;

  :deep(.el-splitter-panel) {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    overflow: hidden;
  }
}

.impower-right {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  padding-left: 8px;
  overflow: hidden;

  .impower-tabs__header {
    flex: none;
    margin-bottom: 10px;
  }

  .impower-pane {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }
}
</style>
