<template>
  <!-- 部门管理页：左右分栏布局，左侧为部门树（筛选/操作），右侧为部门详情 + 成员表 -->
  <div class="page">
    <el-splitter>
      <!-- 左侧面板：部门树（固定最小宽度 200，初始宽度 350） -->
      <el-splitter-panel :min="200" :size="350">
        <div class="panel">
          <DeptTree />
        </div>
      </el-splitter-panel>
      <!-- 右侧面板：部门详情 + 成员表联动 -->
      <el-splitter-panel :min="200">
        <div class="panel">
          <DeptDetail />
        </div>
      </el-splitter-panel>
    </el-splitter>
  </div>
</template>

<script setup lang="ts">
/**
 * 部门管理页面入口
 * 布局：el-splitter 左右分栏，左侧 DeptTree（树 + 操作按钮），右侧 DeptDetail（详情 + 成员表）
 */
// defineOptions 为编译宏，会被提升到模块顶部执行，因此 name 必须使用字符串字面量
// （不能引用 setup 内声明的局部变量，否则触发暂时性死区 ReferenceError）
defineOptions({
  name: "DeptView"
});
import DeptTree from "./components/left/DeptTree.vue";
import DeptDetail from "./components/right/DeptDetail.vue";
</script>

<style scoped lang="scss">
.panel {
  padding: 10px;
}
</style>
