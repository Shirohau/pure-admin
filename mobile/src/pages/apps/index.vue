<script lang="ts" setup>
definePage({
  style: {
    navigationBarTitleText: '应用中心',
  },
})

/**
 * 应用入口定义：图标（wot-design-uni 内置图标）+ 名称 + 跳转地址
 * 后续新增应用时只需在 apps 数组追加一项即可
 */
interface IAppEntry {
  /** 应用名称 */
  name: string
  /** wd-icon 图标名 */
  icon: string
  /** 图标底色（与应用区分的主色） */
  color: string
  /** 跳转页面路径（navigateTo） */
  url: string
}

const apps: IAppEntry[] = [
  {
    name: '作者',
    icon: 'user',
    color: '#018d71',
    url: '/pages/author/list',
  },
  {
    name: '出版社',
    icon: 'shop',
    color: '#4a7de0',
    url: '/pages/publisher/list',
  },
  {
    name: '图书',
    icon: 'books',
    color: '#e6a23c',
    url: '/pages/book/list',
  },
]

// 顶部搜索关键词（wd-search v-model，输入即过滤）
const keyword = ref('')

/**
 * 过滤后的应用列表：按名称模糊匹配（实时）
 */
const filteredApps = computed(() => {
  const kw = keyword.value.trim()
  if (!kw) {
    return apps
  }
  return apps.filter(item => item.name.includes(kw))
})

/**
 * 点击应用格子：跳转对应模块页面
 * @param app 应用入口
 */
function handleOpen(app: IAppEntry) {
  uni.navigateTo({ url: app.url })
}

/**
 * 清空搜索（wd-search clear 事件）
 */
function handleClear() {
  keyword.value = ''
}
</script>

<template>
  <!--
    根容器高度扣减说明（与首页 pages/index/index.vue 保持一致的方案）：
    - var(--window-top)：导航栏占位（default 导航栏 44px，custom 导航栏为 0）；
    - 50px：底部自定义 tabbar（tabbar/index.vue）在文档流中的占位高度（h-50px）；
    - env(safe-area-inset-bottom)：iPhone 底部安全区（与 tabbar 的 pb-safe 对应）；
    - box-border + flex-col：避免 pt-safe 的 padding-top 在 content-box 下叠加到 min-height 之外，
      并阻断子元素 margin-top 折叠穿透导致的额外溢出；
    - 使用 min-height 而非 height：内容不足一屏时恰好铺满可视区域（无滚动条），
      内容超高时页面自然滚动。
  -->
  <view
    class="box-border flex flex-col bg-[#f6f7fb] pt-safe"
    :style="{ minHeight: 'calc(100vh - var(--window-top) - 50px - env(safe-area-inset-bottom))' }"
  >
    <!-- 顶部搜索框 -->
    <view class="bg-[#f6f7fb] px-4 pt-3">
      <wd-search
        v-model="keyword"
        placeholder="搜索应用名称"
        shape="round"
        hide-cancel
        @clear="handleClear"
      />
    </view>

    <!-- 九宫格：3 列网格布局 -->
    <view class="mx-4 mt-4 rounded-xl bg-white p-2 shadow-sm">
      <view class="grid grid-cols-3 gap-y-6 py-3">
        <view
          v-for="app in filteredApps"
          :key="app.name"
          class="flex flex-col items-center"
          @click="handleOpen(app)"
        >
          <!-- 图标：主题色圆角块 + 白色图标 -->
          <view
            class="h-12 w-12 flex items-center justify-center rounded-xl"
            :style="{ backgroundColor: app.color }"
          >
            <wd-icon :name="app.icon" size="24px" color="#fff" />
          </view>
          <!-- 名称 -->
          <text class="mt-2 text-sm text-[#333]">{{ app.name }}</text>
        </view>
      </view>
    </view>

    <!-- 无匹配结果空态 -->
    <view
      v-if="filteredApps.length === 0"
      class="flex flex-col items-center px-4 pt-12"
    >
      <text class="text-sm text-[#999]">未找到相关应用</text>
    </view>
  </view>
</template>
