<script lang="ts" setup>
import type { FormExpose, FormRules } from 'wot-design-uni/components/wd-form/types'
import { createAuthor, getAuthorDetail, updateAuthor } from '@/api/author'
import type { IAuthorForm } from '@/api/author'

definePage({
  style: {
    navigationBarTitleText: '作者表单',
  },
})

/** 编辑目标 id（无 id 为新增模式） */
const authorId = ref<number | null>(null)

// 表单数据（字段与后端 AuthorModel 对齐；
// age 用字符串承接 wd-input 数字输入框的输入值，提交时再转 number）
const form = ref<{
  name: string
  gender: string
  age: string
  birth_date: string
  biography: string
  book: number[]
}>({
  name: '',
  gender: '',
  age: '',
  birth_date: '',
  biography: '',
  book: [],
})

// 出生日期时间戳（wd-datetime-picker 的 v-model 为时间戳，确认后转 YYYY-MM-DD 存入表单）
const birthTs = ref<number | string>('')
// 提交按钮加载状态（防止重复提交）
const submitting = ref(false)
// 表单实例（用于触发校验）
const formRef = ref<FormExpose>()

// 表单校验规则：姓名必填，年龄可选但必须是数字
// （FormItemRule 类型要求 required 必填，可选项须显式置 false）
const formRules: FormRules = {
  name: [{ required: true, message: '请输入作者姓名' }],
  age: [{ required: false, pattern: /^\d{0,3}$/, message: '年龄需为 0-999 的数字' }],
}

/**
 * 页面加载：解析路由参数 id 判断新增/编辑模式
 * 编辑模式拉取详情回填表单，并动态修改导航栏标题
 */
onLoad((options) => {
  if (options?.id) {
    authorId.value = Number(options.id)
    uni.setNavigationBarTitle({ title: '编辑作者' })
    loadDetail(authorId.value)
  }
  else {
    uni.setNavigationBarTitle({ title: '新增作者' })
  }
})

/**
 * 拉取作者详情并回填表单
 * @param id 作者主键
 */
async function loadDetail(id: number) {
  try {
    const data = await getAuthorDetail(id)
    form.value = {
      name: data.name,
      gender: data.gender || '',
      age: data.age != null ? String(data.age) : '',
      birth_date: data.birth_date || '',
      biography: data.biography || '',
      book: data.book || [],
    }
    // 出生日期回填为时间戳（编辑模式下日期选择器展示当前值）
    if (data.birth_date) {
      const ts = new Date(data.birth_date.replace(/-/g, '/')).getTime()
      birthTs.value = Number.isNaN(ts) ? '' : ts
    }
  }
  catch {
    // 加载失败提示已由 http 拦截器统一 toast，返回上一页
    setTimeout(() => uni.navigateBack(), 800)
  }
}

/**
 * 日期选择器确认：时间戳转 YYYY-MM-DD 存入表单
 * @param detail 确认事件参数（value 为时间戳）
 */
function handleBirthConfirm(detail: { value: number | string | (number | string)[] }) {
  const ts = Array.isArray(detail.value) ? detail.value[0] : detail.value
  if (typeof ts === 'number' && !Number.isNaN(ts)) {
    const date = new Date(ts)
    const mm = String(date.getMonth() + 1).padStart(2, '0')
    const dd = String(date.getDate()).padStart(2, '0')
    form.value.birth_date = `${date.getFullYear()}-${mm}-${dd}`
  }
}

/**
 * 提交表单（新增/编辑共用）
 * 校验通过后调接口，成功 toast 并广播数据变更事件，返回上一页
 */
async function handleSubmit() {
  if (submitting.value) {
    return
  }
  const { valid } = await formRef.value?.validate() || { valid: false }
  if (!valid) {
    return
  }
  submitting.value = true
  try {
    // 组装提交体：空串/空值剔除，age 转 number
    const payload: IAuthorForm = {
      name: form.value.name.trim(),
      gender: form.value.gender || undefined,
      age: form.value.age ? Number(form.value.age) : undefined,
      birth_date: form.value.birth_date || undefined,
      biography: form.value.biography?.trim() || undefined,
      book: [],
    }
    if (authorId.value) {
      await updateAuthor(authorId.value, payload)
      uni.showToast({ title: '保存成功', icon: 'success' })
    }
    else {
      await createAuthor(payload)
      uni.showToast({ title: '新增成功', icon: 'success' })
    }
    // 广播数据变更：列表页 onShow 时据此刷新
    uni.$emit('author:changed')
    setTimeout(() => uni.navigateBack(), 600)
  }
  catch {
    // 失败提示已由 http 拦截器统一 toast
  }
  finally {
    submitting.value = false
  }
}
</script>

<template>
  <view class="min-h-screen bg-[#f6f7fb] pb-28 pt-safe">
    <!-- 表单卡片 -->
    <view class="mx-4 mt-4 rounded-xl bg-white p-5 shadow-sm">
      <wd-form ref="formRef" :model="form" :rules="formRules">
        <!-- 作者姓名（必填） -->
        <wd-form-item prop="name">
          <wd-input
            v-model="form.name"
            placeholder="请输入作者姓名"
            clearable
            :border="false"
            prefix-icon="user"
            label="姓名"
            required
          />
        </wd-form-item>

        <!-- 性别：单选（与后端字典取值一致：男/女） -->
        <wd-form-item prop="gender" label="性别">
          <wd-radio-group v-model="form.gender">
            <wd-radio value="男">
              男
            </wd-radio>
            <wd-radio value="女">
              女
            </wd-radio>
          </wd-radio-group>
        </wd-form-item>

        <!-- 年龄 -->
        <wd-form-item prop="age">
          <wd-input
            v-model="form.age"
            type="number"
            placeholder="请输入年龄"
            clearable
            :border="false"
            prefix-icon="order"
            label="年龄"
          />
        </wd-form-item>

        <!-- 出生日期：组件自带 cell 触发，点击弹出日期选择器（type=date，确认后格式化 YYYY-MM-DD） -->
        <wd-datetime-picker
          v-model="birthTs"
          type="date"
          label="出生日期"
          title="选择出生日期"
          placeholder="请选择出生日期"
          @confirm="handleBirthConfirm"
        />

        <!-- 简介 -->
        <wd-form-item prop="biography" label="简介">
          <wd-textarea
            v-model="form.biography"
            placeholder="请输入作者简介"
            :maxlength="500"
            show-word-limit
            :border="false"
          />
        </wd-form-item>
      </wd-form>
    </view>

    <!-- 底部保存按钮：固定贴底（含安全区） -->
    <view class="fixed inset-x-0 bottom-0 z-10 bg-white px-4 pt-3 shadow-sm pb-safe">
      <wd-button
        size="large"
        block
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        保 存
      </wd-button>
    </view>
  </view>
</template>
