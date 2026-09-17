<script lang="ts" setup>
import type { FormExpose, FormRules } from 'wot-design-uni/components/wd-form/types'
import { createPublisher, getPublisherDetail, updatePublisher, type IPublisherForm } from '@/api/publisher'

definePage({
  style: {
    navigationBarTitleText: '出版社表单',
  },
})

/**
 * 表单数据（宽松类型：数值/文本统一用字符串承接 wd-input 输入，提交时转后端所需格式）
 * 字段与后端 PublisherSerializer / web 端表单对齐，book 关联图书暂不维护。
 */
const form = ref<{
  name: string
  province: string
  city: string
  district: string
  address: string
  phone: string
  email: string
  website: string
  book: number[]
}>({
  name: '',
  province: '',
  city: '',
  district: '',
  address: '',
  phone: '',
  email: '',
  website: '',
  book: [],
})

// 当前编辑的出版社 id（新增时为空）
const publisherId = ref<number | null>(null)
// 详情回填中（编辑模式下防止用户提前操作）
const loadingDetail = ref(false)
// 提交中（防止重复提交）
const submitting = ref(false)

/**
 * 页面加载：有 id 为编辑模式，拉取详情回填表单
 */
onLoad((options) => {
  if (options?.id) {
    publisherId.value = Number(options.id)
    uni.setNavigationBarTitle({ title: '编辑出版社' })
    loadDetail(publisherId.value)
  }
  else {
    uni.setNavigationBarTitle({ title: '新增出版社' })
  }
})

/**
 * 拉取出版社详情并回填表单
 * @param id 出版社主键
 */
async function loadDetail(id: number) {
  loadingDetail.value = true
  try {
    const detail = await getPublisherDetail(id)
    form.value = {
      name: detail.name || '',
      province: detail.province || '',
      city: detail.city || '',
      district: detail.district || '',
      address: detail.address || '',
      phone: detail.phone || '',
      email: detail.email || '',
      website: detail.website || '',
      book: [],
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
 * 校验规则：
 * - name / province / city / district / address 必填
 * - phone 可选，手机号格式校验
 * - email 可选，邮箱格式校验
 * - website 可选，URL 格式校验
 */
const formRules: FormRules = {
  name: [{ required: true, message: '请输入出版社名称' }],
  province: [{ required: true, message: '请输入省份' }],
  city: [{ required: true, message: '请输入城市' }],
  district: [{ required: true, message: '请输入区县' }],
  address: [{ required: true, message: '请输入详细地址' }],
  phone: [{ required: false, pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }],
  email: [{ required: false, pattern: /^\S+@\S+\.\S+$/, message: '邮箱格式不正确' }],
  website: [{ required: false, pattern: /^https?:\/\/.+/, message: '网址格式不正确' }],
}

const formRef = ref<FormExpose>()

/**
 * 提交表单：校验通过后按「编辑/新增」分别调更新/新增接口
 */
function handleSubmit() {
  if (submitting.value) {
    return
  }
  formRef.value.validate().then(async () => {
    submitting.value = true
    // 组装提交体：空字符串统一剔除（后端 partial 更新不受影响）
    const payload: IPublisherForm = {
      name: form.value.name,
      book: [],
    }
    for (const key of ['province', 'city', 'district', 'address', 'phone', 'email', 'website'] as const) {
      if (form.value[key]) {
        payload[key] = form.value[key]
      }
    }
    try {
      if (publisherId.value) {
        await updatePublisher(publisherId.value, payload)
        uni.showToast({ title: '保存成功', icon: 'success' })
      }
      else {
        await createPublisher(payload)
        uni.showToast({ title: '新增成功', icon: 'success' })
      }
      // 通知列表页刷新
      uni.$emit('publisher:changed')
      setTimeout(() => {
        uni.navigateBack()
      }, 600)
    }
    catch {
      // 提交失败（如名称重复）提示已由 http 拦截器统一 toast
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
          label="出版社名称"
          placeholder="请输入出版社名称"
          required
          border
        />
        <wd-input
          v-model="form.province"
          label="省份"
          placeholder="请输入省份"
          required
          border
        />
        <wd-input
          v-model="form.city"
          label="城市"
          placeholder="请输入城市"
          required
          border
        />
        <wd-input
          v-model="form.district"
          label="区县"
          placeholder="请输入区县"
          required
          border
        />
        <wd-input
          v-model="form.address"
          label="详细地址"
          placeholder="请输入详细地址"
          required
          border
        />
        <wd-input
          v-model="form.phone"
          label="联系电话"
          placeholder="请输入联系电话"
          border
        />
        <wd-input
          v-model="form.email"
          label="邮箱"
          placeholder="请输入邮箱"
          border
        />
        <wd-input
          v-model="form.website"
          label="官网网址"
          placeholder="请输入官网网址"
          border
        />
      </view>
    </wd-form>

    <!-- 底部固定保存按钮 -->
    <view class="fixed inset-x-0 bottom-0 z-10 bg-white px-4 pt-3 shadow-sm pb-safe">
      <wd-button
        size="large"
        block
        type="primary"
        :loading="submitting"
        :disabled="loadingDetail"
        @click="handleSubmit"
      >
        保 存
      </wd-button>
    </view>
  </view>
</template>
