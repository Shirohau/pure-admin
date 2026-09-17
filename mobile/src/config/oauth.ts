/**
 * 第三方授权登录前端配置（7 平台：微信 / 企业微信 / QQ / 支付宝 / 微博 / GitHub / Gitee）
 *
 * 参数来源优先级说明：
 * 1. 优先调用后端接口 `GET /api/oauth2/get_config/?platform=xxx&kind=PC|M` 获取平台配置
 *    （后端 extends/oauth2/config.py 中的 PLATFORM_CONFIGS，为权威配置源，含 appid / authorize_uri 等）；
 * 2. 后端返回失败时（如平台未配置），回退使用本文件内的占位配置；
 * 3. 真实上线前，请将后端 config.py 中各平台占位符替换为真实值，
 *    并在各开放平台后台配置网页授权域名（H5）与业务域名（小程序）。
 */

/** 是否在登录页展示「第三方授权登录」入口 */
export const OAUTH_AUTH_ENABLED = true

// ===== 平台标识（与后端 extends/oauth2/models.py PLATFORM_CHOICES 保持一致）=====

/** 微信 */
export const OAUTH_PLATFORM_WECHAT = 'wechat'
/** 企业微信 */
export const OAUTH_PLATFORM_WECOM = 'wecom'
/** QQ */
export const OAUTH_PLATFORM_QQ = 'qq'
/** 支付宝 */
export const OAUTH_PLATFORM_ALIPAY = 'alipay'
/** 微博 */
export const OAUTH_PLATFORM_WEIBO = 'weibo'
/** GitHub */
export const OAUTH_PLATFORM_GITHUB = 'github'
/** Gitee */
export const OAUTH_PLATFORM_GITEE = 'gitee'

/** 平台类型：PC=H5 网页授权，M=小程序 */
export const OAUTH_KIND_PC = 'PC'
export const OAUTH_KIND_M = 'M'

/**
 * 单平台展示与前端占位配置
 *
 * 说明：appId / agentId 仅为后端未返回配置时的降级占位，真实值以后端 get_config 为准；
 * 占位符统一以 `your_` 开头，前端据此判断「未配置」并给出降级提示。
 */
export interface IOAuthPlatform {
  /** 平台标识（与后端一致，用于 get_config / callback 接口） */
  platform: string
  /** 平台名称（按钮提示用） */
  title: string
  /** 品牌图标（Iconify 图标名，与 web 端 views/login/utils/enums.ts thirdParty.icon 对齐，用于定位 oauth-icon-{platform} 样式） */
  icon: string
  /** 品牌色（与 web 端 enums.ts 品牌色一致，用于配置层标识） */
  color: string
  /** 授权 URL 中应用 ID 的参数名（微信/企微=appid，支付宝=app_id，其余=client_id） */
  idParamName: 'appid' | 'app_id' | 'client_id'
  /** 占位 appid / client_id（后端未配置时的降级值） */
  appId?: string
  /** 占位 agentid（仅企业微信需要） */
  agentId?: string
  /** 默认授权地址（后端 get_config 优先返回） */
  authorizeUri: string
  /** 授权 scope */
  scope?: string
  /** 是否企业微信（授权 URL 构造特殊：login_type=CorpApp + agentid） */
  isWecom?: boolean
  /** 授权 URL 是否以 #wechat_redirect 结尾（微信网页授权必须） */
  wechatRedirect?: boolean
  /** 小程序端是否展示（当前仅微信小程序支持 uni.login 取 code） */
  mpEnabled?: boolean
}

/**
 * 第三方平台列表（登录页图标行渲染顺序，与 web 端 views/login/utils/enums.ts thirdParty 对齐）
 */
export const OAUTH_PLATFORM_LIST: IOAuthPlatform[] = [
  {
    platform: OAUTH_PLATFORM_WECHAT,
    title: '微信',
    icon: 'ri:wechat-fill',
    color: '#07C160',
    idParamName: 'appid',
    appId: 'your_wechat_mp_appid',
    authorizeUri: 'https://open.weixin.qq.com/connect/oauth2/authorize',
    scope: 'snsapi_userinfo',
    wechatRedirect: true,
    mpEnabled: true,
  },
  {
    platform: OAUTH_PLATFORM_WECOM,
    title: '企业微信',
    icon: 'tdesign:logo-wecom',
    color: '#397BFF',
    idParamName: 'appid',
    appId: 'your_wecom_corpid',
    agentId: 'your_wecom_agentid',
    authorizeUri: 'https://login.work.weixin.qq.com/wwlogin/sso/login',
    scope: 'snsapi_login',
    isWecom: true,
  },
  {
    platform: OAUTH_PLATFORM_QQ,
    title: 'QQ',
    icon: 'ri:qq-fill',
    color: '#12B7F5',
    idParamName: 'client_id',
    appId: 'your_qq_appid',
    authorizeUri: 'https://graph.qq.com/oauth2.0/authorize',
    scope: 'get_user_info',
  },
  {
    platform: OAUTH_PLATFORM_ALIPAY,
    title: '支付宝',
    icon: 'ri:alipay-fill',
    color: '#1677FF',
    idParamName: 'app_id',
    appId: 'your_alipay_appid',
    authorizeUri: 'https://openauth.alipay.com/oauth2/publicAppAuthorize.htm',
    scope: 'auth_base',
  },
  {
    platform: OAUTH_PLATFORM_WEIBO,
    title: '微博',
    icon: 'ri:weibo-fill',
    color: '#E6162D',
    idParamName: 'client_id',
    appId: 'your_weibo_app_key',
    authorizeUri: 'https://api.weibo.com/oauth2/authorize',
  },
  {
    platform: OAUTH_PLATFORM_GITHUB,
    title: 'GitHub',
    icon: 'ri:github-fill',
    color: '#C71D23',
    idParamName: 'client_id',
    appId: 'your_github_client_id',
    authorizeUri: 'https://github.com/login/oauth/authorize',
    scope: 'user',
  },
  {
    platform: OAUTH_PLATFORM_GITEE,
    title: 'Gitee',
    icon: 'ri:gitee-fill',
    color: '#C71D23',
    idParamName: 'client_id',
    appId: 'your_gitee_client_id',
    authorizeUri: 'https://gitee.com/oauth/authorize',
  },
]

/**
 * 授权上下文存储 key
 *
 * H5 授权跳转会丢失 URL 参数与登录页路由参数（redirect），
 * 因此授权前将 state / platform / redirect 统一暂存本地，回调时读取校验与回跳。
 */
export const OAUTH_CONTEXT_KEY = 'oauth_auth_context'

/** 授权上下文数据结构 */
export interface IOAuthContext {
  /** CSRF 防护随机串（回调时比对，防止跨站授权攻击） */
  state: string
  /** 平台标识（回调时据此调用对应平台的 callback 接口） */
  platform: string
  /** 授权前登录页路由参数 redirect（授权成功后的回跳地址，可为空） */
  redirect: string
}

/**
 * 根据平台标识获取平台展示配置
 * @param platform 平台标识（如 wechat）
 * @returns 平台配置，未匹配返回 undefined
 */
export function getOAuthPlatform(platform: string): IOAuthPlatform | undefined {
  return OAUTH_PLATFORM_LIST.find(item => item.platform === platform)
}
