<template>
  <el-tabs v-model="activeName">
    <el-tab-pane lazy label="SPC实验项目" name="first">
      <iframe
        class="h-[80vh] w-screen"
        src="https://pbi.yhkj.com/Reports/powerbi/001?rs:embed=true&token=obZ6p14gETOKjX1wV49sqifpgUCA1wMAOIBBb62Rz3wExRb0ir7C1u4tcnGxLLyz"
      />
    </el-tab-pane>
    <el-tab-pane lazy label="某消费品运营数据监控" name="second">
      <iframe
        class="h-[80vh] w-screen"
        src="https://pbi.yhkj.com/Reports/powerbi/002?rs:embed=true&token=3KwiYpFHOgoq%2FTfkGkZ9g6DbVsg%2B6OhyjB1tlwtz2Jnqbt%2BdrQCq51TQzOOAsEng"
      />
    </el-tab-pane>
    <el-tab-pane lazy label="客户帕累托(ABC)分析" name="third">
      <iframe
        class="h-[80vh] w-screen"
        src="https://pbi.yhkj.com/Reports/powerbi/003?rs:embed=true&token=3KwiYpFHOgoq%2FTfkGkZ9g8fs72Uq93Dz%2FWboBrxxmErA6LitOBqu5Uun%2F2slNdob"
      />
    </el-tab-pane>
  </el-tabs>
</template>
<script lang="ts" setup>
defineOptions({
  name: "PBIRS"
});

import { ref } from "vue";
const activeName = ref("first");
</script>
