<script lang="ts" setup>
// 农历 / 节气 / 节假日 / 宜忌计算库（与 web 端日历首页同款 tyme4ts）
import { SolarDay } from 'tyme4ts'
// SolarDay 类名可直接作类型使用（构造函数为 protected，不能用 InstanceType<typeof SolarDay>）
type SolarDayInstance = SolarDay

defineOptions({
  name: 'Home',
})
definePage({
  // 使用 type: "home" 属性设置首页，其他页面不需要设置，默认为page
  type: 'home',
  style: {
    // 'custom' 表示开启自定义导航栏，默认 'default'
    navigationStyle: 'custom',
    navigationBarTitleText: '首页',
  },
})

/* ==================== 日历状态 ==================== */

// 当前选中的日期（默认今天），用于详情卡片展示
const selectedDate = ref(new Date())
// 当前展示的月份（月历网格按月渲染，切换月份时变化）
const displayYear = ref(selectedDate.value.getFullYear())
const displayMonth = ref(selectedDate.value.getMonth() + 1) // 1~12

// 星期表头：周日开头，与 Date.getDay()（0=周日）对齐
const WEEK_HEADERS = ['日', '一', '二', '三', '四', '五', '六']

/** 判断两个日期是否为同一天（忽略时分秒） */
function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

/** 由 Date 构造 tyme4ts 的公历日对象 */
function toSolarDay(date: Date) {
  return SolarDay.fromYmd(date.getFullYear(), date.getMonth() + 1, date.getDate())
}

/* ==================== 月历网格 ==================== */

// 网格单元格数据结构
interface CalendarCell {
  date: Date // 格子对应日期（含跨月日期）
  solar: number // 公历日数字
  lunarText: string // 农历 / 节日 / 节气 文本
  isCurrentMonth: boolean // 是否属于当前展示月（跨月日期半透明显示）
  isToday: boolean // 是否今天
  isWeekend: boolean // 是否周六/周日
  isHoliday: boolean // 是否法定节假日（显示红色"休"标签）
  isWorkday: boolean // 是否调休上班日（显示蓝色"班"标签）
  isSelected: boolean // 是否当前选中
}

/**
 * 获取格子农历显示文本，优先级（与 web 端 CalendarCard.getLunar 一致）：
 * 1. 公历现代节日（如 元旦、国庆节）
 * 2. 农历传统节日（如 春节、中秋节）
 * 3. 节气（当天为节气首日时显示节气名，如 立春）
 * 4. 默认农历日期：初一显示月名（如 八月），其余显示农历日（如 初五、十五）
 */
function getLunarText(solar: SolarDayInstance) {
  // 1. 公历节日
  const solarFestival = solar.getFestival()
  if (solarFestival) {
    return solarFestival.getName()
  }

  const lunar = solar.getLunarDay()
  // 2. 农历节日
  const lunarFestival = lunar.getFestival()
  if (lunarFestival) {
    return lunarFestival.getName()
  }

  // 3. 节气：getDayIndex() 为 0 表示当天即节气当天
  const term = solar.getTerm()
  if (solar.getTermDay().getDayIndex() === 0) {
    return term.getName()
  }

  // 4. 农历日期：初一显示月名，其余显示农历日
  const lunarDayName = lunar.getName()
  return lunarDayName === '初一' ? lunar.getLunarMonth().getName() : lunarDayName
}

/** 判断是否为法定节假日（含调休规则，非调休上班的节日） */
function isHoliday(solar: SolarDayInstance) {
  const festival = solar.getLegalHoliday()
  return festival !== null && !festival.isWork()
}

/** 判断是否为调休上班日（法定节假日配置为上班的日期） */
function isWorkday(solar: SolarDayInstance) {
  const festival = solar.getLegalHoliday()
  return festival !== null && festival.isWork()
}

// 构建月历网格：固定 6 行 x 7 列 = 42 格，从展示月 1 号所在周的周日开始
const calendarCells = computed<CalendarCell[]>(() => {
  // 展示月 1 号
  const firstOfMonth = new Date(displayYear.value, displayMonth.value - 1, 1)
  // 网格起点：向前推到 1 号所在周的周日
  const start = new Date(firstOfMonth)
  start.setDate(firstOfMonth.getDate() - firstOfMonth.getDay())

  const cells: CalendarCell[] = []
  const today = new Date()
  for (let i = 0; i < 42; i++) {
    const date = new Date(start)
    date.setDate(start.getDate() + i)
    // 每个格子只构造一次公历日对象，供农历文本 / 节假日 / 调休判断复用
    const solar = toSolarDay(date)
    cells.push({
      date,
      solar: date.getDate(),
      lunarText: getLunarText(solar),
      isCurrentMonth: date.getMonth() === displayMonth.value - 1,
      isToday: isSameDay(date, today),
      isWeekend: date.getDay() === 0 || date.getDay() === 6,
      isHoliday: isHoliday(solar),
      isWorkday: isWorkday(solar),
      isSelected: isSameDay(date, selectedDate.value),
    })
  }
  return cells
})

// 将 42 格按 6 行 x 7 列切分，供模板按行渲染并自适应均分行高
const calendarWeeks = computed(() => {
  const weeks: CalendarCell[][] = []
  for (let i = 0; i < calendarCells.value.length; i += 7) {
    weeks.push(calendarCells.value.slice(i, i + 7))
  }
  return weeks
})

/** 点击格子：选中该日期；若点击跨月日期则同时切换展示月份 */
function handleSelect(cell: CalendarCell) {
  selectedDate.value = cell.date
  if (!cell.isCurrentMonth) {
    displayYear.value = cell.date.getFullYear()
    displayMonth.value = cell.date.getMonth() + 1
  }
}

/* ==================== 选中日期详情 ==================== */

// 选中日期的公历 / 农历 / 干支 / 宜忌 详情（参考 web 端 LunarCard）
const detail = computed(() => {
  const date = selectedDate.value
  const solar = toSolarDay(date)
  const lunar = solar.getLunarDay()
  const sixtyCycle = lunar.getSixtyCycleDay()

  // 干支纪年：如 "丙午【马】年 六月 甲子"
  const year = sixtyCycle.getYear().getName()
  const month = sixtyCycle.getMonth().getName()
  const day = sixtyCycle.getName()
  const zodiac = sixtyCycle.getYear().getEarthBranch().getZodiac().getName()

  return {
    // 公历日期，如 "2026年8月2日"
    solarText: `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`,
    // 星期，如 "星期日"
    weekText: `星期${solar.getWeek().getName()}`,
    // 农历月日，如 "六月二十"
    lunarMD: `${lunar.getLunarMonth().getName()}${lunar.getName()}`,
    // 干支纪年 + 生肖
    ganZhi: `${year}【${zodiac}】年 ${month}月 ${day}`,
    // 宜 / 忌（tyme4ts 的 Taboo 列表，toString 即名称）
    recommends: lunar.getRecommends().join('、') || '无',
    avoids: lunar.getAvoids().join('、') || '无',
  }
})

/* ==================== 月份切换 ==================== */

/** 切换上一个月 */
function prevMonth() {
  if (displayMonth.value === 1) {
    displayMonth.value = 12
    displayYear.value -= 1
  }
  else {
    displayMonth.value -= 1
  }
}

/** 切换下一个月 */
function nextMonth() {
  if (displayMonth.value === 12) {
    displayMonth.value = 1
    displayYear.value += 1
  }
  else {
    displayMonth.value += 1
  }
}

/** 回到今天：选中今天并切换展示月份到今天所在月 */
function goToday() {
  selectedDate.value = new Date()
  displayYear.value = selectedDate.value.getFullYear()
  displayMonth.value = selectedDate.value.getMonth() + 1
}

/* ==================== 一言（鸡汤） ==================== */

// 一言内容与来源
const hitokoto = ref('')
const from = ref('')
const hitokotoLoading = ref(false)
const hitokotoError = ref(false)

/**
 * 获取一言（https://v1.hitokoto.cn/）
 * 直接使用 uni.request 而非项目 http 封装：一言接口返回结构并非后端统一
 * { code, data, message } 格式，且无需携带 token 与错误提示
 */
function fetchHitokoto() {
  hitokotoLoading.value = true
  hitokotoError.value = false
  uni.request({
    url: 'https://v1.hitokoto.cn/',
    method: 'GET',
    success: (res) => {
      const data = res.data as Record<string, any>
      hitokoto.value = data.hitokoto || '生活不止眼前的苟且，还有诗和远方。'
      from.value = data.from || '未知来源'
    },
    fail: () => {
      // 接口不可用（如无网络 / 小程序未配置域名白名单）时使用默认文案兜底
      hitokotoError.value = true
      hitokoto.value = '生活不止眼前的苟且，还有诗和远方。'
      from.value = '默认文案'
    },
    complete: () => {
      hitokotoLoading.value = false
    },
  })
}

onMounted(() => {
  fetchHitokoto()
})
</script>

<template>
  <!--
    三区域纵向布局（高度比例 日历 : 详情 : 一言 = 9 : 2 : 1）：
    - 日历占视口可用高度的 3/4，剩余 1/4 中 详情 : 一言 = 2 : 1
      （即 日历 9/12、详情 2/12、一言 1/12）；
    - 本页 navigationStyle 为 custom（自定义导航栏），H5 上 uni-page-head 不渲染、
      页面从视口顶部开始，故高度公式只扣 tabbar 占位(50px)与底部安全区，
      不扣 var(--window-top)（该变量仅对 default 导航栏页面有实际占位）；
    - 根容器与参与 flex 高度分配的元素用 box-border（box-sizing: border-box）；
      且区域容器本身不设 padding——flex-basis 0% 时 padding 会被浏览器从 grow 分配
      空间外扣除并加回最终尺寸，导致比例偏移；区域间隔改用卡片 margin 实现
      （margin 会被 flex 精确扣除，卡片 flex-1 高度 = 区域高度 - margin）；
    - 各区域 min-h-0 + overflow-hidden：内容超高时在区域内压缩/截断，不撑破比例、不互相重叠；
    - 空间紧张时优先保证日历网格完整可交互（网格 6 行均分区域剩余高度，
      公历数字圆点为交互目标保持完整，农历文本行可能被压缩截断）；
    - 详情区域高度有限（约 1/6 屏），采用紧凑排版：行高缩至 16px、
      宜/忌单行截断；一言区域更小（约 1/12 屏），一言文本单行截断、
      来源与「重新获取」入口同行。均不改变任何交互逻辑。
  -->
  <view
    class="box-border flex flex-col bg-[#f6f7fb] pt-safe"
    :style="{
      height: 'calc(100vh - 50px - env(safe-area-inset-bottom))',
    }"
  >
    <!-- ============ 区域一：日历（相对 9 份 = 总高 3/4） ============ -->
    <view class="box-border min-h-0 flex flex-col overflow-hidden" :style="{ flex: 9 }">
      <!-- 月份切换栏 -->
      <view class="flex items-center justify-between bg-white px-4 py-3">
        <view class="flex items-center">
          <!-- 上一个月 -->
          <view class="h-7 w-7 flex items-center justify-center text-xl text-[#666] active:opacity-50" @click="prevMonth">
            ‹
          </view>
          <text class="mx-5 text-base text-[#2a2a2a] font-bold">
            {{ displayYear }}年{{ displayMonth }}月
          </text>
          <!-- 下一个月 -->
          <view class="h-7 w-7 flex items-center justify-center text-xl text-[#666] active:opacity-50" @click="nextMonth">
            ›
          </view>
        </view>
        <!-- 回到今天 -->
        <view class="text-sm text-[#018d71] active:opacity-50" @click="goToday">
          今天
        </view>
      </view>

      <!-- 星期表头：周末红色 -->
      <view class="flex bg-white pb-2">
        <view
          v-for="week in WEEK_HEADERS"
          :key="week"
          class="flex-1 text-center text-xs"
          :class="week === '日' || week === '六' ? 'text-[#e74c3c]' : 'text-[#999]'"
        >
          {{ week }}
        </view>
      </view>

      <!-- 月历网格：6 行 x 7 列，行高随区域剩余高度自适应均分 -->
      <view class="min-h-0 flex flex-1 flex-col bg-white">
        <view
          v-for="(week, weekIndex) in calendarWeeks"
          :key="weekIndex"
          class="min-h-0 flex flex-1 overflow-hidden"
        >
          <view
            v-for="cell in week"
            :key="cell.date.getTime()"
            class="relative flex flex-1 flex-col items-center justify-center overflow-hidden active:opacity-60"
            :class="cell.isHoliday ? 'bg-[#fdf0f6]' : cell.isWorkday ? 'bg-[#f5f7fa]' : ''"
            @click="handleSelect(cell)"
          >
            <!-- 节假日"休"标签（红色圆角小标签，右上角定位） -->
            <view
              v-if="cell.isHoliday"
              class="absolute right-1 top-0.5 h-3.5 min-w-3.5 flex items-center justify-center rounded-sm bg-[#e74c3c] px-0.5 text-[9px] text-white leading-none"
            >
              休
            </view>
            <!-- 调休"班"标签（蓝色） -->
            <view
              v-else-if="cell.isWorkday"
              class="absolute right-1 top-0.5 h-3.5 min-w-3.5 flex items-center justify-center rounded-sm bg-[#409eff] px-0.5 text-[9px] text-white leading-none"
            >
              班
            </view>

            <!-- 公历数字：选中实心主题色圆底 / 今日主题色圆环 / 周末红色 -->
            <view
              class="h-7 w-7 flex items-center justify-center rounded-full"
              :class="[
                cell.isSelected
                  ? 'bg-[#018d71] text-white'
                  : cell.isToday
                    ? 'border border-[#018d71] text-[#018d71]'
                    : cell.isWeekend && cell.isCurrentMonth && !cell.isHoliday && !cell.isWorkday
                      ? 'text-[#e74c3c]'
                      : '',
              ]"
            >
              <text :class="cell.isCurrentMonth ? 'text-sm' : 'text-xs text-[#c0c4cc]'">
                {{ cell.solar }}
              </text>
            </view>

            <!-- 农历 / 节日 / 节气文本（日历区变大，字号上调一档更饱满） -->
            <text
              class="mt-0.5 max-w-full truncate px-0.5 text-xs leading-none"
              :class="cell.isCurrentMonth ? (cell.isHoliday ? 'text-[#e74c3c]' : 'text-[#999]') : 'text-[#e5e6eb]'"
            >
              {{ cell.lunarText }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- ============ 区域二：日期详情（相对 2 份 = 剩余 1/4 的 2/3） ============ -->
    <view class="min-h-0 flex flex-col" :style="{ flex: 2 }">
      <!-- 高度有限：padding/字号/行距全面压缩，宜忌单行截断，信息完整可读 -->
      <view class="mx-4 my-1 box-border min-h-0 flex flex-1 flex-col justify-center overflow-hidden rounded-xl bg-white p-2 shadow-sm">
        <view class="text-[10px] text-[#666] leading-4">
          {{ detail.solarText }} {{ detail.weekText }}
        </view>
        <view class="mt-0.5 text-base text-[#f56c6c] font-bold leading-5">
          {{ detail.lunarMD }}
        </view>
        <view class="mt-0.5 text-[10px] text-[#999] leading-4">
          {{ detail.ganZhi }}
        </view>

        <!-- 宜 -->
        <view class="mt-0.5 flex items-start">
          <view class="h-3.5 w-3.5 flex shrink-0 items-center justify-center rounded-full bg-[#409eff] text-[9px] text-white leading-none">
            宜
          </view>
          <text class="line-clamp-1 ml-1.5 flex-1 text-[10px] text-[#666] leading-4">
            {{ detail.recommends }}
          </text>
        </view>
        <!-- 忌 -->
        <view class="mt-0.5 flex items-start">
          <view class="h-3.5 w-3.5 flex shrink-0 items-center justify-center rounded-full bg-[#f56c6c] text-[9px] text-white leading-none">
            忌
          </view>
          <text class="line-clamp-1 ml-1.5 flex-1 text-[10px] text-[#666] leading-4">
            {{ detail.avoids }}
          </text>
        </view>
      </view>
    </view>

    <!-- ============ 区域三：一言（相对 1 份 = 剩余 1/4 的 1/3） ============ -->
    <view class="min-h-0 flex flex-col" :style="{ flex: 1 }">
      <!-- 高度极小：一言文本单行截断，来源与「重新获取」同行压缩 -->
      <view class="mx-4 mb-1 mt-1 box-border min-h-0 flex flex-1 flex-col justify-center overflow-hidden rounded-xl bg-white px-3 py-1.5 shadow-sm">
        <text v-if="hitokotoLoading" class="text-[10px] text-[#999] leading-4">
          加载中...
        </text>
        <template v-else>
          <text class="line-clamp-1 text-[10px] text-[#666] leading-4">
            {{ hitokoto }}
          </text>
          <view class="mt-0.5 flex items-center justify-between">
            <text class="text-[10px] text-[#999] leading-4">
              —— {{ from }}
            </text>
            <!-- 获取失败时提供重新获取入口 -->
            <text v-if="hitokotoError" class="text-[10px] text-[#018d71] active:opacity-50" @click="fetchHitokoto">
              重新获取
            </text>
          </view>
        </template>
      </view>
    </view>
  </view>
</template>
