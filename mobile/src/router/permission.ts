import { useTokenStore } from '@/store/token'
import { tabbarStore } from '@/tabbar/store'
import { DEFAULT_NEED_LOGIN } from './config'
import { getExcludeLoginPathSet } from './interceptor'

export const permission = {
  install(router) {
    router.beforeEach((to, from, next) => {
      const path = to.path
      tabbarStore.setAutoCurIdx(path)

      // H5 端兜底登录拦截：uni.addInterceptor 只能拦截 uni API 调用，
      // 无法拦截浏览器地址栏直接修改 hash 的导航（不触发 onShow），此处用 vue-router 全局守卫补充拦截。
      // 注意必须使用 next() 重定向而非 next(false) + toLoginPage：
      // next(false) 会中止 uni-app H5 的初始导航，导致页面栈为空且后续 uni.reLaunch 全部失效。
      if (DEFAULT_NEED_LOGIN && !getExcludeLoginPathSet().has(path)) {
        const tokenStore = useTokenStore()
        if (!tokenStore.updateNowTime().hasLogin) {
          // 携带目标路径（含 query）作为 redirect，登录成功后自动回跳
          const fullPath = to.fullPath || path
          next({
            path: '/pages/login/index',
            query: { redirect: encodeURIComponent(fullPath) },
          })
          return
        }
      }

      next()
    })
  },
}
