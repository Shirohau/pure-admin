// index.js or any suitable file name

// 导入各个组件
import CrontabMin from "./02_min.vue";
import CrontabHour from "./03_hour.vue";
import CrontabDay from "./04_day.vue";
import CrontabMonth from "./05_month.vue";
import CrontabWeek from "./06_week.vue";
import CrontabExpression from "./08_expression.vue";
import CrontabResult from "./09_result.vue";
import CrontabNormal from "./10_normal.vue";

// 将所有导入的组件通过一个对象导出
export {
  CrontabMin,
  CrontabHour,
  CrontabDay,
  CrontabMonth,
  CrontabWeek,
  CrontabExpression,
  CrontabResult,
  CrontabNormal
};
