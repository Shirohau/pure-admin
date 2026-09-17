<script lang="ts" setup>
import { deleteBook, getBookDetail, type IBookItem } from '@/api/book'

definePage({
  style: {
    navigationBarTitleText: '图书详情',
  },
})

/** 图书详情数据 */
const detail = ref<IBookItem | null>(null)
// 当前详情图书 id（编辑保存返回后据此重新拉取）
const bookId = ref<number | null>(null)
// 首次加载中（控制 loading 态）
const loading = ref(false)
// 是否已完成首次加载（避免 onShow 首触发重复请求）
let hasLoaded = false
// 数据变更标记：编辑页保存后置位，onShow 时据此刷新
let changed = false
// 加载失败标记（展示重试态）
const loadFailed = ref(false)
// 删除按钮加载状态
const deleting = ref(false)

// 数据变更监听回调（$off 需传同一引用，否则会清空该事件全部监听器）
const onChanged = () => {
  changed = true
}
/**
 * 页面加载：解析路由参数 id 拉取详情，并订阅数据变更事件
 */
onLoad((options) => {
  if (options?.id) {
    bookId.value = Number(options.id)
    loadDetail(bookId.value)
  }
  uni.$on('book:changed', onChanged)
})

/**
 * 页面显示：编辑保存返回后重新拉取详情，保证数据最新
 */
onShow(() => {
  if (hasLoaded && changed && bookId.value) {
    changed = false
    loadDetail(bookId.value)
  }
})

onUnload(() => {
  uni.$off('book:changed', onChanged)
})

/**
 * 拉取图书详情
 * @param id 图书主键
 */
async function loadDetail(id: number) {
  loadFailed.value = false
  if (!hasLoaded) {
    loading.value = true
  }
  try {
    const data = await getBookDetail(id)
    detail.value = data
    hasLoaded = true
    // 动态设置导航栏标题为书名
    uni.setNavigationBarTitle({ title: data.name || '图书详情' })
  }
  catch {
    loadFailed.value = true
  }
  finally {
    loading.value = false
  }
}

/**
 * 跳转编辑页（带当前 id，表单页回填）
 */
function handleEdit() {
  if (!bookId.value) {
    return
  }
  uni.navigateTo({ url: `/pages/book/form?id=${bookId.value}` })
}

/**
 * 删除图书：直接调接口，成功后提示并返回上一页
 */
async function handleDelete() {
  if (!bookId.value || deleting.value) {
    return
  }
  deleting.value = true
  try {
    await deleteBook(bookId.value!)
    uni.showToast({ title: '删除成功', icon: 'success' })
    // 通知列表页刷新
    uni.$emit('book:changed')
    setTimeout(() => {
      uni.navigateBack()
    }, 600)
  }
  catch {
    // 删除失败提示已由 http 拦截器统一 toast
  }
  finally {
    deleting.value = false
  }
}

/**
 * 时间展示：后端 ISO 时间串转为 "YYYY-MM-DD HH:mm"
 */
function formatTime(value?: string) {
  if (!value) {
    return '—'
  }
  return value.replace('T', ' ').slice(0, 16)
}

/**
 * 价格展示：¥ + 字符串（后端 Decimal 序列化为字符串）
 */
function priceText(price?: string) {
  if (price == null) {
    return '—'
  }
  return `¥${price}`
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pt-safe pb-28">
    <!-- 首次加载中 -->
    <view v-if="loading" class="flex flex-col items-center px-4 pt-16">
      <wd-loading size="24px" />
      <text class="mt-3 text-sm text-[#999]">加载中…</text>
    </view>

    <!-- 加载失败重试态 -->
    <view v-else-if="loadFailed" class="flex flex-col items-center px-4 pt-16">
      <text class="text-sm text-[#999]">加载失败，请检查网络后重试</text>
      <wd-button
        class="mt-4"
        size="small"
        plain
        @click="bookId ? loadDetail(bookId) : undefined"
      >
        重新加载
      </wd-button>
    </view>

    <template v-else-if="detail">
      <!-- 头部：书名 + 价格 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="text-lg font-bold text-[#2a2a2a]">{{ detail.name }}</view>
        <view class="mt-2 text-base font-bold text-[#e54d42]">{{ priceText(detail.price) }}</view>
      </view>

      <!-- 基本信息 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">基本信息</view>
        <view class="divide-y divide-[#f2f3f5]">
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">ISBN</text>
            <text class="text-sm text-[#333]">{{ detail.isbn || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">出版社</text>
            <text class="text-sm text-[#333]">{{ detail.publisher_name || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">出版时间</text>
            <text class="text-sm text-[#333]">{{ formatTime(detail.publication_time) }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">页数</text>
            <text class="text-sm text-[#333]">{{ detail.pages != null ? `${detail.pages} 页` : '—' }}</text>
          </view>
        </view>
      </view>

      <!-- 内容简介 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">内容简介</view>
        <text class="text-sm leading-relaxed text-[#666]">{{ detail.description || '暂无简介' }}</text>
      </view>

      <!-- 关联作者 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">关联作者</view>
        <view
          v-if="detail.author_all && detail.author_all.length > 0"
          class="divide-y divide-[#f2f3f5]"
        >
          <view
            v-for="author in detail.author_all"
            :key="author.id"
            class="flex items-center justify-between py-2.5"
          >
            <text class="text-sm text-[#333]">{{ author.name }}</text>
            <text class="text-xs text-[#999]">创建人：{{ author.creator_name || '—' }}</text>
          </view>
        </view>
        <text v-else class="text-sm text-[#999]">暂无关联作者</text>
      </view>

      <!-- 审计信息 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">审计信息</view>
        <view class="divide-y divide-[#f2f3f5]">
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">创建人</text>
            <text class="text-sm text-[#333]">{{ detail.creator_name || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">创建时间</text>
            <text class="text-sm text-[#333]">{{ formatTime(detail.create_dt) }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">更新人</text>
            <text class="text-sm text-[#333]">{{ detail.updater_name || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">更新时间</text>
            <text class="text-sm text-[#333]">{{ formatTime(detail.update_dt) }}</text>
          </view>
        </view>
      </view>
    </template>

    <!-- 底部固定操作条 -->
    <view v-if="detail" class="fixed inset-x-0 bottom-0 z-10 flex bg-white px-4 pt-3 shadow-sm pb-safe">
      <wd-button
        class="flex-1"
        size="large"
        plain
        type="primary"
        @click="handleEdit"
      >
        编 辑
      </wd-button>
      <wd-button
        class="ml-3 flex-1"
        size="large"
        plain
        type="error"
        :loading="deleting"
        @click="handleDelete"
      >
        删 除
      </wd-button>
    </view>
  </view>
</template>
