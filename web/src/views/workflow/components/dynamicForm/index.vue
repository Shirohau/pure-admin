<!--
  审批流程设计器 - 动态表单设计（第二步）
  来源：AntFlow-Designer（https://gitee.com/ldhnet/AntFlow-Designer）
  迁移适配：
  1. import 路径由 @/utils/workflow/、@/store/modules/workflow 调整为 @/views/workflow/... 下对应路径
  2. v-form-designer 组件由项目 main.ts 全局注册（VForm3 UMD），无需额外引入
  作用：基于 VForm3 表单设计器（v-form-designer）可视化设计审批表单，
       并通过 MutationObserver 监听设计器变化，将字段列表实时同步到 Pinia store
       （供条件节点配置时选择字段），发布时通过 getData 输出表单 JSON。
-->
<template>
  <div class="main-container">
    <div id="designer-id" class="lf-form-container">
      <!-- 审批流暂未启用 VForm3 设计器（designer.umd.js 会导致构建报错），功能开发时再放开 -->
      <!-- <v-form-designer ref="formDesign"></v-form-designer> -->
    </div>
    <!-- <button @click="submitForm">ok</button> -->
  </div>
</template>

<script setup>
import { ref, onUnmounted, onMounted, watch } from "vue";
import { isObjectChanged } from "@/views/workflow/utils/workflow/commonUtils";
import { useWorkflowStore } from "@/views/workflow/store/workflow.js";

/** 全局状态：存储表单字段列表，供条件节点配置使用 */
let store = useWorkflowStore();

/**
 * 父级传入的表单 JSON 字符串（VForm3 格式，如流程已有表单则回显）
 */
let props = defineProps({
  lfFormData: {
    type: String,
    default: null
  }
});

const formDesign = ref(null);

/** 上一次获取的字段列表（用于变更检测） */
let formField = {};
//let formImportObj = "{\"widgetList\":[...]}"; // 可直接用 JSON 字符串初始化表单的示例（已注释）

/**
 * MutationObserver：监听设计器 DOM 变化（新增/删除/修改字段），
 * 变化后将最新字段列表同步到 store，供条件节点配置引用
 */
const observer = new MutationObserver(() => {
  // VForm3 设计器暂未启用，实例为空时跳过字段同步
  if (!formDesign.value) return;
  const returnFiled = formDesign.value.getFormFieldJson();
  if (isObjectChanged(formField, returnFiled)) {
    formField = returnFiled;
    store.setLowCodeFormField(formField);
  }
});

onMounted(() => {
  const targetNode = document.querySelector("#designer-id");
  const config = { childList: true, subtree: true };
  observer.observe(targetNode, config);
});

/**
 * 监听父级表单数据与设计器实例就绪，回显已有表单
 */
watch(
  () => [props.lfFormData, formDesign.value],
  ([val, designer]) => {
    if (!val || !designer) {
      return;
    }
    try {
      designer.clearDesigner();
      designer.designer.loadFormJson(JSON.parse(val));
    } catch (error) {
      console.error("lfFormData parse error", error);
    }
  },
  { immediate: true }
);

onUnmounted(() => {
  observer.disconnect();
});

/**
 * 获取表单设计 JSON（发布时调用）
 * @returns {Promise<{ formData: Object }>} VForm3 表单 JSON
 */
const getData = () => {
  // VForm3 设计器暂未启用，实例为空时返回空表单数据
  let exportData = formDesign.value?.getFormJson();
  //console.log('exportData=========', JSON.stringify(exportData))
  return new Promise((resolve, reject) => {
    resolve({ formData: exportData });
    reject(new Error("获取表单数据失败"));
  });
};

/**
 * 获取表单字段列表（预留方法）
 * @returns {Promise<{ formData: Array }>} 字段数组
 */
const getFieldList = () => {
  // VForm3 设计器暂未启用，实例为空时返回空字段列表
  let exportField = formDesign.value?.getFormFieldJson();
  return new Promise((resolve, reject) => {
    resolve({ formData: exportField?.formFields });
    reject(new Error("获取表单获取字段失败"));
  });
};

defineExpose({
  getData,
  getFieldList
});
</script>

<style scoped>
body {
  margin: 0;
  /* 如果页面出现垂直滚动条，则加入此行CSS以消除之 */
}

.main-container {
  margin-left: 0px !important;
}

.lf-form-container {
  background: white !important;
  padding: 0px;
  width: 95%;
  left: 0;
  bottom: 0;
  right: 0;
  margin: auto;
}
</style>
