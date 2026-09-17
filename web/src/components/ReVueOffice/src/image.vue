<template>
  <el-image :src="props.path" style="height: 90vh" />
</template>

<script lang="ts" setup>
const props = defineProps({
  path: {
    type: String as PropType<string>,
    default: ""
  }
});
</script>
