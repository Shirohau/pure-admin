<template>
  <div>
    <el-tabs v-model="activeName" class="h-full">
      <el-tab-pane label="定时" name="clocked" class="h-full">
        <Clocked class="h-full" />
      </el-tab-pane>
      <el-tab-pane label="间隔" name="interval" class="h-full">
        <Interval class="h-full" />
      </el-tab-pane>
      <el-tab-pane label="周期" name="crontab" class="h-full">
        <Crontab class="h-full" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script lang="ts" setup name="schedule">
import { ref } from "vue";

import Clocked from "./clocked/index.vue";
import Interval from "./interval/index.vue";
import Crontab from "./crontab/index.vue";
const activeName = ref("clocked");
defineOptions({
  name: "ScheduleView1"
});
</script>
