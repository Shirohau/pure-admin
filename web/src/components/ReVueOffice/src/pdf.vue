<template>
  <vue-office-pdf :src="props.path" style="height: 90vh" @rendered="rendered" />
</template>

<script lang="ts" setup>
//引入VueOfficePdf组件
import VueOfficePdf from "@vue-office/pdf/lib/v3/vue-office-pdf.mjs";

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
