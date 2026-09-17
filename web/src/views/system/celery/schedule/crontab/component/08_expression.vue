<template>
  <div class="popup-result-scroll">
    <el-descriptions direction="vertical" :column="5" size="small" border>
      <el-descriptions-item label="分钟">{{
        props.cron?.minute
      }}</el-descriptions-item>
      <el-descriptions-item label="小时">{{
        props.cron?.hour
      }}</el-descriptions-item>
      <el-descriptions-item label="日期">{{
        props.cron?.day_of_month
      }}</el-descriptions-item>
      <el-descriptions-item label="月份">
        {{ props.cron?.month_of_year }}
      </el-descriptions-item>
      <el-descriptions-item label="星期">
        {{ props.cron?.day_of_week }}
      </el-descriptions-item>
      <el-descriptions-item label="表达式" :span="5">
        {{ props.cron?.expression }}
      </el-descriptions-item>
      <el-descriptions-item label="中文说明" :span="5">
        {{ props.cron?.described }}
      </el-descriptions-item>
      <el-descriptions-item label="英文说明" :span="5">
        {{ props.cron?.human_readable }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>
<script setup lang="ts">
const props = defineProps({
  cron: {}
} as any);
</script>
<style lang="scss" scoped>
.popup-result-scroll {
  height: calc(20em + 21px);
  overflow-y: auto;
  font-size: 12px;
  line-height: 24px;
}
</style>
