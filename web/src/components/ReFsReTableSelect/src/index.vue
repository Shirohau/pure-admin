<template>
  <!-- 属性绑定：selectAttrs = 组件默认值 + props.select 全量透传；multiple / popper-class 为核心逻辑由组件固定 -->
  <el-select
    v-bind="selectAttrs"
    v-model="displayValue"
    @clear="onClear"
    @visible-change="onVisibleChange"
  >
    <!-- 选中标签回显：组件不渲染 el-option，通过 #label 插槽按 dict 回填名称；
         单选/多选（含折叠 +N 的 tooltip）均走此插槽，找不到节点时回退展示原始值 -->
    <template #label="{ value, label }">
      {{ getTagLabel(value, label) }}
    </template>

    <!-- 下拉面板：fs-crud 表格内嵌，无需弹窗；v-if 控制首次打开面板才挂载（empty 插槽随组件渲染即存在，不控制会在页面加载时就请求数据） -->
    <template #empty>
      <!-- mousedown.stop：面板内点击不冒泡到 document，避免触发 el-select 的 ClickOutside 关闭 -->
      <div
        v-if="panelOpened"
        class="re-table-select__panel"
        :style="panelStyle"
        @mousedown.stop
      >
        <fs-crud ref="crudRef" v-bind="crudBinding">
          <template #header-bottom>
            <FilterTags v-if="FilterTags" />
          </template>
        </fs-crud>
      </div>
    </template>
  </el-select>
</template>

<script lang="ts" setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch
} from "vue";
import {
  useCompute,
  useFs,
  useFsRef,
  useMerge,
  useUi,
  type CreateCrudOptions,
  type Dict,
  type DynamicallyCrudOptions
} from "@fast-crud/fast-crud";
import { useFieldPerms, loadPagePerms } from "@/utils/permissions";

/**
 * 表格下拉选择组件（交互：表格内嵌在 select 下拉面板，无需弹窗；
 * 内部实现对齐 fast-crud 的 fs-table-select 组件）
 */
type ReFsReTableSelectProps = {
  /** v-model 选中值：单选为值字段（默认 id），多选为数组；valueType=object 时传行对象 */
  modelValue?: any;
  /** 创建 CRUD 选项（必传） */
  createCrudOptions: CreateCrudOptions;
  /** 动态修改 CRUD 选项（选择列配置等组件内置逻辑优先，调用方可覆盖） */
  crudOptionsOverride?: DynamicallyCrudOptions;
  /** 数据字典：按值列表回显名称（createTableSelectDict 生成），未配置时标签回退显示值本身 */
  dict?: Dict;
  /** 是否多选：多选为复选框列，单选为 radio 列 + 点击行选中 */
  multiple?: boolean;
  /** 主键字段，element-plus 必传 */
  rowKey?: string;
  /** 是否跨页保留选中 */
  crossPage?: boolean;
  /** 值类型：value=值字段，object=行对象 */
  valueType?: "value" | "object";
  /** el-select 的配置（除 multiple / popper-class 外全量透传绑定，未配置项使用组件默认值） */
  select?: {
    [key: string]: any;
  };
  /** 组件名称（用于加载按钮/字段权限） */
  componentName?: string;
  /** 透传给 createCrudOptions 的上下文 */
  context?: Record<string, any>;
  /** 是否自动搜索（面板首次打开后加载列表） */
  autoSearch?: boolean;
  /** 面板内表格区域高度 */
  tableHeight?: number;
};

const props = withDefaults(defineProps<ReFsReTableSelectProps>(), {
  modelValue: undefined,
  dict: undefined,
  multiple: false,
  rowKey: "id",
  crossPage: true,
  valueType: "value",
  select: () => ({}),
  componentName: undefined,
  context: () => ({}),
  autoSearch: true,
  tableHeight: 380
});

const emit = defineEmits<{
  "update:modelValue": [value: any];
  change: [value: any];
  "selected-change": [rows: any[]];
}>();

const { ui } = useUi();
const { merge } = useMerge();
const { crudRef, crudBinding, crudExpose } = useFsRef();

// ===== 选中状态 =====
// 选中主键列表（单选仅存一个），驱动表格勾选/radio、标签显示与外部值同步
const selectedRowKeys = ref<any[]>([]);

// 行主键获取：优先 props.rowKey，回退 crud 表格配置，最后回退 id
const getRowKey = () =>
  props.rowKey || crudBinding.value?.table?.rowKey || "id";

// 表格 UI 接口：支持 table v2（crudBinding 尚未构建时回退默认 table）
const getTableCI = () => {
  const tableV2 = ui.tableV2;
  if (crudBinding.value?.table?.tableVersion === "v2" && tableV2) {
    return tableV2;
  }
  return ui.table;
};

// 值 → 主键：valueType=object 时行对象需经 dict 取主键字段，其余类型原样返回
const toKey = (item: any) =>
  props.valueType === "object" && props.dict ? props.dict.getValue(item) : item;

// 外部值 → 选中主键列表（对齐 fs-table-select 的 initSelectedKeys 归一化逻辑）
const toKeys = (val: any): any[] => {
  if (val == null) return [];
  const list = props.multiple ? (Array.isArray(val) ? val : []) : [val];
  return list.map(toKey);
};

// ===== 选中 → 外部值 =====
// 根据选中主键构建要输出的 value 与行数据（对齐 fs-table-select 的 onOk 取值逻辑）
const buildValue = () => {
  let value: any = null;
  let rows: any[] = [];
  if (selectedRowKeys.value.length > 0) {
    value = [...selectedRowKeys.value];
    // 选中行数据：优先从 dict 节点取（含 value/label），未配置 dict 时回退主键
    rows = value.map(key => props.dict?.getNodeByValue(key) ?? key);
    if (props.valueType === "object") {
      value = rows;
    }
    if (!props.multiple) {
      value = value[0];
    }
  } else {
    value = props.multiple ? [] : null;
  }
  return { value, rows };
};

// 同步外部值（v-model + change + selected-change）
const syncModelValue = () => {
  const { value, rows } = buildValue();
  emit("update:modelValue", value);
  emit("change", value);
  emit("selected-change", rows);
};

// dict 补充选中数据：仅当存在未缓存的值时才等待拉取完成。
// 注意：值全部已缓存时 appendByValues 内部走 _registerNotify 分支，返回的
// Promise 要等下一次真正拉取才会 resolve，盲目 await 会让后续逻辑永久挂起
// （表现为取消选中后标签/值不减少）。
const appendDictValues = async (keys: any[]) => {
  if (!props.dict) return;
  const needFetch = keys.filter(key => !props.dict.getNodeByValue(key));
  if (needFetch.length > 0) {
    await props.dict.appendByValues(keys);
  }
};

// 选择列选中回调（buildSelectionCrudOptions 注入）：更新选中集合 → 补充 dict → 同步外部值
const handleSelectedKeysChanged = async (changed: any[]) => {
  selectedRowKeys.value = [...changed];
  // 按值列表拉取选中行数据到 dict，供标签/当前选中展示（未缓存值才发请求）
  await appendDictValues(selectedRowKeys.value);
  syncModelValue();
};

// 同步表格勾选/高亮：按选中主键回显（表格未挂载或当前 UI 不支持时跳过）。
// 注意：setSelectedRows 只增不减（仅执行勾选），需先取消"已勾选但不在选中集合"的行，
// 否则点击标签 × 删除后表格勾选会残留；tableV2 复选框为受控渲染，无需此处理
const syncTableSelection = async () => {
  // 等待表格渲染完成后再回显
  await nextTick();
  await nextTick();
  const tableRef = crudExpose.getBaseTableRef?.();
  const tableCI = getTableCI();
  if (!tableRef || !tableCI.setSelectedRows) return;
  if (props.multiple) {
    // el-table 模式：取消多余勾选（触发的 selection-change 回流后选中集合一致，自然收敛不循环）
    if (tableRef.getSelectionRows && tableRef.toggleRowSelection) {
      const rowKey = getRowKey();
      const selectedSet = new Set(selectedRowKeys.value.map(String));
      for (const row of tableRef.getSelectionRows()) {
        if (!selectedSet.has(String(row[rowKey]))) {
          tableRef.toggleRowSelection(row, false);
        }
      }
    }
  } else if (selectedRowKeys.value.length === 0) {
    // 单选：无选中值时清除当前高亮行
    tableRef.setCurrentRow?.();
  }
  tableCI.setSelectedRows({
    getRowKey,
    multiple: props.multiple,
    tableRef,
    selectedRowKeys
  });
};

/**
 * 合并 crud 配置：
 * 1. 选择列配置（buildSelectionCrudOptions：多选复选框跨页保留 / 单选 radio + 点击行选中）
 * 2. 面板基础覆盖（隐藏操作栏/工具栏/行操作；搜索栏保留，表格每列自带筛选）
 * 3. 刷新后回显选中行（跨页数据加载后同步勾选状态）
 */
const buildMergedCrudOptions = () => {
  const selectionOptions = getTableCI().buildSelectionCrudOptions({
    crossPage: props.crossPage,
    selectOnClickRow: true,
    getRowKey,
    getPageData() {
      return crudBinding.value?.data || [];
    },
    useCompute,
    multiple: props.multiple,
    selectedRowKeys,
    onSelectedKeysChanged: handleSelectedKeysChanged
  });
  const refreshSyncOptions = {
    table: {
      async onRefreshed() {
        // 数据刷新后回显选中勾选/高亮（跨页数据加载后同步勾选状态）
        await syncTableSelection();
      }
    }
  };
  const baseOverride = {
    search: { show: false },
    actionbar: { show: false },
    toolbar: { show: false },
    rowHandle: { show: false }
  };
  return merge(
    refreshSyncOptions,
    selectionOptions,
    baseOverride,
    props.crudOptionsOverride
  );
};

// 同步初始化 crud（选择列等内置配置在 crudOptionsOverride 中合并，调用方配置最后生效）
const { crudOptions, FilterTags, resetCrudOptions } = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context: props.context,
  // 使用 any 类型绕过严格类型检查，运行时安全
  createCrudOptions: props.createCrudOptions as any,
  crudOptionsOverride: buildMergedCrudOptions() as any
});

// el-select 属性：内置默认值在前（原模板硬编码项），props.select 全量展开在后，
// select 中的同名配置可覆盖默认值；multiple / popper-class 属组件核心逻辑，固定在末尾不可覆盖
const selectAttrs = computed(() => ({
  clearable: true,
  fitInputWidth: true,
  collapseTags: true,
  collapseTagsTooltip: true,
  ...(props.select ?? {}),
  multiple: props.multiple,
  popperClass: "re-table-select-popper"
}));

// el-select 绑定值：单选/多选均绑定"值"本身（主键），标签文字由 #label 插槽按 dict 回填
const displayValue = computed({
  get: () => {
    if (props.multiple) {
      const val = Array.isArray(props.modelValue) ? props.modelValue : [];
      return val.map(toKey);
    }
    // 单选空值显示空串，否则按需转主键
    return props.modelValue == null ? "" : toKey(props.modelValue);
  },
  set: val => emit("update:modelValue", val)
});

// 按值查找标签文字：优先 dict 节点，找不到时回退 el-select 提供的 label
const getTagLabel = (value: any, fallback: any) => {
  const node = props.dict?.getNodeByValue(value);
  return node ? props.dict.getLabel(node) : fallback;
};

// 点击清除按钮：清空选中集合，同步清空表格勾选/高亮，并补齐 change/selected-change 事件
const onClear = () => {
  selectedRowKeys.value = [];
  const tableRef = crudExpose.getBaseTableRef?.();
  if (props.multiple) {
    tableRef?.clearSelection?.(); // 多选：清空复选框勾选
  } else {
    tableRef?.setCurrentRow?.(); // 单选：清除当前高亮行
  }
  // el-select 清空时已通过 v-model 触发 update:modelValue，这里补齐 change/selected-change
  const { value, rows } = buildValue();
  emit("change", value);
  emit("selected-change", rows);
};

// ===== 面板防意外关闭 =====
// 面板是否已打开过：首次打开后置 true，fs-crud 才挂载并触发数据请求；
// 打开后保持挂载（对齐 el-select persistent 语义，再次打开不重复请求）
const panelOpened = ref(false);

// 面板容器样式：宽度跟随 el-select 触发元素（配合 fit-input-width 与 popper 等宽），高度由配置决定
const panelStyle = computed(() => ({
  width: "100%",
  height: `${props.tableHeight}px`
}));

// 表格搜索栏字段（下拉/日期/级联等）的弹层默认 teleport 到 body，点击/聚焦弹层会被
// el-select 判定为"外部交互"导致面板关闭。在 document 捕获阶段拦截这些弹层内的
// mousedown 与 focusout 传播（不阻止弹层自身交互），使面板在筛选交互期间保持打开。
const POPUP_SELECTOR = [
  ".el-select-dropdown:not(.re-table-select-popper)",
  ".el-picker__popper",
  ".el-table-filter",
  ".el-cascader__dropdown",
  ".el-dropdown__popper",
  ".el-popover",
  ".el-tooltip__popper"
].join(",");

// 事件目标是否位于表格字段弹层内（自身面板通过 popper-class 排除）
const isPopupTarget = (target: EventTarget | null) => {
  if (!(target instanceof HTMLElement)) return false;
  return Boolean(target.closest(POPUP_SELECTOR));
};

// 拦截弹层内的 mousedown：阻止冒泡到 document，避免 ClickOutside 触发面板关闭
const onDocCaptureMouseDown = (e: MouseEvent) => {
  if (isPopupTarget(e.target)) e.stopPropagation();
};

// 拦截移入弹层的 focusout：阻止 select 失焦，避免失焦路径关闭面板
const onDocCaptureFocusOut = (e: FocusEvent) => {
  if (isPopupTarget(e.relatedTarget)) e.stopPropagation();
};

// 开关 document 捕获阶段的弹层拦截（面板开时注册、关/卸载时移除，多个实例互不干扰）
const toggleDocCaptureListeners = (active: boolean) => {
  const method = active ? "addEventListener" : "removeEventListener";
  document[method]("mousedown", onDocCaptureMouseDown, true);
  document[method]("focusout", onDocCaptureFocusOut, true);
};

// 面板开关：打开时置位 panelOpened（fs-crud 首次挂载并触发数据请求），并注册弹层拦截
const onVisibleChange = (visible: boolean) => {
  if (visible) {
    panelOpened.value = true;
    // 首次打开面板时补充选中值标签名称（dict 已缓存时内部跳过，不发请求）
    appendDictValues(selectedRowKeys.value);
  }
  toggleDocCaptureListeners(visible);
};

// 组件卸载时兜底移除监听
onBeforeUnmount(() => toggleDocCaptureListeners(false));

// ===== 外部值回显 =====
// 外部直接赋值（编辑回显/表单重置）时同步选中集合；与自身 emit 的值一致时跳过，避免循环
watch(
  () => props.modelValue,
  async val => {
    const keys = toKeys(val);
    const cur = selectedRowKeys.value.map(String).join(",");
    const next = keys.map(String).join(",");
    if (cur === next) return;
    selectedRowKeys.value = keys;
    // 编辑回显时立即补充 dict 标签数据，保证标签马上显示名称（仅未缓存值才请求；空值/已缓存时零请求）
    await appendDictValues(keys);
    // 表格已加载时即时同步勾选/高亮（不重新请求数据）
    await syncTableSelection();
  },
  { immediate: true }
);

// ===== 初始化 =====
// 权限是否已应用：fs-crud 在面板首次打开时才挂载（empty 插槽 v-if 控制），
// 需在权限应用且表格挂载后触发首次加载
let permsApplied = false;

const maybeLoad = () => {
  if (props.autoSearch && permsApplied && crudRef.value) {
    crudExpose.doRefresh();
  }
};

// fs-crud 挂载（面板首次打开）后触发首次数据加载（maybeLoad 内部校验挂载与权限状态）
watch(
  () => crudRef.value,
  () => maybeLoad()
);

// 页面打开后加载子表按钮权限并刷新
onMounted(async () => {
  const componentName = props.componentName;
  // 加载组件的按钮权限（嵌套场景下子表权限尚未加载）
  if (componentName) {
    await loadPagePerms(componentName);
  }
  // 应用字段权限
  const newOptions = useFieldPerms(componentName, crudOptions);
  // 重置 crudBinding
  resetCrudOptions(newOptions);
  permsApplied = true;
  maybeLoad();
});

// 暴露选中状态与 crud 实例供外部获取
defineExpose({ selectedRowKeys, crudExpose });
</script>

<!-- popper 面板全局样式：el-select 下拉浮层 teleport 至 body，需非 scoped 生效 -->
<style lang="scss">
.re-table-select-popper {
  // 移除 el-select 下拉列表的默认高度限制与内边距，由面板内容撑开
  .el-select-dropdown__wrap {
    max-height: none;
  }

  .el-select-dropdown__list {
    padding: 0;
  }

  .el-select-dropdown__empty {
    padding: 0;
  }

  // 压缩 fs-crud 容器横向留白，适配窄面板
  .fs-container {
    padding: 0 12px;
  }
}
</style>

<style lang="scss" scoped>
.re-table-select__panel {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;

  :deep(.fs-crud) {
    display: flex;
    flex: 1;
    min-height: 0;
  }
}
</style>
