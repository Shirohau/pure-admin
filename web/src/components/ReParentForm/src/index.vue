<template>
  <div :class="{ 're-parent-form': true, 'is-single-group': singleGroup }">
    <fs-form ref="formRef" v-bind="formOptions" />
  </div>
</template>
<script lang="ts" setup>
import { computed, ref, watch } from "vue";
import { cloneDeep } from "lodash-es";
import { useFs, useFsRef } from "@fast-crud/fast-crud";
import type {
  CreateCrudOptions,
  DynamicallyCrudOptions
} from "@fast-crud/fast-crud";

type FormProps = {
  /**
   * crudOptions创建方法
   */
  createCrudOptions?: CreateCrudOptions;
  /**
   * crudOptions 覆盖配置（由 useFs 内部自动合并）
   */
  crudOptionsOverride?: DynamicallyCrudOptions;
  /**
   * 自定义上下文，透传给内部 createCrudOptions（如 isNested 标记）
   */
  context?: Record<string, any>;
  /**
   * api 接口对象（需提供 GetObj 方法），与 id 搭配使用：
   * 由组件内部按 id 查询详情并填充表单，替代调用方 asyncCompute 异步监听
   */
  api?: any;
  /**
   * 要查询的记录主键；变化时组件内部调用 api.GetObj(id) 填充表单
   */
  id?: any;
};

const props = withDefaults(defineProps<FormProps>(), {
  createCrudOptions: undefined,
  crudOptionsOverride: undefined,
  context: () => ({}),
  api: undefined,
  id: undefined
});

const formRef = ref();

const { crudRef, crudBinding, crudExpose } = useFsRef();
useFs({
  crudRef,
  crudBinding,
  crudExpose,
  createCrudOptions: props.createCrudOptions as any,
  crudOptionsOverride: props.crudOptionsOverride as any,
  context: props.context
});

// 2. 过滤列：移除 $checked 行选择列、非 base 分组字段与 form.show=false 的字段
//    统一基于 crudBinding.value.viewForm 的 columns（框架已保证字段 component.disabled=true、mode=view）
//    字段隐藏由调用方 crudOptionsOverride 控制（如母工单只读表单配置 columns.material.form.show=false）；
//    在副本上操作避免污染 viewForm 配置；无分组配置时保留全部字段
const filteredColumns = computed(() => {
  const source = (crudBinding.value.viewForm as any)?.columns;
  if (!source) {
    return {};
  }
  const columns = { ...source };
  // 默认保留范围：base 分组的字段列表；无分组配置时不限制
  const groups = (crudBinding.value.viewForm as any)?.group?.groups as
    | Record<string, { columns?: string[]; [key: string]: any }>
    | undefined;
  const baseColumns: string[] | undefined = groups?.base?.columns;

  for (const key of Object.keys(columns)) {
    // override 合并后的原始列配置（form.show 不进入 viewForm.columns，需从 columns 读取）
    const columnConfig = (crudBinding.value.columns as any)?.[key];
    const inRemove =
      key === "$checked" ||
      (baseColumns && !baseColumns.includes(key)) ||
      // crudOptionsOverride 中配置 form.show=false 的字段（如只读表单隐藏 material 子表）
      columnConfig?.form?.show === false ||
      (columns[key] as any)?.show === false;
    if (inRemove) {
      delete columns[key];
      continue;
    }
  }
  return columns;
});

// 3. 过滤分组：清理已被移除的字段并删除空分组，避免出现空页签
const filteredGroups = computed(() => {
  const groups = (crudBinding.value.viewForm as any)?.group?.groups as
    | Record<string, { columns?: string[]; [key: string]: any }>
    | undefined;
  if (!groups) {
    return undefined;
  }
  const result: Record<string, any> = {};
  for (const [groupKey, groupItem] of Object.entries(groups)) {
    const remaining = (groupItem?.columns ?? []).filter(
      (key: string) => filteredColumns.value[key] != null
    );
    if (remaining.length > 0) {
      result[groupKey] = { ...groupItem, columns: remaining };
    }
  }
  return result;
});

// 仅剩一个分组时隐藏分组页签栏（分组配置保留，保证字段顺序与原始表单一致）
const singleGroup = computed(
  () =>
    filteredGroups.value != null &&
    Object.keys(filteredGroups.value).length === 1
);

// 4. 构建表单配置：直接基于 crudBinding.value.viewForm 展开（fs-form 可接受的完整配置），
//    不再经过 crudOptions 重新构建，保证字段禁用（component.disabled=true）与只读模式（mode=view）
const formOptions = computed(() => {
  const viewForm = crudBinding.value.viewForm;
  if (!viewForm) {
    return {};
  }
  return {
    ...viewForm,
    columns: filteredColumns.value,
    group: filteredGroups.value
      ? {
          ...(viewForm as any)?.group,
          groups: filteredGroups.value
        }
      : undefined
  };
});

// 5. 内部查询模式：id 变化时调用 api.GetObj(id) 查询详情并填充表单
//    （调用方只需传入 id 与 api；id 为空时清空表单，避免残留上一行数据）
watch(
  () => props.id,
  async val => {
    let data: any = {};
    if (val && props.api?.GetObj) {
      try {
        const res = (await props.api.GetObj(val)) as ApiResponse;
        data = res?.data;
      } catch (e) {
        console.error("[ReParentForm] 按 id 查询详情失败:", e);
      }
    }
    setFormData(data);
  },
  { immediate: true }
);

/**
 * 写入表单值（mergeForm: false 先清空再写入，避免残留上一次行数据）
 */
function setFormData(data: any) {
  formRef.value?.setFormData(cloneDeep(data || {}), { mergeForm: false });
}
</script>
<style lang="scss" scoped>
.re-parent-form.is-single-group {
  :deep(.el-tabs__header) {
    display: none;
  }
}
</style>
