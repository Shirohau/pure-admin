<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "../api";
import { debounce } from "lodash-es";
import XEUtils from "xe-utils";

// 声明 props 类型
export interface FormProps {
  formInline?: {
    tags: string;
    search: string;
  };
}

// 声明 props 默认值
// 推荐阅读：https://cn.vuejs.org/guide/typescript/composition-api.html#typing-component-props
const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({ tags: "", search: "" })
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
const tableData = ref({});
// 数据加载
const fetchData = async () => {
  const params = {
    search: newFormInline.value.search
  };
  const { data } = await api.GetApiList(params);
  tableData.value = XEUtils.groupBy(data, "tags");
};

// 初始化数据
onMounted(async () => {
  fetchData();
});
</script>

<template>
  <div>
    <el-input
      v-model="newFormInline.search"
      class="pl-5 pr-5"
      clearable
      placeholder="请输入关键词"
      @input="debouncedSearch"
      @clear="onSearchClear"
    >
      <template #append>
        <el-button type="primary" icon="Search" @click="fetchData" />
      </template>
    </el-input>
    <el-scrollbar height="400px" class="p-5 overflow-y-auto">
      <el-collapse v-model="newFormInline.tags" accordion class="h-full">
        <el-collapse-item
          v-for="(item, key) in tableData"
          :key="key"
          :title="key"
          :name="key"
        >
          <template #title="{ isActive }">
            <div :class="['title-wrapper', { 'is-active': isActive }]">
              {{ key }}
            </div>
          </template>
          <el-table row-key="model" border highlight-current-row :data="item">
            <el-table-column type="index" width="50" />
            <el-table-column prop="summary" width="100" label="概要" />
            <el-table-column prop="function" width="100" label="函数名" />
            <el-table-column prop="method" width="80" label="请求方法" />
            <el-table-column
              prop="path"
              label="API地址"
              width="300"
              show-overflow-tooltip
            />
            <el-table-column
              prop="description"
              label="详细说明"
              show-overflow-tooltip
            />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-scrollbar>
  </div>
</template>
<style scoped>
.title-wrapper {
  display: flex;
  gap: 4px;
  align-items: center;
}

.title-wrapper.is-active {
  color: var(--el-color-primary);
}
</style>
