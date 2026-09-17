<template>
  <el-card class="h-full">
    <el-calendar>
      <template #date-cell="{ data }">
        <div
          class="date-cell"
          :class="{
            'is-weekend': isWeekend(data.date),
            'is-holiday': isHoliday(data.date),
            'is-workday': isWorkday(data.date)
          }"
          @click="handleClick(data.date)"
        >
          <!-- 公历 -->
          <span class="solar">{{ data.date.getDate() }}</span>
          <!-- 农历 -->
          <span class="lunar">{{ getLunar(data.date) }}</span>
          <!-- 节假日标签 -->
          <div v-if="isHoliday(data.date)" class="tag holiday">休</div>
          <div v-if="isWorkday(data.date)" class="tag workday">班</div>
        </div>
      </template>
    </el-calendar>
  </el-card>
</template>

<script setup lang="ts">
import { SolarDay } from "tyme4ts";
import { useSelectDay } from "../useSelectDay";
const selectDay = useSelectDay();
// 点击事件
const handleClick = (date: Date) => {
  selectDay.day.value = date;
};

// 初始化公历日
const initSolar = (date: Date) => {
  return SolarDay.fromYmd(
    date.getFullYear(),
    date.getMonth() + 1,
    date.getDate()
  );
};

// 判断是否为周末（周六、周日）
const isWeekend = (date: Date) => {
  const solarDay = initSolar(date);
  const week = solarDay.getWeek().getName();
  return week == "六" || week == "日";
};

// 判断是否为节假日（非调休）
const isHoliday = (date: Date) => {
  const solarDay = initSolar(date);
  const festival = solarDay.getLegalHoliday();

  // 检查是否为配置中的节假日或有法定节假日
  return festival && !festival.isWork();
};

// 判断是否为调休上班日
const isWorkday = (date: Date) => {
  const solarDay = initSolar(date);
  const festival = solarDay.getLegalHoliday();
  // 如果是工作日或者配置中指定的工作日
  return festival && festival.isWork();
};

// 农历显示内容
const getLunar = (date: Date) => {
  const solarDay = initSolar(date);

  // 1. 公历现代节日
  const solarFestival = solarDay.getFestival();
  if (solarFestival) {
    return solarFestival.getName();
  }

  // 2. 农历传统节日
  const lunar = solarDay.getLunarDay();
  const lunarFestival = lunar.getFestival();
  if (lunarFestival) {
    return lunarFestival.getName();
  }

  // 3. 节气
  const term = solarDay.getTerm();
  const termIndex = solarDay.getTermDay(); //公历日位于节气的第几天
  if (termIndex.getDayIndex() == 0) {
    return term;
  }
  // 4. 默认返回农历日期
  const lunarMonth = lunar.getLunarMonth(); // 回 "正月", "二月", ..., "腊月"
  const lunarDay = lunar.getName(); // 返回 "初一", "初二", ..., "十五", "十六"...

  // 如果是农历初一，显示月份名称（如“正月”）
  if (lunarDay === "初一") {
    return lunarMonth.getName(); // 如："八月"
  }

  // 其他日子显示“初X”、“十五”、“十六”等
  return lunarDay;
};
</script>

<style scoped>
:deep(.el-calendar__body) {
  padding: 0;
}

:deep(.el-calendar) {
  --el-calendar-cell-width: 75px !important;
}

.date-cell {
  position: relative;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 4px;
  cursor: pointer;
}

.solar {
  font-size: 24px;
  font-weight: bold;
}

.lunar {
  margin-top: 2px;
  font-size: 12px;
}

/* 标签样式 */
.tag {
  position: absolute;
  top: 2px;
  right: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  font-size: 10px;
  line-height: 1;
  color: white;
  border-radius: 50%;
}

.tag.holiday {
  background-color: #e74c3c;
}

.tag.workday {
  background-color: #409eff;
}

/* 今日高亮 */
:deep(.el-calendar-table td.is-today) {
  color: #fff !important;
  background-color: #409eff !important;
}

/* 跨月日期：整体透明度 50% */
.el-calendar-table td.prev .date-cell,
.el-calendar-table td.next .date-cell {
  opacity: 0.5;
}

/* 当前月的周末：仅周六日，且非节假日、非调班日 */
.date-cell.is-weekend:not(.is-holiday, .is-workday, .is-other-month) .solar {
  color: #e74c3c;
}

/* 法定节假日：背景、公历数字、标签统一红色风格 */
.date-cell.is-holiday {
  color: #e74c3c; /* 整体设为红色 */
  background-color: #fdf0f6;
}

/* 调班日背景色 */
.date-cell.is-workday {
  background-color: #f5f7fa;
}
</style>
