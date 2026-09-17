import type { IAuthLoginRes, IOAuthConfig, IOAuthLoginParams } from './types/login'
import { http } from '@/http/http'

/**
 * 登录表单
 */
export interface ILoginForm {
  /** 登录名：支持用户名 / 邮箱 / 手机号 */
  username: string
  /** 密码 */
  password: string
}

/**
 * 用户登录
 *
 * 后端接口：POST /api/token/（extends/jwt/views.py CustomTokenObtainPairView）
 * 成功返回令牌 + 用户信息（一次返回，无需再请求用户信息接口）
 *
 * @param loginForm 登录表单（用户名/邮箱/手机号 + 密码）
 * @returns 登录结果（accessToken / refreshToken / expires / 用户信息）
 */
export function login(loginForm: ILoginForm) {
  return http.post<IAuthLoginRes>('/api/token/', loginForm)
}

/**
 * 刷新 token
 *
 * 后端接口：POST /api/token/refresh/（CustomTokenRefreshView）
 * 后端已开启 ROTATE_REFRESH_TOKENS，刷新成功后旧 refreshToken 自动拉黑
 *
 * @param refreshToken 刷新令牌
 * @returns 新的令牌 + 用户信息
 */
export function refreshToken(refreshToken: string) {
  return http.post<IAuthLoginRes>('/api/token/refresh/', { refresh: refreshToken })
}

/**
 * 退出登录
 *
 * 后端无独立退出接口：access token 过期即失效，refresh token 7 天后自动过期，
 * 前端只需清理本地存储，故此处仅作占位（保持 store.logout 调用链完整）。
 */
export function logout() {
  return Promise.resolve()
}

/**
 * 获取第三方平台授权配置
 *
 * 后端接口：GET /api/oauth2/get_config/（extends/oauth2/views.py，免登录）
 * 返回平台授权所需参数（appid / client_id / authorize_uri / redirect_uri 等，不含 secret）。
 *
 * @param platform 平台标识（如 wechat / wecom / qq / alipay / weibo / github / gitee）
 * @param kind 平台类型（PC=H5 网页授权，M=小程序）
 * @returns 平台配置信息
 */
export function getOAuthConfig(platform: string, kind: string) {
  return http.get<IOAuthConfig>('/api/oauth2/get_config/', { platform, kind }, undefined, { hideErrorToast: true })
}

/**
 * 第三方授权登录（微信 / 企业微信 / QQ / 支付宝 / 微博 / GitHub / Gitee 通用入口）
 *
 * 后端接口：POST /api/oauth2/callback/（extends/oauth2/views.py，免登录）
 * 后端服务层处理：校验 code → 换取平台用户信息 → 自动注册/绑定 → 签发 JWT，
 * 成功返回与密码登录一致的令牌 + 用户信息结构（可复用 token store 的 _postLogin）。
 *
 * 提示：平台占位符未替换为真实值时，后端会返回明确业务错误（如微信 invalid appid），
 * 前端需在调用处捕获并以友好提示降级，不影响密码登录体验。
 *
 * @param params 回调参数（platform / kind / source / code）
 * @returns 登录结果（令牌 + 用户信息）
 */
export function oauthLogin(params: IOAuthLoginParams) {
  return http.post<IAuthLoginRes>('/api/oauth2/callback/', params, undefined, undefined, { hideErrorToast: true })
}
