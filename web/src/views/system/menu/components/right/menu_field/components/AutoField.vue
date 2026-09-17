<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";
import { debounce } from "lodash-es";

// 声明 props 类型
export interface FormProps {
  formInline?: {
    name: string;
    model: string;
    search: string;
  };
}

// 声明 props 默认值
// 推荐阅读：https://cn.vuejs.org/guide/typescript/composition-api.html#typing-component-props
const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({ name: "", model: "", search: "" })
});
// vue 规定所有的 prop 都遵循着单向绑定原则，直接修改 prop 时，Vue 会抛出警告。此处的写法仅仅是为了消除警告。
// 因为对一个 reactive 对象执行 ref，返回 Ref 对象的 value 值仍为传入的 reactive 对象，
// 即 newFormInline === props.formInline 为 true，所以此处代码的实际效果，仍是直接修改 props.formInline。
// 但该写法仅适用于 props.formInline 是一个对象类型的情况，原始类型需抛出事件
// 推荐阅读：https://cn.vuejs.org/guide/components/props.html#one-way-data-flow
const newFormInline = ref(props.formInline);

// 防抖
const debouncedSearch = debounce(() => {
  fetchData();
}, 300);
// 清除事件
const onSearchClear = () => {
  newFormInline.value.search = "";
  fetchData();
};

// 表格数据源
const tableData = ref([]);
// 数据加载
const fetchData = async () => {
  const params = {
    search: newFormInline.value.search
  };
  const { data } = await api.GetAppModels(params);
  tableData.value = data;
};
// 表格单选事件
const handleRowClick = (val: FormProps["formInline"]) => {
  newFormInline.value.name = val.name;
  newFormInline.value.model = val.model;
};
// 初始化数据
onMounted(async () => {
  fetchData();
});
</script>

<template>
  <div class="p-2">
    <el-input
      v-model="newFormInline.search"
      style="margin-bottom: 10px"
      clearable
      placeholder="请输入关键词"
      @input="debouncedSearch"
      @clear="onSearchClear"
    >
      <template #append>
        <el-button type="primary" icon="Search" @click="fetchData" />
      </template>
    </el-input>
    <el-table
      row-key="model"
      height="400px"
      border
      highlight-current-row
      :data="tableData"
      @row-click="handleRowClick"
    >
      <el-table-column prop="name" label="模型名称" width="120" />
      <el-table-column prop="model" label="模型表" />
    </el-table>
  </div>
</template>
