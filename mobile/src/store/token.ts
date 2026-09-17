import type { ILoginForm } from '@/api/login'
import type { IAuthLoginRes, ITokenInfo, IUserInfo } from '@/api/types/login'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useUserStore } from './user'
import {
  login as _login,
  logout as _logout,
  oauthLogin as _oauthLogin,
  refreshToken as _refreshToken,
} from '@/api/login'

// 初始化令牌状态
const tokenInfoState: ITokenInfo = {
  accessToken: '',
  refreshToken: '',
  expires: 0,
}

export const useTokenStore = defineStore(
  'token',
  () => {
    // 令牌信息（accessToken / refreshToken / 过期时间戳）
    const tokenInfo = ref<ITokenInfo>({ ...tokenInfoState })

    // 添加一个时间戳 ref 作为响应式依赖，确保过期判断能拿到最新时间
    const nowTime = ref(Date.now())

    /**
     * 更新响应式时间戳 nowTime
     *
     * 由于 isTokenExpired 依赖 nowTime 计算，调用本方法可强制重新计算过期状态，
     * 避免使用缓存的过期结果。建议在登录、登出、刷新后链式调用：tokenStore.updateNowTime().hasLogin
     *
     * @returns 最新的 tokenStore 实例
     */
    const updateNowTime = () => {
      nowTime.value = Date.now()
      return useTokenStore()
    }

    /**
     * 设置令牌信息，并持久化过期时间戳
     * @param val 令牌信息（accessToken / refreshToken / expires 毫秒时间戳）
     */
    const setTokenInfo = (val: ITokenInfo) => {
      updateNowTime()
      tokenInfo.value = val
      // 持久化过期时间戳（毫秒），刷新页面后仍能判断是否过期
      uni.setStorageSync('accessTokenExpireTime', val.expires)
    }

    /**
     * 判断 access token 是否过期
     */
    const isTokenExpired = computed(() => {
      if (!tokenInfo.value || !tokenInfo.value.accessToken) {
        return true
      }

      const now = nowTime.value
      const expireTime = uni.getStorageSync('accessTokenExpireTime')

      if (!expireTime)
        return true
      return now >= expireTime
    })

    /**
     * 登录成功后的公共处理：保存令牌 + 写入用户信息
     *
     * 后端登录/刷新接口一次返回令牌与用户信息，无需再额外请求用户信息接口。
     *
     * @param res 登录/刷新接口响应（令牌 + 用户信息）
     */
    async function _postLogin(res: IAuthLoginRes) {
      // 拆分令牌与用户信息，分别写入对应 store
      const { accessToken, refreshToken, expires, ...userInfo } = res
      setTokenInfo({ accessToken, refreshToken, expires })
      const userStore = useUserStore()
      userStore.setUserInfo(userInfo as IUserInfo)
    }

    /**
     * 用户登录
     *
     * @param loginForm 登录参数（用户名/邮箱/手机号 + 密码）
     * @returns 登录结果（令牌 + 用户信息）
     */
    const login = async (loginForm: ILoginForm) => {
      try {
        const res = await _login(loginForm)
        console.log('普通登录-res: ', res)
        await _postLogin(res)
        uni.showToast({
          title: '登录成功',
          icon: 'success',
        })
        return res
      }
      catch (error) {
        console.error('登录失败:', error)
        throw error
      }
      finally {
        updateNowTime()
      }
    }

    /**
     * 第三方授权登录（微信 / 企业微信 / QQ / 支付宝 / 微博 / GitHub / Gitee）
     *
     * 复用 _postLogin 公共处理：后端返回结构与密码登录一致（令牌 + 用户信息），
     * 授权失败/后端未支持时抛出错误，由调用方（登录页）捕获并降级提示。
     *
     * @param platform 平台标识（如 wechat / wecom / qq / alipay）
     * @param kind 平台类型（PC=H5 网页授权，M=小程序）
     * @param code 授权码（H5 回调 code 或小程序 uni.login 返回的 code）
     * @returns 登录结果（令牌 + 用户信息）
     */
    const oauthLogin = async (platform: string, kind: string, code: string) => {
      try {
        const res = await _oauthLogin({ platform, kind, source: 'login', code })
        console.log('第三方授权登录-res: ', res)
        await _postLogin(res)
        uni.showToast({
          title: '登录成功',
          icon: 'success',
        })
        return res
      }
      catch (error) {
        console.error('第三方授权登录失败:', error)
        throw error
      }
      finally {
        updateNowTime()
      }
    }

    /**
     * 退出登录：调用后端退出（当前为本地占位）+ 清理本地令牌与用户信息
     */
    const logout = async () => {
      try {
        // 后端无独立退出接口，此处仅清理本地状态
        await _logout()
      }
      catch (error) {
        console.error('退出登录失败:', error)
      }
      finally {
        updateNowTime()

        // 无论成功失败，都需要清除本地令牌与过期时间
        uni.removeStorageSync('accessTokenExpireTime')
        console.log('退出登录-清除用户信息')
        tokenInfo.value = { ...tokenInfoState }
        uni.removeStorageSync('token')
        const userStore = useUserStore()
        userStore.clearUserInfo()
      }
    }

    /**
     * 刷新 token
     *
     * 后端开启 ROTATE_REFRESH_TOKENS，刷新成功会返回新的 accessToken 与 refreshToken，
     * 同时旧 refreshToken 自动拉黑，因此这里整体覆盖令牌信息并同步更新用户信息。
     *
     * @returns 刷新结果（新令牌 + 用户信息）
     */
    const refreshToken = async () => {
      // 安全检查：确保 refreshToken 存在
      if (!tokenInfo.value || !tokenInfo.value.refreshToken) {
        throw new Error('无效的refreshToken')
      }

      try {
        const refreshTokenValue = tokenInfo.value.refreshToken
        const res = await _refreshToken(refreshTokenValue)
        console.log('刷新token-res: ', res)
        await _postLogin(res)
        return res
      }
      catch (error) {
        console.error('刷新token失败:', error)
        throw error
      }
      finally {
        updateNowTime()
      }
    }

    /**
     * 获取有效的 access token（未过期才返回，过期返回空字符串）
     *
     * 注意：本计算属性不触发异步刷新，如需自动刷新请使用 tryGetValidToken
     */
    const getValidToken = computed(() => {
      // token 已过期或不存在，返回空
      if (isTokenExpired.value) {
        return ''
      }
      return tokenInfo.value?.accessToken || ''
    })

    /**
     * 检查是否已登录（仅判断本地是否存有令牌，不校验过期时间）
     */
    const hasLoginInfo = computed(() => {
      return !!tokenInfo.value && !!tokenInfo.value.accessToken
    })

    /**
     * 检查是否已登录且令牌有效（未过期）
     * 建议这样使用：tokenStore.updateNowTime().hasLogin
     */
    const hasValidLogin = computed(() => {
      return hasLoginInfo.value && !isTokenExpired.value
    })

    /**
     * 尝试获取有效的 access token，若已过期则先刷新令牌
     *
     * @returns 有效的 access token 或空字符串
     */
    const tryGetValidToken = async (): Promise<string> => {
      updateNowTime()
      if (!getValidToken.value && tokenInfo.value?.refreshToken) {
        try {
          await refreshToken()
          return getValidToken.value
        }
        catch (error) {
          console.error('尝试刷新token失败:', error)
          return ''
        }
      }
      return getValidToken.value
    }

    return {
      // 核心API方法
      login,
      oauthLogin,
      logout,
      refreshToken,

      // 认证状态判断（最常用的）
      hasLogin: hasValidLogin,
      hasLoginInfo,

      // 内部系统使用的方法
      tryGetValidToken,
      validToken: getValidToken,

      // 调试或特殊场景可能需要直接访问的信息
      tokenInfo,
      setTokenInfo,
      updateNowTime,
    }
  },
  {
    // 添加持久化配置，确保刷新页面后令牌信息不丢失
    persist: true,
  },
)
