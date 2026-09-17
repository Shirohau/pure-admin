/**
 * 登录拦截策略配置
 *
 * 与 src/router/interceptor.ts 的路由拦截器配对使用，详情见 src/router/README.md
 */

/**
 * 登录策略：
 * - DEFAULT_NEED_LOGIN = true  → 默认需要登录策略：进入任何页面都需要登录，只有白名单中的页面才不需要登录
 * - DEFAULT_NEED_LOGIN = false → 默认无需登录策略：进入任何页面都不需要登录，只有黑名单中的页面才需要登录
 *
 * 本项目为 2B 类应用，采用默认需要登录策略
 */
export const DEFAULT_NEED_LOGIN = true

/**
 * 排除登录的路由列表（路径以 '/' 开头，与路由路径一致）
 *
 * - 默认需要登录策略下：列表中的页面不需要登录（白名单，如登录页、注册页等）
 * - 默认无需登录策略下：列表中的页面才需要登录（黑名单）
 *
 * 注意：除了本列表，页面 definePage 中配置了 excludeLoginPath: true 的页面同样会被视为免登录页面，
 * 两者是并集关系（见 interceptor.ts 中的 getExcludeLoginPathSet）
 */
export const EXCLUDE_LOGIN_PATH_LIST: string[] = [
  // 登录页本身保持免登录，避免重定向死循环
  '/pages/login/index',
]

/**
 * 是否在小程序中使用 H5 登录页的登录逻辑
 * 本项目登录页复用 H5 逻辑，小程序端同样启用
 */
export const LOGIN_PAGE_ENABLE_IN_MP = true
