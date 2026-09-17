<script lang="ts" setup>
import { useTokenStore } from '@/store/token'
import { useUserStore } from '@/store/user'
import { toLoginPage } from '@/utils/toLoginPage'

definePage({
  style: {
    navigationBarTitleText: '我的',
  },
})

const tokenStore = useTokenStore()
const userStore = useUserStore()

// 是否已登录（令牌存在且未过期）
const isLogin = computed(() => tokenStore.updateNowTime().hasLogin)

/**
 * 跳转登录页（携带当前页面作为登录成功后的回跳地址）
 */
function handleGoLogin() {
  toLoginPage({
    mode: 'reLaunch',
    queryString: `?redirect=${encodeURIComponent('/pages/me/me')}`,
  })
}

/**
 * 跳转「应用中心」九宫格页（页面底部「关于」区域入口）
 *
 * 应用中心页为 tabBar 页面（pages.json tabBar 已注册），须使用 switchTab 跳转，
 * navigateTo 无法打开 tabBar 页面。
 */
function handleGoAppCenter() {
  uni.switchTab({ url: '/pages/apps/index' })
}

/**
 * 跳转「关于」页面
 *
 * 关于页为普通页面（非 tabBar 页面），使用 navigateTo 跳转。
 */
function handleGoAbout() {
  uni.navigateTo({ url: '/pages/about/about' })
}

/**
 * 退出登录：清理本地令牌与用户信息，并跳转登录页
 *
 * 流程说明：
 * 1. 弹出确认弹窗，用户点击「确定」后继续；
 * 2. 调用 tokenStore.logout() 清除本地令牌与用户信息（含持久化存储）；
 * 3. uni.showToast 提示「已退出登录」；
 * 4. 调用 toLoginPage 以 reLaunch 模式跳转登录页。
 *
 * 注意：主动退出场景不携带 redirect 回跳参数，退出后不应再回到退出前的页面；
 * 登录页本身在路由白名单中（免登录），跳转不会被路由拦截器再次拦截。
 */
async function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: async (res) => {
      if (res.confirm) {
        // 先清理本地令牌与用户信息
        await tokenStore.logout()
        // 再提示退出成功
        uni.showToast({ title: '已退出登录', icon: 'none' })
        // 最后跳转登录页（reLaunch 清空页面栈，不携带 redirect 回跳参数）
        toLoginPage({ mode: 'reLaunch' })
      }
    },
  })
}
</script>

<template>
  <!--
    根容器高度扣减说明（与首页 pages/index/index.vue 保持一致的方案）：
    - var(--window-top)：导航栏占位（default 导航栏 44px，custom 导航栏为 0）；
    - 50px：底部自定义 tabbar（tabbar/index.vue）在文档流中的占位高度（h-50px）；
    - env(safe-area-inset-bottom)：iPhone 底部安全区（与 tabbar 的 pb-safe 对应）；
    - box-border + flex-col：避免 pt-safe 的 padding-top 在 content-box 下叠加到 min-height 之外，
      并阻断子元素 margin-top 折叠穿透（首个卡片 mt-4）导致的额外溢出；
    - 使用 min-height 而非 height：内容不足一屏时恰好铺满可视区域（无滚动条），
      内容超高时页面自然滚动。
  -->
  <view
    class="box-border flex flex-col bg-[#f6f7fb] pt-safe"
    :style="{ minHeight: 'calc(100vh - var(--window-top) - 50px - env(safe-area-inset-bottom))' }"
  >
    <!-- 用户信息卡片 -->
    <view class="mx-4 mt-4 flex items-center rounded-xl bg-white p-5 shadow-sm">
      <image
        :src="userStore.userInfo.avatar"
        alt="avatar"
        class="h-16 w-16 rounded-full"
      />
      <view class="ml-4 flex-1">
        <!-- 已登录：展示用户名、姓名与所属部门 -->
        <template v-if="isLogin">
          <view class="text-lg text-[#2a2a2a] font-bold">
            {{ userStore.userInfo.name || userStore.userInfo.username }}
          </view>
          <view class="mt-1 text-sm text-[#999]">
            {{ userStore.userInfo.username }}
          </view>
          <!-- 所属部门：登录接口返回 deptName，未分配部门时隐藏 -->
          <view
            v-if="userStore.userInfo.deptName"
            class="mt-1 flex items-center text-sm text-[#999]"
          >
            <text class="mr-1 h-1.5 w-1.5 rounded-full bg-[#018d71]"></text>
            <text>{{ userStore.userInfo.deptName }}</text>
          </view>
        </template>
        <!-- 未登录：提示去登录 -->
        <template v-else>
          <view class="text-lg text-[#2a2a2a] font-bold">
            未登录
          </view>
          <view class="mt-1 text-sm text-[#999]">
            登录后同步你的信息
          </view>
        </template>
      </view>
    </view>

    <!-- 未登录：展示去登录按钮（独立卡片） -->
    <view
      v-if="!isLogin"
      class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm"
    >
      <wd-button
        size="large"
        block
        type="primary"
        @click="handleGoLogin"
      >
        去登录
      </wd-button>
    </view>

    <!-- 应用中心入口卡片：点击跳转「应用中心」九宫格页（聚合作者/出版社/图书等应用入口） -->
    <view
      class="mx-4 mt-4 flex items-center justify-between rounded-xl bg-white px-5 py-5 shadow-sm"
      @click="handleGoAppCenter"
    >
      <text class="text-lg font-medium leading-none text-[#333]">应用中心</text>
      <text class="i-carbon-chevron-right text-2xl leading-none text-[#c0c4cc]" />
    </view>

    <!-- 关于入口卡片：点击跳转「关于」页展示系统版本号与说明 -->
    <view
      class="mx-4 mt-4 flex items-center justify-between rounded-xl bg-white px-5 py-5 shadow-sm"
      @click="handleGoAbout"
    >
      <text class="text-lg font-medium leading-none text-[#333]">关于</text>
      <text class="i-carbon-chevron-right text-2xl leading-none text-[#c0c4cc]" />
    </view>

    <!-- 退出登录：独立置底展示，与上方操作区隔离 -->
    <view
      v-if="isLogin"
      class="mx-4 mt-4 mb-4 rounded-xl bg-white p-5 shadow-sm"
    >
      <wd-button
        size="large"
        plain
        block
        type="error"
        @click="handleLogout"
      >
        退出登录
      </wd-button>
    </view>
  </view>
</template>
