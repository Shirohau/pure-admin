/**
 * 部门树 hooks：管理左侧部门树的数据加载、选中联动、展开/收起、过滤与节点移动。
 *
 * 职责划分：
 *  - 树数据加载与默认选中（setTreeData）
 *  - 树节点点击选中 + 右侧详情/员工表联动（treeNodeClick / refreshUserTable）
 *  - 树节点上移/下移（moveTreeNode）
 *  - 树节点关键字过滤（filterText / treeFilter）与展开状态管理（expandedKeySet）
 */
import { computed, ref, watch } from "vue";
import { api } from "../api";
import XEUtils from "xe-utils";
import type { FilterNodeMethodFunction } from "element-plus";
import { useMerge } from "@fast-crud/fast-crud";
const { merge } = useMerge();
/** 部门状态筛选条件（null=全部，true=启用，false=停用），由页面上方状态筛选切换 */
const dept_status = ref(null);
/** el-tree 属性配置：子节点字段为 children，节点显示文本字段为 name */
const treeProps = {
  children: "children",
  label: "name"
};
/**
 * @description 树形数据源
 */
const treeData = ref();
/** 部门树 el-tree 组件实例引用（用于选中、过滤、展开控制） */
const deptTreeRef = ref();
/** 右侧员工表（fast-crud）组件实例引用，用于联动刷新 */
const deptUserTableRef = ref();
/**
 * 加载部门树数据并刷新左侧树组件
 *
 * 流程：
 *  1. 请求列表接口（关闭分页，仅取树渲染所需字段 id/name/path/parent_path/status）；
 *  2. 数据非空时自动选中第一行并触发树节点点击事件，保证右侧详情初始有内容；
 *  3. 通过 XEUtils.toArrayTree 按 path/parent_path 将扁平列表还原为树形结构。
 *
 * 说明：path/parent_path 为 treebeard 物化路径（如 "0001"、"00010001"），
 * 前缀关系即父子关系，因此无需递归即可还原树结构。
 */
const setTreeData = async () => {
  const { data } = await api.GetList({
    paginate: false,
    status: dept_status.value,
    query: "{id,name,path,parent_path,status}"
  });
  if (data.length > 0) {
    deptTreeRef.value.setCurrentKey(data[0]); // 选中第一行
    treeNodeClick(data[0]); // 激活点击事件
    expandedKeySet.value.add(data[0].id); // 默认展开第一行
  }
  treeData.value = XEUtils.toArrayTree(data, {
    key: "path",
    parentKey: "parent_path"
  });
};

/**
 * 选中的树节点
 */
const selectTreeNode = ref();
// 是否有选中部门
const isSelected = computed(() => selectTreeNode.value != null);

/**
 * 重置用户表的 crudOptions
 */
const resetCrudOptions = () => {
  const options = {
    columns: {
      username: {
        column: {
          show: false
        }
      },
      timezone: {
        column: {
          show: false
        }
      },
      avatar_path: {
        column: {
          show: false
        }
      },
      dept: {
        search: {
          show: false
        },
        form: {
          component: {
            disabled: true
          }
        }
      }
    }
  };
  const onNewOptions = merge(deptUserTableRef.value.crudOptions, options);
  deptUserTableRef.value.resetCrudOptions(onNewOptions);
};
/**
 * 树节点单击事件
 * - 请求部门详情并记录为选中部门（selectTreeNode）
 * - 携带部门ID刷新右侧员工表，实现"详情 + 成员"联动展示
 * @param node 树节点数据（须含 id 字段）
 */
const treeNodeClick = async (node: any) => {
  const { data } = await api.GetObj(node.id);
  selectTreeNode.value = data;
  refreshUserTable({
    dept: selectTreeNode.value?.id
  });
};

/**
 * 刷新右侧员工表
 * - 把当前选中部门设置为员工表 dept 字段的默认表单值（新增员工时自动归属该部门）
 * - 通过 setSearchFormData 设置查询条件并触发 doRefresh 重新拉取员工列表
 * @param form 查询条件对象（如 { dept: 部门ID }）
 */
const refreshUserTable = form => {
  // 设置部门默认值
  const options = {
    columns: {
      dept: {
        form: {
          value: selectTreeNode.value.id
        }
      }
    }
  };
  const onNewOptions = merge(deptUserTableRef.value.crudOptions, options);
  deptUserTableRef.value.resetCrudOptions(onNewOptions);
  // 刷新表

  deptUserTableRef.value.setSearchFormData({ form });
  deptUserTableRef.value.doRefresh();
};

/**
 * 树节点上移/下移（与兄弟节点交换顺序）
 * @param direction "up" 上移 / "down" 下移，边界情况（首节点上移、末节点下移）由后端忽略处理
 */
const moveTreeNode = (direction: string) => {
  api.MoveObj(selectTreeNode.value.id, direction).then(async () => {
    await setTreeData();
  });
};

/** 树节点关键字过滤内容（由搜索输入框双向绑定） */
const filterText = ref("");
// 输入变化时实时调用 el-tree 的 filter 方法进行节点过滤
watch(filterText, val => {
  deptTreeRef.value!.filter(val);
});

/**
 * @description 树形数据源定义
 */
interface Tree {
  [key: string]: any;
}
/**
 * el-tree 过滤回调：节点名称包含关键字即保留
 * @param value 过滤关键字
 * @param data 当前节点数据
 * @returns true 显示该节点，false 隐藏
 */
const treeFilter: FilterNodeMethodFunction = (value: string, data: Tree) => {
  if (!value) return true;
  return data.name.includes(value);
};

/**
 * 默认展开的部门
 */
// 内部用 Set 管理（去重、高效）
const expandedKeySet = ref(new Set<string>());

// 对外提供响应式数组（供 Tree 组件使用）
const treeExpandedKeys = computed(() => Array.from(expandedKeySet.value));
/**
 * 设置默认展开的部门
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
/**
 * 部门树 hooks 统一出口：返回全部状态与操作方法供页面组件使用
 */
export function useDeptTree() {
  return {
    dept_status,
    treeData,
    deptTreeRef,
    deptUserTableRef,
    resetCrudOptions,
    treeProps,
    setTreeData,
    isSelected,
    treeNodeClick,
    selectTreeNode,
    filterText,
    treeFilter,
    moveTreeNode,
    treeExpandedKeys,
    setTreeExpandedKeys,
    refreshUserTable
  };
}
