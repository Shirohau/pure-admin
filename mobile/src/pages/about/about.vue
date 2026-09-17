<script lang="ts" setup>
// 系统版本号来源：mobile/package.json 的 version 字段（npm 包版本号）
import packageJson from '../../../package.json'

definePage({
  style: {
    navigationBarTitleText: '关于',
  },
})

// 系统名称：构建环境变量注入（VITE_APP_TITLE），未配置时兜底展示
const appName = import.meta.env.VITE_APP_TITLE || '移动端应用'
// 系统版本号（package.json version 字段）
const version = packageJson.version
</script>

<template>
  <!--
    自适应布局说明：
    - flex 纵向布局：内容矮时撑满可用高度，内容高时自然扩展；
    - minHeight 扣除 H5 导航栏（--window-top）及底部安全区，
      使内容不超过一屏可视区域，避免出现滚动条；
      （关于页已不是 tabBar 页面，无需再扣除自定义 tabbar 的 50px 占位）
    - 用内联 style 而非 unocss 类，避免 presetUni 的 px→rpx 转换影响 calc 计算。
  -->
  <view
    class="flex flex-col bg-[#f6f7fb] pt-safe"
    :style="{
      minHeight: 'calc(100vh - var(--window-top) - env(safe-area-inset-bottom))',
    }"
  >
    <!-- 应用图标与名称：顶部间距按屏幕高度比例适配（presetUni 不支持 vh 任意值类，故用内联 style） -->
    <view
      class="flex flex-col items-center"
      :style="{ paddingTop: '10vh' }"
    >
      <image src="/static/logo.svg" alt="logo" class="h-20 w-20" />
      <view class="mt-4 text-xl text-[#2a2a2a] font-bold">
        {{ appName }}
      </view>
      <view class="mt-1 text-sm text-[#999]">
        版本 {{ version }}
      </view>
    </view>

    <!-- 系统说明卡片：间距随屏幕高度比例适配 -->
    <view
      class="mx-4 rounded-xl bg-white p-5 shadow-sm"
      :style="{ marginTop: '4vh' }"
    >
      <view class="text-sm text-[#666] leading-6">
        本应用基于 unibest 框架构建（uni-app + Vue3 + TypeScript），
        提供账号密码登录及微信、企业微信、QQ、支付宝等第三方登录能力，
        支持 H5 与微信小程序双端运行。
      </view>
    </view>

    <!-- 版权信息：mt-auto 自动贴底，随内容流排布，不重叠不额外撑出滚动条 -->
    <view
      class="mt-auto pb-8 text-center text-xs text-[#c0c4cc]"
      :style="{ paddingTop: '4vh' }"
    >
      © 2026 unibest 保留所有权利
    </view>
  </view>
</template>
