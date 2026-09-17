import { computed, ref, watch } from "vue";
import { api } from "../api";
import XEUtils from "xe-utils";
import type { FilterNodeMethodFunction } from "element-plus";
// import { useMerge } from "@fast-crud/fast-crud";
// const { merge } = useMerge();

const treeProps = {
  children: "children",
  label: "title"
};

/**
 * @description 树形数据源
 */
const treeData = ref();
const menuTreeRef = ref();
const menuButtonExpose = ref();
const menuFieldExpose = ref();
const menuRightActive = ref("button");
/**
 * 设置数据
 */
const setTreeData = async () => {
  const { data } = await api.GetList({ paginate: false });
  treeData.value = XEUtils.toArrayTree(data, { parentKey: "parentId" });
};

/**
 * 选中的树节点
 */
const selectTreeNode = ref();
// 是否有选中菜单
const isSelected = computed(() => selectTreeNode.value != null);
/**
 * 树节点单击事件
 * - 设置选中菜单
 * @param node
 */
const treeNodeClick = async (node: any) => {
  const { data } = await api.GetObj(node.id);
  selectTreeNode.value = data;
  refreshRightTable(menuRightActive.value);
};

/**
 * 刷新右侧表
 */
const refreshRightTable = (name: string) => {
  if (!isSelected.value) return;
  if (name == "button") {
    // 刷新菜单按钮表
    menuButtonExpose.value.setSearchFormData({
      form: { menu: selectTreeNode.value?.id }
    });
    menuButtonExpose.value.doRefresh();
  } else if (name == "field") {
    // 刷新菜单字段表
    menuFieldExpose.value.setSearchFormData({
      form: { menu: selectTreeNode.value?.id }
    });
    menuFieldExpose.value.doRefresh();
  }
};

/**
 * 树节点移动
 */
const moveTreeNode = (direction: string) => {
  api.MoveObj(selectTreeNode.value.id, direction).then(async () => {
    await setTreeData();
  });
};

/**
 * 筛选内容
 */
const filterText = ref("");
watch(filterText, val => {
  menuTreeRef.value!.filter(val);
});

/**
 * @description 树形数据源定义
 */
interface Tree {
  [key: string]: any;
}
/**
 * @description 树形数据筛选
 */
const treeFilter: FilterNodeMethodFunction = (value: string, data: Tree) => {
  if (!value) return true;
  return data.title.includes(value);
};

/**
 * 默认展开的菜单
 */
// 内部用 Set 管理（去重、高效）
const expandedKeySet = ref(new Set<string>());

// 对外提供响应式数组（供 Tree 组件使用）
const treeExpandedKeys = computed(() => Array.from(expandedKeySet.value));
/**
 * 设置默认展开的菜单
 * @param node
 * @param mode
 */
const setTreeExpandedKeys = (node: Tree, mode: string) => {
  switch (mode) {
    case "expand":
      // 打开
      expandedKeySet.value.add(node.id);
      break;
    case "collapse":
      // 收起
      expandedKeySet.value.delete(node.id);
      break;
  }
};
export function useMenuTree() {
  return {
    treeData,
    menuTreeRef,
    menuButtonExpose,
    menuFieldExpose,
    menuRightActive,
    refreshRightTable,
    treeProps,
    setTreeData,
    isSelected,
    treeNodeClick,
    selectTreeNode,
    filterText,
    treeFilter,
    moveTreeNode,
    treeExpandedKeys,
    setTreeExpandedKeys
  };
}
