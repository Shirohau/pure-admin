<template>
  <div>
    <view-word v-if="view_type === 'word'" :path="props.modelValue" />
    <view-excel v-else-if="view_type === 'excel'" :path="props.modelValue" />
    <view-pdf v-else-if="view_type === 'pdf'" :path="props.modelValue" />
    <view-image v-else-if="view_type === 'image'" :path="props.modelValue" />
    <div v-else class="unsupported-file">
      不支持的文件类型：{{ props.file_suffix }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, defineAsyncComponent, PropType } from "vue";

// 懒加载子组件
const ViewWord = defineAsyncComponent(() => import("./word.vue"));
const ViewExcel = defineAsyncComponent(() => import("./excel.vue"));
const ViewPdf = defineAsyncComponent(() => import("./pdf.vue"));
const ViewImage = defineAsyncComponent(() => import("./image.vue"));

// 文件后缀映射表（常量）
const EXTENSION_MAP: Record<string, string> = {
  docx: "word",
  doc: "word",
  xlsx: "excel",
  xls: "excel",
  pdf: "pdf",
  jpg: "image",
  jpeg: "image",
  png: "image",
  gif: "image",
  bmp: "image"
};

// Props 定义（类型安全）
const props = defineProps({
  drawer_show: {
    type: Boolean,
    default: false
  },
  file_suffix: {
    type: String as PropType<string>,
    default: ""
  },
  file_name: {
    type: String as PropType<string>,
    default: ""
  },
  modelValue: {
    type: [String, ArrayBuffer] as PropType<string | ArrayBuffer>,
    default: ""
  }
});

// 计算当前应展示的视图类型
const view_type = computed(() => {
  const suffix = (props.file_suffix || "").trim().toLowerCase();
  if (!suffix) return "unknown";
  return EXTENSION_MAP[suffix] || "unknown";
});
</script>

<style scoped>
.unsupported-file {
  padding: 20px;
  color: #999;
  text-align: center;
}
</style>
