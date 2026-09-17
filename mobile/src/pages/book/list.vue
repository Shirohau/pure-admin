<script lang="ts" setup>
import { deleteBook, getBookList, type IBookItem } from '@/api/book'

definePage({
  style: {
    navigationBarTitleText: '图书',
    // 开启下拉刷新（微信小程序生效；H5 端下拉刷新能力有限，页面内提供空态重试兜底）
    enablePullDownRefresh: true,
    backgroundTextStyle: 'dark',
  },
})

/** 每页数量（后端 limit 参数） */
const PAGE_SIZE = 10

// 列表数据与分页状态
const list = ref<IBookItem[]>([])
const page = ref(1)
// 是否还有更多数据：通过 paginated.next 判断
const hasMore = ref(true)
// 首屏加载中（控制骨架/加载态）
const loading = ref(false)
// 触底加载更多中（防止重复触发）
const loadingMore = ref(false)
// 首屏加载失败（展示失败重试态）
const loadFailed = ref(false)

// 数据变更标记：表单页保存成功后通过 uni.$emit('book:changed') 通知本页刷新
let changed = false

/**
 * 加载图书列表
 * @param init 是否为重新加载（true：回到第一页并清空旧数据）
 */
async function loadList(init: boolean) {
  if (init) {
    page.value = 1
    hasMore.value = true
    loadFailed.value = false
  }
  if (loadingMore.value || !hasMore.value) {
    return
  }
  if (init) {
    loading.value = true
  }
  else {
    loadingMore.value = true
  }
  try {
    const { data, paginated } = await getBookList({ page: page.value, limit: PAGE_SIZE })
    // 直接追加新数据（后端分页不会重复返回）
    list.value = init ? data : [...list.value, ...data]
    // 通过 paginated.next 判断是否还有更多数据
    hasMore.value = paginated != null && paginated.next != null
    page.value += 1
  }
  catch {
    if (init) {
      loadFailed.value = true
    }
    // 错误提示已由 http 拦截器统一 toast
  }
  finally {
    loading.value = false
    loadingMore.value = false
    uni.stopPullDownRefresh()
  }
}

// 首次进入加载第一页
onLoad(() => {
  loadList(true)
})

// 表单页保存成功后（book:changed 事件）刷新列表
onShow(() => {
  if (changed) {
    changed = false
    loadList(true)
  }
})

// 注册/注销数据变更监听
// 注意：uni.$off 必须传入与 $on 相同的回调引用，否则会移除该事件的所有监听器
// （H5 端 eventBus.off 不带 callback 会清空该事件全部监听，误杀其他页面的监听器）
const onChanged = () => {
  changed = true
}
onLoad(() => {
  uni.$on('book:changed', onChanged)
})
onUnload(() => {
  uni.$off('book:changed', onChanged)
})

// 下拉刷新（小程序端生效）
onPullDownRefresh(() => {
  loadList(true)
})

// 触底加载下一页
onReachBottom(() => {
  if (!loading.value) {
    loadList(false)
  }
})

/**
 * 跳转新增图书表单页
 */
function handleAdd() {
  uni.navigateTo({ url: '/pages/book/form' })
}

/**
 * 跳转图书详情页
 * @param item 图书条目（仅传 id，详情页重新拉取完整数据）
 */
function handleDetail(item: IBookItem) {
  uni.navigateTo({ url: `/pages/book/detail?id=${item.id}` })
}

/**
 * 跳转编辑图书表单页（阻止事件冒泡，避免触发详情跳转）
 * @param item 图书条目
 */
function handleEdit(item: IBookItem) {
  uni.navigateTo({ url: `/pages/book/form?id=${item.id}` })
}

/**
 * 删除图书：二次确认后调接口，成功后重新加载第一页并提示
 * @param item 图书条目
 */
function handleDelete(item: IBookItem) {
  uni.showModal({
    title: '删除提示',
    content: `确定要删除图书「${item.name}」吗？`,
    confirmColor: '#e54d42',
    success: async (res) => {
      if (!res.confirm) {
        return
      }
      try {
        await deleteBook(item.id)
        uni.showToast({ title: '删除成功', icon: 'success' })
        // 通知其他页面数据已变更
        uni.$emit('book:changed')
        // 删除后总数变化，回第一页重新加载保证页码与数据一致
        loadList(true)
      }
      catch {
        // 删除失败提示已由 http 拦截器统一 toast
      }
    },
  })
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pt-safe">
    <!-- 新增入口已收敛为右下角悬浮「+」按钮（FAB），见模板底部 -->

    <!-- 首屏加载中 -->
    <view v-if="loading" class="flex flex-col items-center px-4 pt-16">
      <wd-loading size="24px" />
      <text class="mt-3 text-sm text-[#999]">加载中…</text>
    </view>

    <!-- 首屏加载失败 -->
    <view v-else-if="loadFailed" class="flex flex-col items-center px-4 pt-16">
      <text class="text-sm text-[#999]">加载失败，请检查网络后重试</text>
      <wd-button class="mt-4" size="small" plain @click="loadList(true)">
        重新加载
      </wd-button>
    </view>

    <!-- 空态 -->
    <view v-else-if="list.length === 0" class="flex flex-col items-center px-4 pt-16">
      <text class="text-sm text-[#999]">暂无图书数据</text>
      <wd-button class="mt-4" size="small" plain @click="handleAdd">
        去新增
      </wd-button>
    </view>

    <!-- 图书列表 -->
    <view v-else class="px-4 pb-24">
      <wd-swipe-action v-for="item in list" :key="item.id" class="mb-3">
        <view
          class="rounded-xl bg-white p-4 shadow-sm"
          @click="handleDetail(item)"
        >
          <!-- 第一行：书名 -->
          <text class="text-base font-bold text-[#2a2a2a]">{{ item.name }}</text>

          <!-- 第二行：价格 / ISBN / 出版社 / 页数 -->
          <view class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[#666]">
            <text class="text-[#e54d42]">¥{{ item.price }}</text>
            <text>ISBN：{{ item.isbn }}</text>
            <text v-if="item.publisher_name">出版社：{{ item.publisher_name }}</text>
            <text v-if="item.pages != null">页数：{{ item.pages }}</text>
          </view>

          <!-- 第三行：简介摘要（单行截断） -->
          <view
            v-if="item.description"
            class="mt-2 line-clamp-1 text-xs text-[#999]"
          >
            {{ item.description }}
          </view>
        </view>
        <template #right>
          <view class="flex h-full">
            <wd-button
              type="warning"
              size="small"
              class="h-full"
              @click.stop="handleEdit(item)"
            >编辑</wd-button>
            <wd-button
              type="error"
              size="small"
              class="h-full"
              @click.stop="handleDelete(item)"
            >删除</wd-button>
          </view>
        </template>
      </wd-swipe-action>

      <!-- 底部加载状态 -->
      <view class="flex items-center justify-center py-3">
        <wd-loading v-if="loadingMore" size="16px" />
        <text v-else-if="!hasMore && list.length > 0" class="text-xs text-[#999]">没有更多了</text>
        <text v-else class="text-xs text-[#999]">上拉加载更多</text>
      </view>
    </view>

    <!-- 右下角悬浮「新增」按钮（FAB）：
         fixed 固定于视口右下角（right-4 = 距右 16px，bottom = 16px + 底部安全区 env(safe-area-inset-bottom)），
         与列表底部 pb-24 留白配合，滚动到底也不会遮挡最后一条数据；
         z-50 高于页面内容（原 sticky 条 z-10）、低于系统浮层（uni-modal 遮罩 999、自定义 tabbar 99）；
         v-if="!loading"：首屏加载骨架态不展示，避免悬浮在加载提示上。 -->
    <view
      v-if="!loading"
      class="fixed right-4 z-50 flex h-50px w-50px items-center justify-center rounded-full bg-[#018d71] shadow-lg active:opacity-80"
      :style="{ bottom: 'calc(16px + env(safe-area-inset-bottom))' }"
      @click="handleAdd"
    >
      <text class="i-carbon-add text-2xl leading-none text-white" />
    </view>
  </view>
</template>
