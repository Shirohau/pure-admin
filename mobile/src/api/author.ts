import { http } from '@/http/http'

/**
 * 作者接口封装（对接后端 apps/example/models/author，前缀 /api/example/author/）
 *
 * 后端说明：
 * - 列表接口使用 page/limit 分页（CustomPageNumberPagination），
 *   响应中 paginated 字段包含 next / previous / page / limit / total / total_pages；
 *   传 paginate=false 时不分页，返回全量数据（paginated 为 null），用于表单选择器；
 * - 由于 http 封装仅返回 responseData.data，列表接口需使用 uni.request 直接获取完整响应
 *   （uni.addInterceptor 拦截器仍会处理 baseUrl 拼接与 Authorization 注入）；
 * - 性别字段存中文值（男/女，后端过滤器注释约定 gender__in=男,女）；
 * - 新增/更新需提交 book 字段（关联图书 ID 数组），作者模块暂不维护关联图书，提交空数组。
 */

/** 作者关联的图书摘要（AuthorBookSerializer 返回结构） */
export interface IAuthorBook {
  id: number
  /** 书名 */
  name: string
  /** 价格（Decimal 序列化为字符串） */
  price: string
  /** 最后更新人 */
  updater_name: string
}

/** 作者实体（与后端 AuthorSerializer 返回结构对齐） */
export interface IAuthorItem {
  id: number
  /** 作者姓名 */
  name: string
  /** 性别（男/女） */
  gender?: string
  /** 年龄 */
  age?: number
  /** 出生日期（YYYY-MM-DD） */
  birth_date?: string
  /** 简介 */
  biography?: string
  /** 关联图书 ID 列表 */
  book: number[]
  /** 关联图书详情列表（仅详情接口返回） */
  book_all?: IAuthorBook[]
  /** 图书数量 */
  book_count?: number
  /** 图书平均价格（字符串，如 "0.00"） */
  avg_price?: string
  /** 创建人 */
  creator_name?: string
  /** 更新人 */
  updater_name?: string
  /** 创建时间 */
  create_dt?: string
  /** 更新时间 */
  update_dt?: string
}

/** 作者新增/编辑提交体 */
export interface IAuthorForm {
  /** 作者姓名（必填） */
  name: string
  /** 性别（男/女） */
  gender?: string
  /** 年龄 */
  age?: number
  /** 出生日期（YYYY-MM-DD） */
  birth_date?: string
  /** 简介 */
  biography?: string
  /** 关联图书 ID 列表（作者模块暂不维护，提交空数组） */
  book?: number[]
}

/** 列表分页参数 */
export interface IAuthorListParams {
  /** 页码（从 1 开始，paginate=false 时可不传） */
  page?: number
  /** 每页数量（paginate=false 时可不传） */
  limit?: number
  /** 传 false 时不分页，返回全量数据（paginated 为 null） */
  paginate?: boolean
}

/** 后端分页元数据 */
export interface IPaginatedMeta {
  next: string | null
  previous: string | null
  page: number
  limit: number
  total: number
  total_pages: number
}

/** 列表接口返回结构（data + 分页元数据） */
export interface IAuthorListResult {
  data: IAuthorItem[]
  paginated: IPaginatedMeta | null
}

/** 接口前缀（与后端路由 apps/example/urls.py 对齐） */
const AUTHOR_API = '/api/example/author'

/**
 * 分页查询作者列表
 *
 * 由于 http 封装仅返回 responseData.data，此处直接使用 uni.request 获取完整响应，
 * uni.addInterceptor 拦截器仍会处理 baseUrl 拼接、Authorization 注入与超时设置。
 *
 * @param params 分页参数（page 页码 / limit 每页数量，或 paginate=false 获取全量）
 * @returns 包含 data 数组和 paginated 分页元数据的对象
 */
export function getAuthorList(params: IAuthorListParams): Promise<IAuthorListResult> {
  // 构建查询字符串（与 http/tools/queryString.ts 逻辑一致）
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${AUTHOR_API}/`,
      method: 'GET',
      dataType: 'json',
      // #ifndef MP-WEIXIN
      responseType: 'json',
      // #endif
      ...(qs ? { url: `${AUTHOR_API}/?${qs}` } : {}),
      success: (res) => {
        const responseData = res.data as Record<string, any>
        const code = responseData?.code

        // 成功状态：HTTP 2xx 且业务码为成功码（2000 等）
        if (res.statusCode >= 200 && res.statusCode < 300 && code === 2000) {
          resolve({
            data: (responseData.data ?? []) as IAuthorItem[],
            paginated: (responseData.paginated ?? null) as IPaginatedMeta | null,
          })
        }
        else {
          // 业务错误：展示后端返回的 message
          const msg = responseData?.message || responseData?.msg || '请求失败'
          uni.showToast({ icon: 'none', title: msg })
          reject(new Error(msg))
        }
      },
      fail: (err) => {
        uni.showToast({ icon: 'none', title: '网络错误，换个网络试试' })
        reject(err)
      },
    })
  })
}

/**
 * 查询作者详情
 * @param id 作者主键
 * @returns 作者完整信息（含 book_all 关联图书列表）
 */
export function getAuthorDetail(id: number) {
  return http.get<IAuthorItem>(`${AUTHOR_API}/${id}/`)
}

/**
 * 新增作者
 * @param data 作者表单数据
 * @returns 新增后的作者
 */
export function createAuthor(data: IAuthorForm) {
  return http.post<IAuthorItem>(`${AUTHOR_API}/`, data)
}

/**
 * 更新作者（后端 update 为 partial=True，支持只传部分字段）
 * @param id 作者主键
 * @param data 待更新字段
 * @returns 更新后的作者
 */
export function updateAuthor(id: number, data: IAuthorForm) {
  return http.put<IAuthorItem>(`${AUTHOR_API}/${id}/`, data)
}

/**
 * 删除作者（后端捕获 ProtectedError，被图书引用时返回错误提示）
 * @param id 作者主键
 */
export function deleteAuthor(id: number) {
  return http.delete<null>(`${AUTHOR_API}/${id}/`)
}
