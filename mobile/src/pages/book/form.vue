<script lang="ts" setup>
import type { FormExpose, FormRules } from 'wot-design-uni/components/wd-form/types'
import { getBookDetail, createBook, updateBook, type IBookForm } from '@/api/book'
import { getAuthorList } from '@/api/author'
import { getPublisherList } from '@/api/publisher'

definePage({
  style: {
    navigationBarTitleText: '图书表单',
  },
})

/**
 * 表单数据（宽松类型：数值/文本统一用字符串承接 wd-input 输入，提交时转后端所需格式）
 * 字段与后端 BookSerializer / web 端表单对齐，author 为关联作者 ID 数组（后端要求至少 1 位）。
 */
const form = ref<{
  name: string
  isbn: string
  price: string
  pages: string
  publication_time: string
  publisher: number | null
  description: string
  author: number[]
}>({
  name: '',
  isbn: '',
  price: '',
  pages: '',
  publication_time: '',
  publisher: null,
  description: '',
  author: [],
})

// 当前编辑的图书 id（新增时为空）
const bookId = ref<number | null>(null)
// 详情回填中（编辑模式下防止用户提前操作）
const loadingDetail = ref(false)
// 提交中（防止重复提交）
const submitting = ref(false)
// 出版时间选择器 v-model（时间戳）
const pubTs = ref<number | string>('')

// 出版社下拉选项（从出版社列表接口拉取）
const publisherOptions = ref<Array<{ value: number; label: string }>>([])
// 作者多选选项（从作者列表接口拉取）
const authorOptions = ref<Array<{ value: number; label: string }>>([])

/**
 * 拉取出版社选项（传 paginate=false 获取全量数据，用于图书表单的出版社选择器）
 */
async function loadPublishers() {
  try {
    const res = await getPublisherList({ paginate: false })
    publisherOptions.value = res.data.map(item => ({ value: item.id, label: item.name }))
  }
  catch {
    // 选项加载失败不阻塞表单，错误提示已由 http 拦截器统一 toast
  }
}

/**
 * 拉取作者选项（传 paginate=false 获取全量数据，用于图书表单的作者多选器）
 */
async function loadAuthors() {
  try {
    const res = await getAuthorList({ paginate: false })
    authorOptions.value = res.data.map(item => ({ value: item.id, label: item.name }))
  }
  catch {
    // 选项加载失败不阻塞表单，错误提示已由请求层统一 toast
  }
}

/**
 * 页面加载：有 id 为编辑模式，拉取详情回填表单；同时加载出版社/作者选项
 */
onLoad((options) => {
  loadPublishers()
  loadAuthors()
  if (options?.id) {
    bookId.value = Number(options.id)
    uni.setNavigationBarTitle({ title: '编辑图书' })
    loadDetail(bookId.value)
  }
  else {
    uni.setNavigationBarTitle({ title: '新增图书' })
  }
})

/**
 * 拉取图书详情并回填表单
 * @param id 图书主键
 */
async function loadDetail(id: number) {
  loadingDetail.value = true
  try {
    const detail = await getBookDetail(id)
    form.value = {
      name: detail.name || '',
      isbn: detail.isbn || '',
      price: detail.price || '',
      pages: detail.pages != null ? String(detail.pages) : '',
      publication_time: detail.publication_time || '',
      publisher: detail.publisher ?? null,
      description: detail.description || '',
      author: detail.author || [],
    }
    // 出版时间回填为时间戳（wd-datetime-picker 的 modelValue 为毫秒时间戳）
    if (detail.publication_time) {
      const t = new Date(detail.publication_time.replace(' ', 'T'))
      pubTs.value = Number.isNaN(t.getTime()) ? '' : t.getTime()
    }
    else {
      pubTs.value = ''
    }
  }
  catch {
    // 错误提示已由 http 拦截器统一 toast
  }
  finally {
    loadingDetail.value = false
  }
}

/**
 * 出版时间选择确认：时间戳转 "YYYY-MM-DD HH:mm:ss" 存入表单
 * 注：wd-datetime-picker 的 confirm 事件 value 为毫秒时间戳，直接 new Date(ts) 即可
 * @param detail confirm 事件参数 { value: 毫秒时间戳 }
 */
function handlePubConfirm(detail: { value: number | string }) {
  const ts = Number(detail.value)
  if (Number.isNaN(ts) || ts <= 0) {
    form.value.publication_time = ''
    return
  }
  const d = new Date(ts)
  const pad = (n: number) => String(n).padStart(2, '0')
  form.value.publication_time = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/**
 * 校验规则：name / isbn / price 必填，price 需为非负数字，author 至少选 1 位
 * 注：author 为数组，wd-form 的 required 对空数组不生效，需用 validator
 */
const formRules: FormRules = {
  name: [{ required: true, message: '请输入书名' }],
  isbn: [{ required: true, message: '请输入ISBN' }],
  price: [
    { required: true, message: '请输入价格' },
    { required: false, pattern: /^\d+(\.\d{1,2})?$/, message: '价格需为非负数字，最多两位小数' },
  ],
  pages: [{ required: false, pattern: /^\d{0,6}$/, message: '页数需为 0-999999 的数字' }],
  author: [
    { validator: (value) => Array.isArray(value) && value.length > 0, message: '请选择至少一位作者' },
  ],
}

const formRef = ref<FormExpose>()

/**
 * 扫码识别 ISBN：调用系统扫码，清洗后校验（10/13 位数字），合法则自动填入表单
 * 注：H5 端 uni.scanCode 不可用，失败时统一提示，不阻断手动输入
 */
function handleScan() {
  uni.scanCode({
    // 仅识别条形码，避免误扫二维码（ISBN 印刷为条形码）
    scanType: ['barCode'],
    success: (res) => {
      // 清洗扫码结果：去除空白与连字符（部分条码携带分隔符）
      const isbn = (res.result || '').replace(/[\s-]/g, '')
      if (!/^\d{10}$|^\d{13}$/.test(isbn)) {
        uni.showToast({ title: '识别结果非有效ISBN', icon: 'none' })
        return
      }
      form.value.isbn = isbn
      uni.showToast({ title: 'ISBN 已自动填入', icon: 'success' })
    },
    fail: () => {
      // 用户取消扫码或当前平台不支持（如 H5），提示后仍可手动输入
      uni.showToast({ title: '扫码失败，请手动输入', icon: 'none' })
    },
  })
}

/**
 * 提交表单：校验通过后按「编辑/新增」分别调更新/新增接口
 */
function handleSubmit() {
  if (submitting.value) {
    return
  }
  formRef.value.validate().then(async () => {
    // 价格校验：确保为非负数字
    const priceNum = Number(form.value.price)
    if (Number.isNaN(priceNum) || priceNum < 0) {
      uni.showToast({ title: '价格需为非负数字', icon: 'none' })
      return
    }
    // 组装提交体：空字符串统一剔除，可选数字字段转 number
    const payload: IBookForm = {
      name: form.value.name,
      isbn: form.value.isbn,
      price: form.value.price,
      author: form.value.author,
    }
    if (form.value.publication_time) {
      payload.publication_time = form.value.publication_time
    }
    if (form.value.publisher != null) {
      payload.publisher = form.value.publisher
    }
    if (form.value.pages) {
      payload.pages = Number(form.value.pages)
    }
    if (form.value.description) {
      payload.description = form.value.description
    }
    submitting.value = true
    try {
      if (bookId.value) {
        await updateBook(bookId.value, payload)
        uni.showToast({ title: '保存成功', icon: 'success' })
      }
      else {
        await createBook(payload)
        uni.showToast({ title: '新增成功', icon: 'success' })
      }
      // 通知列表页刷新
      uni.$emit('book:changed')
      setTimeout(() => {
        uni.navigateBack()
      }, 600)
    }
    catch {
      // 提交失败（如 ISBN 重复）提示已由 http 拦截器统一 toast
    }
    finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pt-safe pb-28">
    <wd-form ref="formRef" :model="form" :rules="formRules">
      <!-- 基本信息卡片 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <wd-input
          v-model="form.name"
          label="书名"
          placeholder="请输入书名"
          required
          border
        />
        <wd-input
          v-model="form.isbn"
          label="ISBN"
          placeholder="请输入ISBN"
          required
          border
        >
          <!-- 扫码按钮：扫描图书条形码自动填入 ISBN -->
          <template #suffix>
            <view
              class="flex items-center gap-0.5 px-1 text-primary active:opacity-70"
              @click.stop="handleScan"
            >
              <text class="i-carbon-scan text-base leading-none" />
              <text class="text-sm">扫码</text>
            </view>
          </template>
        </wd-input>
        <wd-input
          v-model="form.price"
          label="价格"
          placeholder="请输入价格（元）"
          type="digit"
          required
          border
        />
        <wd-select-picker
          v-model="form.publisher"
          type="radio"
          label="出版社"
          placeholder="请选择出版社"
          :columns="publisherOptions"
          border
        />
        <wd-select-picker
          v-model="form.author"
          type="checkbox"
          label="作者"
          title="选择作者"
          placeholder="请选择作者"
          :columns="authorOptions"
          border
        />
        <wd-input
          v-model="form.pages"
          label="页数"
          placeholder="请输入页数"
          type="number"
          border
        />
        <wd-datetime-picker
          v-model="pubTs"
          type="datetime"
          label="出版时间"
          title="选择出版时间"
          placeholder="请选择出版时间"
          @confirm="handlePubConfirm"
        />
      </view>

      <!-- 内容简介卡片 -->
      <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
        <wd-textarea
          v-model="form.description"
          label="内容简介"
          placeholder="请输入内容简介"
          :maxlength="500"
          show-word-limit
          :autosize="false"
          rows="4"
        />
      </view>
    </wd-form>

    <!-- 底部固定保存按钮 -->
    <view class="fixed inset-x-0 bottom-0 z-10 bg-white px-4 pt-3 shadow-sm pb-safe">
      <wd-button
        size="large"
        block
        type="primary"
        :loading="submitting || loadingDetail"
        :disabled="submitting || loadingDetail"
        @click="handleSubmit"
      >
        保 存
      </wd-button>
    </view>
  </view>
</template>
