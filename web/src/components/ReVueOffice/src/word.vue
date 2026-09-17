<template>
  <vue-office-docx
    :src="props.path"
    style="height: 90vh"
    @rendered="rendered"
  />
</template>

<script lang="ts" setup>
//引入VueOfficeDocx组件
import VueOfficeDocx from "@vue-office/docx/lib/v3/vue-office-docx.mjs";
//引入相关样式
import "@vue-office/docx/lib/v3/index.css";

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
