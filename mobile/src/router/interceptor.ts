/**
 * by 菲鸽 on 2025-08-19
 * 路由拦截，通常也是登录拦截
 * 黑、白名单的配置，请看 config.ts 文件， EXCLUDE_LOGIN_PATH_LIST
 */
import { useTokenStore } from '@/store/token'
import { tabbarStore } from '@/tabbar/store'
import { getAllPages, getLastPage, parseUrlToObj } from '@/utils/index'
import { toLoginPage } from '@/utils/toLoginPage'
import { DEFAULT_NEED_LOGIN, EXCLUDE_LOGIN_PATH_LIST } from './config'

export const FG_LOG_ENABLE = false

/**
 * 获取免登录页面路径集合（白名单）
 *
 * 白名单 = config.ts 中的 EXCLUDE_LOGIN_PATH_LIST + 页面 definePage 中配置了 excludeLoginPath: true 的页面，两者取并集
 *
 * @returns 免登录页面路径集合，路径以 '/' 开头（如 '/pages/login/index'）
 */
export function getExcludeLoginPathSet() {
  const excludeSet = new Set<string>(EXCLUDE_LOGIN_PATH_LIST)
  // getAllPages('excludeLoginPath') 返回配置了 excludeLoginPath: true 的页面，path 为 '/' 开头
  getAllPages('excludeLoginPath').forEach((page) => {
    excludeSet.add(page.path)
  })
  return excludeSet
}

export const navigateToInterceptor = {
  // 注意，这里的url是 '/' 开头的，如 '/pages/index/index'，跟 'pages.json' 里面的 path 不同
  // 增加对相对路径的处理，BY 网友 @ideal
  invoke({ url, query }: { url: string, query?: Record<string, string> }) {
    if (url === undefined) {
      return
    }
    let { path, query: _query } = parseUrlToObj(url)

    FG_LOG_ENABLE && console.log('\n\n路由拦截器:-------------------------------------')
    FG_LOG_ENABLE && console.log('路由拦截器 1: url->', url, ', query ->', query)
    const myQuery = { ..._query, ...query }
    // /pages/route-interceptor/index?name=feige&age=30
    FG_LOG_ENABLE && console.log('路由拦截器 2: path->', path, ', _query ->', _query)
    FG_LOG_ENABLE && console.log('路由拦截器 3: myQuery ->', myQuery)

    // 处理相对路径
    if (!path.startsWith('/')) {
      const currentPath = getLastPage()?.route || ''
      const normalizedCurrentPath = currentPath.startsWith('/') ? currentPath : `/${currentPath}`
      const baseDir = normalizedCurrentPath.substring(0, normalizedCurrentPath.lastIndexOf('/'))
      path = `${baseDir}/${path}`
    }

    // 登录拦截：默认需要登录策略下，未登录用户访问受保护页面时阻止跳转并跳转登录页
    if (DEFAULT_NEED_LOGIN && !getExcludeLoginPathSet().has(path)) {
      const tokenStore = useTokenStore()
      // hasLogin：令牌存在且未过期（内部会读取本地持久化的过期时间，兼容刷新页面场景）
      if (!tokenStore.updateNowTime().hasLogin) {
        FG_LOG_ENABLE && console.log('路由拦截器-未登录拦截: path->', path)
        // 拼接完整目标地址（含 query）作为 redirect 参数，登录成功后自动回跳
        const queryStr = Object.keys(myQuery).length > 0
          ? `?${Object.entries(myQuery).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&')}`
          : ''
        const redirectPath = `${path}${queryStr}`
        toLoginPage({
          mode: 'reLaunch',
          queryString: `?redirect=${encodeURIComponent(redirectPath)}`,
        })
        return false // 明确表示阻止原路由继续执行
      }
    }

    // 处理直接进入路由非首页时，tabbarIndex 不正确的问题
    tabbarStore.setAutoCurIdx(path)
  },
}

export const routeInterceptor = {
  install() {
    uni.addInterceptor('navigateTo', navigateToInterceptor)
    uni.addInterceptor('reLaunch', navigateToInterceptor)
    uni.addInterceptor('redirectTo', navigateToInterceptor)
    uni.addInterceptor('switchTab', navigateToInterceptor)
  },
}
