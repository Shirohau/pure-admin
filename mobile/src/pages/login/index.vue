<script lang="ts" setup>
import type { FormExpose, FormRules } from 'wot-design-uni/components/wd-form/types'
import type { IOAuthConfig } from '@/api/types/login'
import { getOAuthConfig } from '@/api/login'
import {
  OAUTH_CONTEXT_KEY,
  OAUTH_KIND_M,
  OAUTH_KIND_PC,
  OAUTH_PLATFORM_LIST,
} from '@/config/oauth'
import type { IOAuthContext, IOAuthPlatform } from '@/config/oauth'
import { useTokenStore } from '@/store/token'
import { HOME_PAGE } from '@/utils'

definePage({
  style: {
    navigationStyle: 'custom',
    navigationBarTitleText: '登录',
  },
  // 免登录白名单：登录页本身不需要登录即可访问（与 src/router/interceptor.ts 路由拦截器配对使用）
  excludeLoginPath: true,
})

// 登录表单数据（演示项目：默认填入演示账号，访客打开登录页即可直接体验；输入框仍可编辑/清空）
const loginForm = ref({
  username: 'superadmin',
  password: 'admin123456',
})
// 登录按钮加载状态（防止重复提交）
const loading = ref(false)
// 第三方授权登录加载状态（防止重复点击）
const oauthLoading = ref(false)
// 登录成功后的跳转地址（默认首页，由 toLoginPage 传入 redirect 参数）
const redirect = ref('')

const tokenStore = useTokenStore()
// 表单实例（用于触发校验）
const formRef = ref<FormExpose>()

// 登录页展示的第三方平台列表：H5 展示全部 7 平台，小程序端仅展示支持 uni.login 的平台（当前为微信）
const visiblePlatforms = computed(() => {
  // #ifdef MP-WEIXIN
  return OAUTH_PLATFORM_LIST.filter(item => item.mpEnabled)
  // #endif
  // #ifndef MP-WEIXIN
  return OAUTH_PLATFORM_LIST
  // #endif
})

// 表单校验规则
const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名 / 邮箱 / 手机号' }],
  password: [{ required: true, message: '请输入密码' }],
}

// 读取路由参数：如 /pages/login/index?redirect=%2Fpages%2Findex%2Findex
onLoad((options) => {
  if (options?.redirect) {
    redirect.value = decodeURIComponent(options.redirect)
  }

  // H5 第三方授权回调：授权平台重定向回登录页并携带 code/state 参数
  if (options?.code) {
    handleOAuthCallback(options.code, options.state)
  }
})

/**
 * 生成随机 state 串（CSRF 防护：第三方授权回调时比对，防止跨站授权攻击）
 * @returns 随机 state 字符串
 */
function generateState() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

/**
 * 提交登录
 *
 * 表单校验通过后调用登录接口；登录成功后跳转到目标页面（默认首页），
 * 登录失败的错误提示由 http 拦截器统一 toast，此处无需重复提示。
 */
async function handleLogin() {
  if (loading.value) {
    return
  }
  const { valid } = await formRef.value?.validate() || { valid: false }
  if (!valid) {
    return
  }
  loading.value = true
  try {
    await tokenStore.login({
      username: loginForm.value.username.trim(),
      password: loginForm.value.password,
    })
    // 等待成功 toast 展示后再跳转，避免跳转打断提示
    setTimeout(() => {
      uni.reLaunch({ url: redirect.value || HOME_PAGE })
    }, 800)
  }
  catch {
    // 错误提示已由 http 层统一处理
  }
  finally {
    loading.value = false
  }
}

/**
 * 第三方授权登录入口（按端分发）
 *
 * - H5：跳转平台网页授权链接，授权后平台重定向回登录页（携带 code），由 onLoad 接管换取登录态
 * - 小程序：仅微信平台支持（uni.login 获取 code 后直连后端换取登录态，无跳转）
 *
 * @param item 平台配置（platform / title / 授权地址等）
 */
function handleThirdPartyLogin(item: IOAuthPlatform) {
  if (oauthLoading.value) {
    return
  }
  // #ifdef H5
  handleOAuthLoginH5(item)
  // #endif
  // #ifdef MP-WEIXIN
  // 小程序端仅微信平台展示（mpEnabled=true），走 uni.login 流程
  handleWechatLoginMp(item)
  // #endif
}

/**
 * 组装第三方平台 H5 授权 URL（按平台类型区分构造方式，与 web 端 thirdLogin 保持一致）
 *
 * - 企业微信：构造型登录（login_type=CorpApp + appid + agentid）
 * - 微信：网页授权（appid + #wechat_redirect）
 * - 其余平台：标准 OAuth2（response_type=code + 平台对应应用 ID 参数名）
 *
 * @param item 平台配置
 * @param runtime 运行时参数（应用 ID / agentid / 授权地址，来自后端 get_config 或前端占位）
 * @param state CSRF 随机串
 * @returns 完整授权 URL
 */
function buildAuthUrl(
  item: IOAuthPlatform,
  runtime: { appid: string, agentid: string, authorizeUri: string },
  state: string,
) {
  // 回调地址固定为当前 H5 登录页（平台授权后携带 code/state 重定向回来）
  const redirectUri = `${location.origin}${location.pathname}#/pages/login/index`
  const enc = encodeURIComponent

  // 企业微信：构造型登录，无 response_type/scope，必须带 login_type=CorpApp
  if (item.isWecom) {
    return `${runtime.authorizeUri}?login_type=CorpApp&appid=${enc(runtime.appid)}&agentid=${enc(runtime.agentid)}&redirect_uri=${enc(redirectUri)}&state=${state}`
  }

  // 标准 OAuth2：应用 ID 参数名按平台区分（appid / app_id / client_id）
  let url = `${runtime.authorizeUri}?${item.idParamName}=${enc(runtime.appid)}&redirect_uri=${enc(redirectUri)}&response_type=code`
  if (item.scope) {
    url += `&scope=${item.scope}`
  }
  url += `&state=${state}`
  // 微信网页授权要求 state 后追加 #wechat_redirect
  if (item.wechatRedirect) {
    url += '#wechat_redirect'
  }
  return url
}

/**
 * H5 第三方网页授权登录（通用流程，支持全部平台）
 *
 * 流程：获取平台配置（优先后端 get_config，失败回退前端占位配置）→ 组装授权 URL → 跳转平台授权页
 * 授权成功后平台重定向回登录页（URL 追加 ?code=xxx&state=yyy），由 onLoad → handleOAuthCallback 完成登录。
 *
 * @param item 平台配置
 */
async function handleOAuthLoginH5(item: IOAuthPlatform) {
  oauthLoading.value = true
  try {
    // 1. 优先从后端获取平台配置（后端支持后返回真实 appid / 授权地址）
    let appid = ''
    let agentid = item.agentId || ''
    let authorizeUri = item.authorizeUri
    try {
      const config: IOAuthConfig = await getOAuthConfig(item.platform, OAUTH_KIND_PC)
      appid = config.appid || config.client_id || config.app_id || ''
      agentid = config.agentid || item.agentId || ''
      authorizeUri = config.authorize_uri || item.authorizeUri
    }
    catch {
      // 后端未返回配置（如平台未在 PLATFORM_CONFIGS 注册）：回退前端占位配置
      appid = item.appId || ''
    }

    // 2. 校验应用 ID（占位符视为未配置，给出降级提示，不影响密码登录）
    if (!appid || appid.startsWith('your_')) {
      uni.showToast({ title: `${item.title}登录暂未开放，敬请期待`, icon: 'none' })
      return
    }

    // 3. 暂存授权上下文：state（CSRF 校验）+ platform（回调时确定平台）+ redirect（授权跳转会丢失 URL 参数）
    const state = generateState()
    const context: IOAuthContext = {
      state,
      platform: item.platform,
      redirect: redirect.value,
    }
    uni.setStorageSync(OAUTH_CONTEXT_KEY, JSON.stringify(context))

    // 4. 组装授权 URL 并跳转
    const authUrl = buildAuthUrl(item, { appid, agentid, authorizeUri }, state)
    window.location.href = authUrl
  }
  finally {
    oauthLoading.value = false
  }
}

/**
 * 小程序微信授权登录
 *
 * 流程：uni.login 获取临时 code → 直连后端 callback（kind=M）→ 后端 jscode2session 换 openid 完成登录。
 * 小程序与 H5 差异：无需跳转授权页，code 由 uni.login 直接返回。
 *
 * @param item 平台配置（当前仅微信平台会进入此分支）
 */
function handleWechatLoginMp(item: IOAuthPlatform) {
  oauthLoading.value = true
  uni.login({
    provider: 'weixin',
    success: async (res) => {
      // 未取到 code（如用户拒绝授权）给出提示
      if (!res.code) {
        oauthLoading.value = false
        uni.showToast({ title: '微信授权失败，请重试', icon: 'none' })
        return
      }
      try {
        await tokenStore.oauthLogin(item.platform, OAUTH_KIND_M, res.code)
        // 等待成功 toast 展示后再跳转
        setTimeout(() => {
          uni.reLaunch({ url: redirect.value || HOME_PAGE })
        }, 800)
      }
      catch {
        // 后端未支持或授权失败：http 层已隐藏错误提示，此处统一降级提示
        uni.showToast({ title: '微信登录失败，请稍后重试', icon: 'none' })
      }
      finally {
        oauthLoading.value = false
      }
    },
    fail: () => {
      // 用户取消授权或获取 code 失败
      oauthLoading.value = false
      uni.showToast({ title: '已取消微信授权', icon: 'none' })
    },
  })
}

/**
 * 处理 H5 第三方授权回调（登录页 onLoad 检测到 code 参数时调用）
 *
 * 读取授权前暂存的上下文确定平台；用 code 向后端换取登录态；
 * 成功后跳转：优先授权前暂存的 redirect，其次路由参数 redirect，最后首页。
 *
 * @param code 第三方授权码
 * @param state 第三方回调携带的 state（CSRF 校验）
 */
async function handleOAuthCallback(code: string, state?: string) {
  if (oauthLoading.value) {
    return
  }
  oauthLoading.value = true
  try {
    // 1. 读取并清理授权前暂存的上下文（state / platform / redirect）
    const raw = uni.getStorageSync(OAUTH_CONTEXT_KEY)
    uni.removeStorageSync(OAUTH_CONTEXT_KEY)
    let context: IOAuthContext | null = null
    try {
      context = raw ? JSON.parse(raw) : null
    }
    catch {
      context = null
    }

    // 2. 校验 state 防跨站授权（无暂存上下文或未携带 state 时跳过校验，兼容直接访问场景）
    const isStateValid = !context || !state || context.state === state
    if (!isStateValid || !context?.platform) {
      uni.showToast({ title: '授权校验失败，请重试', icon: 'none' })
      return
    }

    // 3. 用 code 向后端换取登录态（platform 由授权前暂存决定）
    await tokenStore.oauthLogin(context.platform, OAUTH_KIND_PC, code)

    // 4. 等待成功 toast 展示后再跳转：优先授权前暂存的回跳地址
    setTimeout(() => {
      uni.reLaunch({ url: context?.redirect || redirect.value || HOME_PAGE })
    }, 800)
  }
  catch {
    // 后端未支持或授权失败：http 层已隐藏错误提示，此处统一降级提示
    uni.showToast({ title: '第三方登录失败，请稍后重试', icon: 'none' })
  }
  finally {
    oauthLoading.value = false
  }
}
</script>

<template>
  <!-- 登录页：自定义导航栏，全屏背景；一屏自适应布局（flex 弹性 + vh 相对单位，任何屏幕尺寸均无滚动条） -->
  <view class="login-page flex flex-col bg-white px-8 pt-safe">
    <!-- 弹性主区：品牌区 + 登录表单 + 第三方登录整体垂直居中（内容不足一屏时留白均匀分布在上下两侧，超出一屏时由外层弹性布局收进一屏） -->
    <view class="flex flex-1 flex-col justify-center">
      <!-- 顶部品牌区：顶部留白用 vh 相对单位，随屏幕高度缩放 -->
      <view class="flex flex-col items-center pt-[3vh]">
        <image src="/static/logo.svg" alt="logo" class="h-20 w-20" />
        <view class="mt-3 text-2xl text-[#2a2a2a] font-bold">
          欢迎登录
        </view>
        <view class="mt-1 text-sm text-[#999]">
          登录后开启完整体验
        </view>
      </view>

      <!-- 登录表单区 -->
      <wd-form ref="formRef" :model="loginForm" :rules="loginRules" class="mt-6">
        <wd-form-item prop="username" :border="false">
          <wd-input
            v-model="loginForm.username"
            placeholder="请输入用户名 / 邮箱 / 手机号"
            clearable
            :border="false"
            prefix-icon="user"
          />
        </wd-form-item>
        <wd-form-item prop="password" :border="false">
          <wd-input
            v-model="loginForm.password"
            placeholder="请输入密码"
            show-password
            :border="false"
            prefix-icon="lock-on"
            @confirm="handleLogin"
          />
        </wd-form-item>
        <wd-button
          class="mt-4"
          size="large"
          block
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </wd-button>
      </wd-form>

      <!-- 第三方授权登录分隔区 -->
      <view class="mt-4 flex items-center gap-3">
        <view class="h-px flex-1 bg-[#eee]" />
        <text class="text-xs text-[#bbb]">其他登录方式</text>
        <view class="h-px flex-1 bg-[#eee]" />
      </view>

      <!-- 第三方平台图标行：H5 展示全部 7 平台，小程序端仅展示支持 uni.login 的平台；
          允许自动换行（flex-wrap），窄屏下图标折为两行展示，不撑高页面 -->
      <view class="mt-3 flex flex-wrap items-center justify-center gap-x-4 gap-y-3">
        <view
          v-for="item in visiblePlatforms"
          :key="item.platform"
          class="flex flex-col items-center"
          @click="handleThirdPartyLogin(item)"
        >
          <!-- 品牌图标（SVG data URI 背景图，源自 Iconify，与 web 端 IconifyIconOnline 图标同源；hover 放大反馈） -->
          <view
            class="oauth-icon"
            :class="`oauth-icon-${item.platform}`"
            :style="{ opacity: oauthLoading ? 0.6 : 1 }"
            hover-class="oauth-icon-hover"
          />
          <text class="mt-1 text-xs text-[#999]">{{ item.title }}</text>
        </view>
      </view>
    </view>

    <!-- 底部提示：固定贴底，间距从宽收紧，为小屏腾出空间 -->
    <view class="pb-4 pt-2 text-center text-xs text-[#bbb]">
      未注册账号请联系管理员开通
    </view>
  </view>
</template>

<style lang="scss" scoped>
.login-page {
  background: linear-gradient(180deg, #f8faff 0%, #ffffff 40%);
  // 一屏高度：100vh 兜底 + 100dvh 动态视口（H5 移动端地址栏收起/展开时保持一屏，避免出现滚动条或底部留白）
  height: 100vh;
  height: 100dvh;
  // 兜底防溢出：极端尺寸下优先保证无滚动条（内容按紧凑间距设计，正常手机尺寸不会触发裁切）
  overflow: hidden;
}

// 图标点击反馈：轻微放大（配合 hover-class 生效）
.oauth-icon-hover {
  transform: scale(1.1);
}
</style>

<!-- 非 scoped 样式：H5 端将页面容器高度锁定为视口并禁止滚动，
     避免 html/body 与页面容器同时出现滚动条（双滚动条防护） -->
<style lang="scss">
/* #ifdef H5 */
page {
  height: 100%;
  overflow: hidden;
}
/* #endif */
</style>
