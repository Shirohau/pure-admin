<template>
  <vue-office-excel
    :src="props.path"
    style="height: 90vh"
    @rendered="rendered"
  />
</template>

<script lang="ts" setup>
//引入VueOfficeExcel组件
import VueOfficeExcel from "@vue-office/excel/lib/v3/vue-office-excel.mjs";
//引入相关样式
import "@vue-office/excel/lib/v3/index.css";

const props = defineProps({
  path: {
    type: String as PropType<string>,
    default: ""
  }
});
const rendered = () => {
  console.log("渲染完成");
};
</script>
