<template>
  <div>
    <p>最近20次运行时间：</p>
    <ul class="popup-result-scroll">
      <template v-if="isShow">
        <li v-for="item in resultList" :key="item">{{ item }}</li>
      </template>
      <li v-else>计算结果中...</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { CronExpressionParser } from "cron-parser";
import { ref, watch } from "vue";
import { dayjs } from "element-plus";
const resultList = ref<string[]>([]);
const isShow = ref(false);

const props = defineProps({
  cron: {}
} as any);

watch(
  () => props.cron?.expression,
  newValue => {
    expressionChange(newValue);
  },
  { deep: true, immediate: true }
);

// 表达式值变化时，开始去计算结果
function expressionChange(expression: string) {
  try {
    const dates: string[] = [];
    const interval = CronExpressionParser.parse(expression, {
      tz: "Asia/Shanghai"
    });
    for (let i = 0; i < 20; i++) {
      const date = interval.next(); // 获取下一个运行时间
      const formattedDate = dayjs(date.toDate()).format("YYYY-MM-DD HH:mm");
      dates.push(formattedDate);
    }
    // 更新结果列表
    if (dates.length === 0) {
      resultList.value = ["没有达到条件的结果！"];
    } else {
      resultList.value = dates;
    }
  } catch (err) {
    resultList.value = [
      "无效的 Cron 表达式:",
      (err as Error)?.message || "未知错误"
    ];
  } finally {
    // 显示计算结果
    isShow.value = true;
  }
}
</script>

<style lang="scss" scoped>
.popup-result-scroll {
  height: 164px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 24px;
}
</style>
