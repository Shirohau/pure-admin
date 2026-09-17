<template>
  <el-scrollbar class="flex-1">
    <el-tree
      ref="treeRef"
      node-key="id"
      highlight-current
      default-expand-all
      show-checkbox
      check-strictly
      :data="treeData"
      :props="treeProps"
      :expand-on-click-node="false"
      :check-on-click-leaf="false"
      @check-change="handleMenuChange"
      @node-click="handleMenuClick"
    >
      <template v-slot:default="{ node }">
        <element-tree-line
          :node="node"
          :showLabelLine="false"
          :indent="treeIndent"
        >
          <template v-slot:node-label>
            <span>{{ node.label }}</span>
          </template>
        </element-tree-line>
      </template>
    </el-tree>
  </el-scrollbar>
</template>

<script setup lang="ts">
/**
 * 授权菜单树
 * @description 左侧菜单树：展示系统全部菜单，勾选即调用接口为当前角色添加/移除菜单权限；
 * 点击节点则选中该菜单，联动右侧按钮/字段授权面板刷新对应权限列表
 */
import { nextTick, onMounted, ref } from "vue";
import XEUtils from "xe-utils";
import { api as menu_api } from "@/views/system/menu/api";
import { api as role_api } from "@/views/system/role/api";
import { ElMessage } from "element-plus";

import { useImpowerContext } from "../hooks/useImpower";
const { roleInfo, setRoleInfo, setMenuInfo, getPermission } =
  useImpowerContext();

const treeRef = ref();
const treeData = ref([]);
const treeIndent = 30;
const treeProps = {
  children: "children",
  label: "title"
};
/** 程序化设置勾选标志：初始化回显时避免触发 check-change 导致重复请求授权接口 */
const isSettingChecked = ref(false);
/**
 * 菜单复选框选中
 * @param node：当前节点的 Node 对象
 * @param checked：布尔值，表示当前节点是否被选中
 */
const handleMenuChange = (node: any, checked: boolean) => {
  // 程序化回显勾选不发起请求，仅用户手动勾选才调用授权接口
  if (isSettingChecked.value) return;
  const data = {
    action: checked ? "add" : "remove",
    menu_id: node.id
  };
  role_api.AuthorizedMenu(roleInfo.id, data).then((res: ApiResponse) => {
    setRoleInfo(res.data);
    ElMessage({ message: res.message, type: "success" });
  });
};

/**
 * 设置树形菜单的选中节点
 * @param ids - 需要选中的节点ID数组
 */
const setCheckedKeys = (ids: number[]) => {
  isSettingChecked.value = true;
  treeRef.value!.setCheckedKeys(ids, true);
  // 等本轮 check-change 事件派发完成后恢复，避免误拦截用户后续勾选
  nextTick(() => {
    isSettingChecked.value = false;
  });
};
/**
 * 菜单点击事件
 */
const handleMenuClick = async (node: any) => {
  setMenuInfo(node);
  getPermission();
};
/**
 * 获取树形数据
 */
const setTreeData = async () => {
  const { data }: ApiResponse = await menu_api.GetList({ paginate: false });
  treeData.value = XEUtils.toArrayTree(data, { parentKey: "parentId" });
};
onMounted(async () => {
  // 先等菜单树数据加载完成，再勾选已授权菜单，避免树为空时 setCheckedKeys 失效
  await setTreeData();
  setCheckedKeys(roleInfo.menus);
});
</script>
