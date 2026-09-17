<template>
  <el-row :gutter="20">
    <el-col :span="14">
      <calendar-card />
    </el-col>
    <el-col :span="10">
      <lunar-card />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import calendarCard from "./components/CalendarCard.vue";
import lunarCard from "./components/LunarCard.vue";
</script>
