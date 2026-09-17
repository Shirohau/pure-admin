/**
 * 认证相关类型定义
 *
 * 与后端 extends/jwt/views.py 的 UserTokenSerializer 输出结构对齐：
 * 登录 / 刷新 / 验证接口统一返回 { accessToken, refreshToken, expires, ...用户信息 }
 */

/**
 * 令牌信息（登录/刷新响应中的令牌部分）
 */
export interface ITokenInfo {
  /** 访问令牌（请求时放入 Authorization: Bearer <accessToken>） */
  accessToken: string
  /** 刷新令牌（用于换取新的访问令牌） */
  refreshToken: string
  /** access token 过期时间戳（毫秒，后端由 JWT exp 换算而来） */
  expires: number
}

/**
 * 用户角色ID（对应后端角色表主键）
 */
export type UserRole = number

/**
 * 用户信息（登录/刷新响应中的用户部分）
 */
export interface IUserInfo {
  /** 用户ID */
  id: number
  /** 用户账号 */
  username: string
  /** 用户姓名 */
  name: string
  /** 头像URL */
  avatar?: string | undefined
  /** 角色ID列表 */
  roles: UserRole[]
  /** 所属部门名称（后端登录/刷新接口返回，未分配部门时为 null） */
  deptName?: string | null
}

/**
 * 登录/刷新接口完整响应（令牌 + 用户信息，一次返回）
 */
export type IAuthLoginRes = ITokenInfo & IUserInfo

/**
 * 第三方平台配置（后端 GET /api/oauth2/get_config/ 返回）
 *
 * 不同平台字段不一致（微信/企业微信为 appid，支付宝为 app_id，微博/GitHub 为 client_id），
 * 因此除常用字段外开放任意扩展字段。
 */
export interface IOAuthConfig {
  /** 应用ID（微信 / 企业微信为 appid，支付宝为 app_id，其余平台为 client_id） */
  appid?: string
  /** 应用ID（非微信平台） */
  client_id?: string
  /** 应用ID（支付宝） */
  app_id?: string
  /** 授权页面地址（H5 跳转授权链接用） */
  authorize_uri?: string
  /** 授权回调地址 */
  redirect_uri?: string
  /** 企业微信自建应用 ID */
  agentid?: string
  /** 其余平台特有字段（token_uri / userinfo_uri / scope 等） */
  [key: string]: any
}

/**
 * OAuth2 回调参数（POST /api/oauth2/callback/ 请求体）
 *
 * 后端 extends/oauth2/service.py OAuthService 解析：
 * - platform: 平台标识（wechat / wecom / qq / alipay / weibo / github / gitee）
 * - kind: 平台类型（PC=H5 网页授权，M=小程序）
 * - source: 操作类型（login=登录，binding=账号绑定）
 * - code: 授权码（H5 回调 code 或小程序 uni.login 返回的 code）
 * - user_id: 当前用户ID（仅 binding 场景必传）
 */
export interface IOAuthLoginParams {
  /** 平台标识（如 wechat / qq / alipay） */
  platform: string
  /** 平台类型（PC / M） */
  kind: string
  /** 操作类型（当前仅登录场景） */
  source: 'login' | 'binding'
  /** 授权码 */
  code: string
  /** 当前用户ID（仅绑定场景需要） */
  user_id?: number
}
