<template>
  <div class="page">
    <!-- 黄历 -->
    <el-card class="solar">
      <!-- 顶部：公历 -->
      <div class="solar-date">
        <el-text class="text-gray">{{ getSolar }} {{ getWeekDay }}</el-text>
      </div>

      <!-- 农历标题（红色） -->
      <div class="lunar-title">
        <el-text class="text-red text-xl font-bold">{{ getLunarMD }}</el-text>
      </div>

      <!-- 干支纪年 -->
      <div class="gan-zhi">
        <el-text class="text-sm text-gray-500">{{ getGanZhi }}</el-text>
      </div>

      <!-- 宜 忌 -->
      <div class="recommendations">
        <div class="item">
          <span class="label blue">宜</span>
          <span class="content">{{ getGoodThings }}</span>
        </div>
        <div class="item">
          <span class="label red">忌</span>
          <span class="content">{{ getBadThings }}</span>
        </div>
      </div>
    </el-card>

    <!-- 鸡汤 -->
    <el-card class="soup">
      <div v-if="hitokotoLoading">
        <el-text class="text-gray">加载中...</el-text>
      </div>
      <template v-else>
        <div>
          <el-text>{{ hitokoto }}</el-text>
        </div>
        <div>
          <el-text>—— {{ from }}</el-text>
        </div>
      </template>
      <div v-if="hitokotoError" class="retry-wrap">
        <el-button link type="primary" size="small" @click="fetchHitokoto">
          重新获取
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useSelectDay } from "../useSelectDay";
import { SolarDay } from "tyme4ts";
import { http } from "@/utils/http";
const selectDay = useSelectDay();

// 获取当前选中日期的公历
const getSolar = computed(() => {
  const date = selectDay.day.value || new Date();
  return SolarDay.fromYmd(
    date.getFullYear(),
    date.getMonth() + 1,
    date.getDate()
  );
});

// 获取星期
const getWeekDay = computed(() => {
  return `星期${getSolar.value.getWeek()}`;
});

// 获取农历
const getLunar = computed(() => {
  return getSolar.value.getLunarDay();
});

// 获取农历月日
const getLunarMD = computed(() => {
  const lunar = getLunar.value;
  return `${lunar.getLunarMonth().getName()}${lunar.getName()}`;
});
// 获取干支纪年
const getGanZhi = computed(() => {
  const lunar = getLunar.value;
  const scd = lunar.getSixtyCycleDay();
  return scd;
});
// 获取宜：嫁娶, 祭祀, 理发
const getGoodThings = computed(() => {
  const lunar = getLunar.value;
  return lunar.getRecommends().toLocaleString();
});
// 获取忌：破土, 出行, 栽种
const getBadThings = computed(() => {
  const lunar = getLunar.value;
  return lunar.getAvoids().toLocaleString();
});

// 响应式数据：鸡汤内容
const hitokoto = ref<string>();
const from = ref<string>("");
const hitokotoLoading = ref(false);
const hitokotoError = ref(false);
// 获取一言;
const fetchHitokoto = async () => {
  hitokotoLoading.value = true;
  hitokotoError.value = false;
  try {
    const { data } = (await http.get(
      "https://v1.hitokoto.cn/",
      {},
      {
        skipToken: true,
        skipResponse: true
      }
    )) as any;
    hitokoto.value = data.hitokoto;
    from.value = data.from || "未知来源";
  } catch {
    hitokotoError.value = true;
    hitokoto.value = "生活不止眼前的苟且，还有诗和远方。";
    from.value = "默认文案";
  } finally {
    hitokotoLoading.value = false;
  }
};

onMounted(() => {
  fetchHitokoto();
});
</script>

<style scoped lang="scss">
.page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;

  .solar,
  .soup {
    flex: 1;
  }
}

.solar {
  padding: 20px;

  .solar-date {
    margin-bottom: 8px;
    text-align: center;
  }

  .lunar-title {
    margin: 10px 0;
    text-align: center;
  }

  .gan-zhi {
    margin: 8px 0;
    text-align: center;
  }

  .recommendations {
    margin: 16px 0;

    .item {
      display: flex;
      align-items: center;
      min-height: 24px; // 确保至少有高度
      margin-bottom: 8px;

      .label {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        margin-right: 8px;
        font-size: 12px;
        color: white;
        border-radius: 50%;

        &.blue {
          background-color: #409eff;
        }

        &.red {
          background-color: #f56c6c;
        }
      }

      .content {
        display: -webkit-box;
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 14px;
        line-height: 1.4;
        color: #666;
        word-break: break-all; // 支持中文断行
        -webkit-box-orient: vertical;
      }
    }
  }

  .info-table {
    width: 100%;
    margin-top: 16px;

    table {
      width: 100%;
      font-size: 12px;
      border-collapse: collapse;

      td {
        padding: 8px;
        vertical-align: top;
        text-align: center;
        border: 1px solid #e4e7ed;
      }

      .table-header {
        font-weight: bold;
        color: #909399;
        background-color: #f5f7fa;
      }

      .table-label {
        font-weight: bold;
        color: #909399;
        text-align: center;
        background-color: #f5f7fa;
      }

      .table-content {
        padding: 4px;
        line-height: 1.4;
      }
    }
  }
}

.text-red {
  color: #f56c6c;
}

.text-gray {
  color: #666;
}

.text-xl {
  font-size: 1.5rem;
}

.font-bold {
  font-weight: bold;
}

.soup {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;

  .retry-wrap {
    margin-top: 8px;
  }
}
</style>
