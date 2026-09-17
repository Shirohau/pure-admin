<script lang="ts" setup>
import { deletePublisher, getPublisherDetail, type IPublisherItem } from '@/api/publisher'

definePage({
  style: {
    navigationBarTitleText: '出版社详情',
  },
})

/** 出版社详情数据 */
const detail = ref<IPublisherItem | null>(null)
// 当前详情出版社 id（编辑保存返回后据此重新拉取）
const publisherId = ref<number | null>(null)
// 是否已完成首次加载（避免 onShow 首触发重复请求）
let hasLoaded = false
// 数据变更标记：编辑页保存后置位，onShow 时据此刷新
let changed = false
// 加载失败标记（展示重试态）
const loadFailed = ref(false)
// 删除按钮加载状态
const deleting = ref(false)

/**
 * 页面加载：解析路由参数 id 拉取详情，并订阅数据变更事件
 */
// 数据变更监听回调（$off 需传同一引用，否则会清空该事件全部监听器）
const onChanged = () => {
  changed = true
}
onLoad((options) => {
  if (options?.id) {
    publisherId.value = Number(options.id)
    loadDetail(publisherId.value)
  }
  uni.$on('publisher:changed', onChanged)
})

/**
 * 页面显示：编辑保存返回后重新拉取详情，保证数据最新
 */
onShow(() => {
  if (hasLoaded && changed && publisherId.value) {
    changed = false
    loadDetail(publisherId.value)
  }
})

onUnload(() => {
  uni.$off('publisher:changed', onChanged)
})

/**
 * 拉取出版社详情
 * @param id 出版社主键
 */
async function loadDetail(id: number) {
  loadFailed.value = false
  try {
    const data = await getPublisherDetail(id)
    detail.value = data
    hasLoaded = true
    // 动态设置导航栏标题为出版社名称
    uni.setNavigationBarTitle({ title: data.name || '出版社详情' })
  }
  catch {
    loadFailed.value = true
  }
}

/**
 * 跳转编辑页（带当前 id，表单页回填）
 */
function handleEdit() {
  if (!publisherId.value) {
    return
  }
  uni.navigateTo({ url: `/pages/publisher/form?id=${publisherId.value}` })
}

/**
 * 删除出版社：直接调接口，成功后提示并返回上一页
 */
async function handleDelete() {
  if (!publisherId.value || deleting.value) {
    return
  }
  deleting.value = true
  try {
    await deletePublisher(publisherId.value!)
    uni.showToast({ title: '删除成功', icon: 'success' })
    // 通知列表页刷新
    uni.$emit('publisher:changed')
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
 * 地区展示（优先 area_str，缺失时拼接省市县）
 */
function areaText(item: IPublisherItem) {
  const joined = [item.province, item.city, item.district].filter(Boolean).join(' / ')
  return item.area_str || joined || '—'
}

/**
 * 价格展示：¥ + 字符串（后端 Decimal 序列化为字符串）
 */
function avgPriceText(price?: string) {
  if (price == null) {
    return '—'
  }
  return `¥${price}`
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pt-safe pb-28">
    <!-- 加载失败重试态 -->
    <view v-if="loadFailed" class="flex flex-col items-center px-4 pt-16">
      <text class="text-sm text-[#999]">加载失败，请检查网络后重试</text>
      <wd-button
        class="mt-4"
        size="small"
        plain
        @click="publisherId ? loadDetail(publisherId) : undefined"
      >
        重新加载
      </wd-button>
    </view>

    <template v-else-if="detail">
      <!-- 头部：名称 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="text-lg font-bold text-[#2a2a2a]">{{ detail.name }}</view>
        <view class="mt-2 text-xs text-[#999]">出版社编号：{{ detail.id }}</view>
      </view>

      <!-- 基本信息 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">基本信息</view>
        <view class="divide-y divide-[#f2f3f5]">
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">地区</text>
            <text class="text-sm text-[#333]">{{ areaText(detail) }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">详细地址</text>
            <text class="text-sm text-[#333]">{{ detail.address || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">联系电话</text>
            <text class="text-sm text-[#333]">{{ detail.phone || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">邮箱</text>
            <text class="text-sm text-[#333]">{{ detail.email || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5">
            <text class="text-sm text-[#999]">官网网址</text>
            <text class="text-sm text-[#018d71]">{{ detail.website || '—' }}</text>
          </view>
        </view>
      </view>

      <!-- 图书统计 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">图书统计</view>
        <view class="flex items-center">
          <view class="flex-1">
            <view class="text-xl font-bold text-[#018d71]">
              {{ detail.book_count ?? detail.book.length }}
            </view>
            <view class="mt-1 text-xs text-[#999]">图书数量</view>
          </view>
          <view class="flex-1">
            <view class="text-xl font-bold text-[#018d71]">
              {{ avgPriceText(detail.avg_price) }}
            </view>
            <view class="mt-1 text-xs text-[#999]">图书均价</view>
          </view>
        </view>
      </view>

      <!-- 关联图书 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="mb-3 text-sm font-bold text-[#2a2a2a]">关联图书</view>
        <view
          v-if="detail.book_all && detail.book_all.length > 0"
          class="divide-y divide-[#f2f3f5]"
        >
          <view
            v-for="book in detail.book_all"
            :key="book.id"
            class="flex items-center justify-between py-2.5"
          >
            <text class="text-sm text-[#333]">{{ book.name }}</text>
            <text class="text-sm text-[#999]">¥{{ book.price }}</text>
          </view>
        </view>
        <text v-else class="text-sm text-[#999]">暂无关联图书</text>
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
