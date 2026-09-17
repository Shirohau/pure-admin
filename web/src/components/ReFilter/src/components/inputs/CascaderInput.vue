<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { FilterInputExpose, FilterResult, InputProps } from "../../types";

defineOptions({ name: "CascaderInput" });

/**
 * 级联输入组件（内嵌树形控件方案）
 * 不用 el-cascader：其浮层会遮住"重置/确定"按钮；内嵌树固定高度内滚动，搜索过滤只隐藏不匹配节点
 * - 多选勾选：check-strictly（勾选父节点只提交父路径，与原 el-cascader 语义一致）
 */
const props = defineProps<InputProps>();

const emit = defineEmits<{
  filter: [result: FilterResult];
  reset: [];
}>();

/** 树实例引用（获取选中节点/清空勾选/过滤） */
const treeRef = ref<any>(null);

/** 搜索关键词（按 label 过滤节点） */
const keyword = ref("");

/** 已勾选节点 key 列表（check 事件同步，用于清空按钮禁用态） */
const checkedKeys = ref<any[]>([]);

/** 值字段名（提交路径构建用，兼容 cascaderProps 自定义映射） */
const valueKey = computed(
  () => (props.cascaderProps?.value ?? "value") as string
);

/**
 * 节点唯一 key 字段名（注入到树数据）
 * 省市县数据第二层"市辖区"重名（value 用 name 时）：按 value 作 key 会互相覆盖、路径反查串位，
 * 因此按"根到当前节点的完整 value 路径"注入唯一 key，node-key 与 pathMap 均以它为准
 */
const NODE_KEY = "__nodeKey";

/** label 字段名（过滤与标签路径用，兼容 cascaderProps 自定义映射） */
const labelKey = computed(
  () => (props.cascaderProps?.label ?? "label") as string
);

/** 树节点字段映射（children 字段名兼容 cascaderProps 自定义映射） */
const treeProps = computed(() => ({
  label: labelKey.value,
  children: (props.cascaderProps?.children ?? "children") as string
}));

/** 树数据：注入唯一节点 key（映射新对象，不污染原数据），禁用时递归标记 disabled */
const treeData = computed(() => {
  const injectKey = (items: any[], valuePath: any[]): any[] =>
    items.map(item => ({
      ...item,
      [NODE_KEY]: [...valuePath, item[valueKey.value]].join("/"),
      ...(item.children
        ? {
            children: injectKey(item.children, [
              ...valuePath,
              item[valueKey.value]
            ])
          }
        : {})
    }));
  let list = injectKey(props.selectList ?? [], []);
  if (props.disabled) {
    const markDisabled = (items: any[]): any[] =>
      items.map(item => ({
        ...item,
        disabled: true,
        ...(item.children ? { children: markDisabled(item.children) } : {})
      }));
    list = markDisabled(list);
  }
  return list;
});

/**
 * 节点唯一 key → { valuePath, labelPath } 路径映射
 * el-tree getCheckedNodes() 返回数据对象（无 parent 链可用），按唯一 key 预建到根节点的完整路径，提交时反查
 */
const pathMap = computed(() => {
  const map = new Map<string, { valuePath: any[]; labelPath: any[] }>();
  const walk = (items: any[], valuePath: any[], labelPath: any[]) => {
    for (const item of items ?? []) {
      const value = item[valueKey.value];
      const label = item[labelKey.value];
      map.set(item[NODE_KEY], {
        valuePath: [...valuePath, value],
        labelPath: [...labelPath, label]
      });
      const children = item[treeProps.value.children];
      if (Array.isArray(children)) {
        walk(children, [...valuePath, value], [...labelPath, label]);
      }
    }
  };
  walk(treeData.value, [], []);
  return map;
});

/** 搜索词变化：过滤树节点（filter 只隐藏不匹配节点，已勾选状态保留） */
watch(keyword, val => {
  treeRef.value?.filter(val);
});

/** 重置内部状态（不触发事件，供 FilterArea 调用） */
const reset = () => {
  keyword.value = "";
  checkedKeys.value = [];
  treeRef.value?.setCheckedKeys([]);
};

/** 勾选变化：同步已勾选 key 列表（清空按钮禁用态） */
const handleCheck = (_data: any, info: any) => {
  checkedKeys.value = info.checkedKeys;
};

/** 清空所有已选值 */
const clearAll = () => {
  reset();
};

/** 节点过滤：label 包含关键词的节点显示（祖先链自动保留可见） */
const filterNode = (value: string, data: any) => {
  if (!value) return true;
  return String(data[labelKey.value]).includes(value);
};

/**
 * 提交筛选：lookup 按第一个选中节点路径提交；默认所有路径提交（路径间 | 分隔、层级间 , 分隔，
 * 如 "天津市,市辖区,和平区|北京市,市辖区,东城区"），并附带 label 路径列表（仅用于标签展示）
 */
const submit = () => {
  const checkedNodes = treeRef.value?.getCheckedNodes() || [];
  if (!checkedNodes.length) {
    emit("reset");
    return;
  }

  // 兼容两种返回值：数据对象（本版本 getCheckedNodes 返回 child.data）或 Node 实例（新版本），
  // 再按节点 value 反查 pathMap 得到根到该节点的 value/label 路径
  const paths: any[][] = [];
  const labels2D: any[][] = [];
  for (const node of checkedNodes) {
    const data = node?.data ?? node;
    const info = pathMap.value.get(data[NODE_KEY]);
    if (!info) continue;
    paths.push(info.valuePath);
    labels2D.push(info.labelPath);
  }

  if (!paths.length) {
    emit("reset");
    return;
  }

  // lookup 场景：单路径提交
  if (props.lookup) {
    emit("filter", {
      cond1Operator: props.lookup,
      cond1Value: paths[0].join(",")
    });
    return;
  }

  emit("filter", {
    cond1Operator: "",
    cond1Value: paths.map(p => p.join(",")).join("|"),
    cascaderLabels: labels2D
  });
};

defineExpose<FilterInputExpose>({ reset, submit });
</script>

<template>
  <div class="tree-cascader">
    <!-- 搜索行：搜索框 + 清空按钮（无选中时清空按钮禁用） -->
    <div class="search-row">
      <el-input
        v-model="keyword"
        size="small"
        placeholder="搜索选项"
        clearable
        :disabled="disabled"
      />
      <el-button
        link
        type="danger"
        size="small"
        :disabled="disabled || !checkedKeys.length"
        @click="clearAll"
        >清空</el-button
      >
    </div>

    <!-- 树形控件：固定高度内滚动，多选勾选，内嵌面板不悬浮、不遮挡操作按钮 -->
    <div class="tree-body">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :node-key="NODE_KEY"
        show-checkbox
        check-strictly
        render-after-expand
        :expand-on-click-node="false"
        :check-on-click-node="true"
        :filter-node-method="filterNode"
        @check="handleCheck"
      />
    </div>
  </div>
</template>

<style scoped>
/* 整体纵向布局：搜索行 → 树 */
.tree-cascader {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
/* 搜索行：搜索框占满剩余宽度，清空按钮居右 */
.search-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.search-row .el-input {
  flex: 1;
}
/* 树容器：固定高度内滚动（与 SelectInput 表格风格一致） */
.tree-body {
  height: 200px;
  overflow-y: auto;
  padding: 4px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}
/* 已勾选节点文字主色（check-strictly 下无半选态，checked 即选中） */
.tree-cascader
  :deep(
    .el-tree-node.is-checked > .el-tree-node__content .el-tree-node__label
  ) {
  color: #409eff;
}
</style>
