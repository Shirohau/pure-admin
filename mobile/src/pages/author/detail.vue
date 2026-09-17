<script lang="ts" setup>
import { deleteAuthor, getAuthorDetail } from '@/api/author'
import type { IAuthorItem } from '@/api/author'

definePage({
  style: {
    navigationBarTitleText: '作者详情',
  },
})

/** 作者详情数据 */
const detail = ref<IAuthorItem | null>(null)
// 当前详情作者 id（编辑保存返回后据此重新拉取）
const authorId = ref<number | null>(null)
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
    authorId.value = Number(options.id)
    loadDetail(authorId.value)
  }
  uni.$on('author:changed', onChanged)
})

/**
 * 页面显示：编辑保存返回后重新拉取详情，保证数据最新
 */
onShow(() => {
  if (hasLoaded && changed && authorId.value) {
    changed = false
    loadDetail(authorId.value)
  }
})

/**
 * 页面卸载：注销数据变更事件
 */
onUnload(() => {
  uni.$off('author:changed', onChanged)
})

/**
 * 拉取作者详情
 * @param id 作者主键
 */
async function loadDetail(id: number) {
  loadFailed.value = false
  try {
    detail.value = await getAuthorDetail(id)
    hasLoaded = true
    // 动态设置导航栏标题为作者姓名
    uni.setNavigationBarTitle({ title: detail.value.name || '作者详情' })
  }
  catch {
    loadFailed.value = true
  }
}

/**
 * 跳转编辑页
 */
function handleEdit() {
  if (detail.value) {
    uni.navigateTo({ url: `/pages/author/form?id=${detail.value.id}` })
  }
}

/**
 * 删除作者：直接调接口，成功后广播变更事件并返回列表页
 */
async function handleDelete() {
  const item = detail.value
  if (!item || deleting.value) {
    return
  }
  deleting.value = true
  try {
    await deleteAuthor(item.id)
    uni.showToast({ title: '删除成功', icon: 'success' })
    uni.$emit('author:changed')
    setTimeout(() => uni.navigateBack(), 600)
  }
  catch {
    // 删除失败（如被图书引用）提示已由 http 拦截器统一 toast
  }
  finally {
    deleting.value = false
  }
}

/**
 * 格式化时间展示：ISO 时间串转 "YYYY-MM-DD HH:mm"（无值时返回占位符）
 * @param value 后端返回的时间字符串
 */
function formatTime(value?: string) {
  if (!value) {
    return '—'
  }
  return value.replace('T', ' ').slice(0, 16)
}

/**
 * 性别展示（空值显示占位符）
 */
function genderText(gender?: string) {
  return gender || '—'
}

/**
 * 年龄展示（空值显示占位符）
 */
function ageText(age?: number) {
  return age != null ? String(age) : '—'
}

/**
 * 图书平均价格展示（保留两位小数，空值显示占位符）
 */
function avgPriceText(price?: string) {
  return price != null ? `¥${price}` : '—'
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pb-28 pt-safe">
    <!-- 加载失败 -->
    <view v-if="loadFailed" class="flex flex-col items-center px-4 pt-16">
      <text class="text-sm text-[#999]">加载失败，请检查网络后重试</text>
      <wd-button
        class="mt-4"
        size="small"
        plain
        @click="authorId ? loadDetail(authorId) : undefined"
      >
        重新加载
      </wd-button>
    </view>

    <template v-else-if="detail">
      <!-- 头部卡片：姓名 + 性别/年龄 -->
      <view class="mx-4 mt-4 flex items-center rounded-xl bg-white p-5 shadow-sm">
        <view class="flex-1">
          <view class="text-xl text-[#2a2a2a] font-bold">
            {{ detail.name }}
          </view>
          <view class="mt-2 flex items-center gap-x-3 text-sm text-[#666]">
            <text>性别：{{ genderText(detail.gender) }}</text>
            <text>年龄：{{ ageText(detail.age) }}</text>
          </view>
        </view>
      </view>

      <!-- 基本信息卡片 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="text-sm text-[#333] font-bold">
          基本信息
        </view>
        <view class="mt-3 divide-y divide-[#f2f3f5]">
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">出生日期</text>
            <text class="text-[#333]">{{ detail.birth_date || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">图书数量</text>
            <text class="text-[#333]">{{ detail.book_count ?? detail.book.length }} 本</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">图书均价</text>
            <text class="text-[#333]">{{ avgPriceText(detail.avg_price) }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">创建人</text>
            <text class="text-[#333]">{{ detail.creator_name || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">创建时间</text>
            <text class="text-[#333]">{{ formatTime(detail.create_dt) }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">更新人</text>
            <text class="text-[#333]">{{ detail.updater_name || '—' }}</text>
          </view>
          <view class="flex items-center justify-between py-2.5 text-sm">
            <text class="text-[#999]">更新时间</text>
            <text class="text-[#333]">{{ formatTime(detail.update_dt) }}</text>
          </view>
        </view>
      </view>

      <!-- 简介卡片 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="text-sm text-[#333] font-bold">
          简介
        </view>
        <view class="mt-3 text-sm text-[#666] leading-6">
          {{ detail.biography || '暂无简介' }}
        </view>
      </view>

      <!-- 关联图书卡片 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <view class="text-sm text-[#333] font-bold">
          关联图书（{{ detail.book_all?.length ?? 0 }}）
        </view>
        <view v-if="detail.book_all && detail.book_all.length > 0" class="mt-3">
          <view
            v-for="book in detail.book_all"
            :key="book.id"
            class="flex items-center justify-between border-t border-[#f2f3f5] py-2.5 text-sm first:border-t-0"
          >
            <view class="flex-1">
              <text class="text-[#333]">{{ book.name }}</text>
              <text class="ml-2 text-xs text-[#999]">更新：{{ book.updater_name || '—' }}</text>
            </view>
            <text class="text-[#018d71]">¥{{ book.price }}</text>
          </view>
        </view>
        <view v-else class="mt-3 text-sm text-[#999]">
          暂无关联图书
        </view>
      </view>
    </template>

    <!-- 底部操作条：编辑 + 删除，固定贴底（含安全区） -->
    <view v-if="detail" class="fixed inset-x-0 bottom-0 z-10 flex gap-3 bg-white px-4 pt-3 shadow-sm pb-safe">
      <wd-button
        class="flex-1"
        size="large"
        type="primary"
        plain
        @click="handleEdit"
      >
        编 辑
      </wd-button>
      <wd-button
        class="flex-1"
        size="large"
        type="error"
        :loading="deleting"
        @click="handleDelete"
      >
        删 除
      </wd-button>
    </view>
  </view>
</template>
