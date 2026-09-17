<template>
  <div class="re-aside-table">
    <fs-crud ref="crudRef" v-bind="crudBinding">
      <template #header-bottom>
        <FilterTags v-if="FilterTags" />
      </template>
      <template #actionbar-right>
        <slot name="actionbar-right" />
      </template>
      <template #pagination-left>
        <el-tooltip v-if="showBatchDelete" content="批量删除">
          <fs-button
            type="danger"
            icon="ion:trash-outline"
            :disabled="selectedData.length === 0"
            @click="handleBatchDelete"
          />
        </el-tooltip>
      </template>
    </fs-crud>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted } from "vue";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import { useFieldPerms, loadPagePerms } from "@/utils/permissions";
import type { ReAsideTableProps } from "../types";

const props = withDefaults(defineProps<ReAsideTableProps>(), {
  createCrudOptions: undefined,
  componentName: undefined,
  crudOptionsOverride: undefined,
  autoSearch: true,
  context: () => ({}),
  showBatchDelete: undefined
});
/** 初始化完成（权限加载与 crudBinding 重建后）事件：需注入外部查询条件的父级在此回调刷新 */
const emit = defineEmits<{
  inited: [];
}>();
const componentName = props.componentName;
const { crudRef, crudBinding, crudExpose } = useFsRef();
//同步初始化crud
// 注意：useFs 会展开 createCrudOptions 的返回值，crud 配置可能未返回 hasPerms 等字段
const {
  hasPerms,
  selectedData = [],
  handleBatchDelete,
  crudOptions,
  FilterTags,
  resetCrudOptions
} = useFs({
  crudRef,
  crudBinding,
  crudExpose,
  context: props.context,
  // 使用any类型绕过严格类型检查，因为在运行时这应该是安全的
  createCrudOptions: props.createCrudOptions as any,
  crudOptionsOverride: props.crudOptionsOverride as any
});
// 兼容 crud 配置返回的权限值：可能为 ref、boolean 或 undefined
const toBool = (v: any) =>
  v == null ? false : typeof v === "object" ? Boolean(v.value) : Boolean(v);

// 批量删除按钮显示：showBatchDelete 传入时强制生效（true 显示 / false 隐藏）；
// 未传入时自动判断：$checked 列显示 且 有 batchDestroy 权限 且 提供了删除处理函数
// （crud 配置未返回 hasPerms/handleBatchDelete 时自动隐藏，如穿梭框场景）
const showBatchDelete = computed(() => {
  if (props.showBatchDelete != null) {
    return props.showBatchDelete;
  }
  return (
    Boolean(handleBatchDelete) &&
    toBool(hasPerms?.batchDestroy) &&
    (crudOptions.columns as any)?.$checked?.column?.show
  );
});

// 暴露 selectedData 与 crudExpose 供外部获取
defineExpose({ selectedData, crudExpose });
// 页面打开后加载子表按钮权限并刷新
onMounted(async () => {
  // 加载子表组件的按钮权限（嵌套场景下子表权限尚未加载）
  if (componentName) {
    await loadPagePerms(componentName);
  }
  // 应用字段权限
  const newOptions = useFieldPerms(componentName, crudOptions);
  //重置crudBinding
  resetCrudOptions(newOptions);
  if (props.autoSearch) {
    crudExpose.doRefresh();
  }
  // 通知父级初始化完成：resetCrudOptions 重建 crudBinding 会重置 search.validatedForm，
  // 依赖外部同步上下文注入查询条件的父级需在此事件后重新注入并刷新
  emit("inited");
});
</script>

<style lang="scss" scoped>
.re-aside-table {
  display: flex;
  flex-direction: column;
  height: 100%;

  :deep(.fs-crud) {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
  }
}
</style>
