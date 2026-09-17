import { http } from '@/http/http'
import { stringifyQuery } from '@/http/tools/queryString'

/**
 * 出版社接口封装（对接后端 apps/example/models/publisher，前缀 /api/example/publisher/）
 *
 * 后端说明：
 * - 列表接口支持 page/limit 分页（CustomPageNumberPagination），
 *   响应包含 data（当前页数组）和 paginated（分页元数据），
 *   列表函数通过 uni.request 直接获取完整响应，以拿到 paginated.next 判断 hasMore；
 * - 省市县为独立字段（province/city/district），后端同时返回拼接后的 area_str（如 "浙江省 / 杭州市 / 西湖区"）；
 * - 新增/更新需提交 book 字段（关联图书 ID 数组），出版社模块暂不维护关联图书，提交空数组。
 */

/** 分页元数据（与后端 CustomPageNumberPagination 返回结构对齐） */
export interface IPaginatedMeta {
  /** 下一页链接（null 表示没有更多数据） */
  next: string | null
  /** 上一页链接 */
  previous: string | null
  /** 当前页码 */
  page: number
  /** 每页数量 */
  limit: number
  /** 总记录数 */
  total: number
  /** 总页数 */
  total_pages: number
}

/** 出版社关联的图书摘要（PublisherBookSerializer 返回结构） */
export interface IPublisherBook {
  id: number
  /** 书名 */
  name: string
  /** 价格（Decimal 序列化为字符串） */
  price: string
  /** 最后更新人 */
  updater_name: string
}

/** 出版社实体（与后端 PublisherSerializer 返回结构对齐） */
export interface IPublisherItem {
  id: number
  /** 出版社名称（必填，唯一） */
  name: string
  /** 省份 */
  province?: string
  /** 城市 */
  city?: string
  /** 区县 */
  district?: string
  /** 详细地址 */
  address?: string
  /** 联系电话 */
  phone?: string
  /** 邮箱 */
  email?: string
  /** 官网网址 */
  website?: string
  /** 关联图书 ID 列表 */
  book: number[]
  /** 关联图书详情列表（仅详情接口返回） */
  book_all?: IPublisherBook[]
  /** 图书数量 */
  book_count?: number
  /** 图书平均价格（字符串，如 "0.00"） */
  avg_price?: string
  /** 地区拼接字符串（如 "浙江省 / 杭州市 / 西湖区"） */
  area_str?: string
  /** 创建人 */
  creator_name?: string
  /** 更新人 */
  updater_name?: string
  /** 创建时间 */
  create_dt?: string
  /** 更新时间 */
  update_dt?: string
}

/** 出版社新增/编辑提交体 */
export interface IPublisherForm {
  /** 出版社名称（必填） */
  name: string
  /** 省份 */
  province?: string
  /** 城市 */
  city?: string
  /** 区县 */
  district?: string
  /** 详细地址 */
  address?: string
  /** 联系电话 */
  phone?: string
  /** 邮箱 */
  email?: string
  /** 官网网址 */
  website?: string
  /** 关联图书 ID 列表（出版社模块暂不维护，提交空数组） */
  book?: number[]
}

/** 列表分页参数 */
export interface IPublisherListParams {
  /** 页码（从 1 开始，paginate=false 时可不传） */
  page?: number
  /** 每页数量（paginate=false 时可不传） */
  limit?: number
  /** 传 false 时不分页，返回全量数据（paginated 为 null） */
  paginate?: boolean
}

/** 接口前缀（与后端路由 apps/example/urls.py 对齐） */
const PUBLISHER_API = '/api/example/publisher'

/**
 * 分页查询出版社列表
 *
 * 使用 uni.request 直接发起请求（仍经过拦截器拼接 baseUrl / token / query），
 * 以获取完整响应中的 paginated 分页元数据，从而准确判断 hasMore 状态。
 *
 * @param params 分页参数（page 页码 / limit 每页数量）
 * @returns 当前页出版社数组 + 分页元数据
 */
export function getPublisherList(params: IPublisherListParams): Promise<{ data: IPublisherItem[], paginated: IPaginatedMeta | null }> {
  const queryStr = stringifyQuery(params as Record<string, any>)
  const url = `${PUBLISHER_API}/${queryStr ? `?${queryStr}` : ''}`

  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: 'GET',
      dataType: 'json',
      timeout: 60000,
      success: (res) => {
        const responseData = res.data as Record<string, any>
        const statusCode = res.statusCode
        if (statusCode >= 200 && statusCode < 300) {
          const code = responseData?.code
          // 兼容 0 / 200 / 2000 三种成功码
          if (code === 0 || code === 200 || code === 2000) {
            resolve({
              data: (responseData.data ?? []) as IPublisherItem[],
              paginated: (responseData.paginated ?? null) as IPaginatedMeta | null,
            })
          }
          else {
            const msg = responseData?.message || responseData?.msg || '请求错误'
            uni.showToast({ icon: 'none', title: msg })
            reject(new Error(msg))
          }
        }
        else {
          const msg = `请求错误(${statusCode})`
          uni.showToast({ icon: 'none', title: msg })
          reject(new Error(msg))
        }
      },
      fail: (err) => {
        const msg = '网络错误，换个网络试试'
        uni.showToast({ icon: 'none', title: msg })
        reject(new Error(msg))
      },
    } as any)
  })
}

/**
 * 查询出版社详情
 * @param id 出版社主键
 * @returns 出版社完整信息（含 book_all 关联图书列表）
 */
export function getPublisherDetail(id: number) {
  return http.get<IPublisherItem>(`${PUBLISHER_API}/${id}/`)
}

/**
 * 新增出版社
 * @param data 出版社表单数据
 * @returns 新增后的出版社
 */
export function createPublisher(data: IPublisherForm) {
  return http.post<IPublisherItem>(`${PUBLISHER_API}/`, data)
}

/**
 * 更新出版社（后端 update 为 partial=True，支持只传部分字段）
 * @param id 出版社主键
 * @param data 待更新字段
 * @returns 更新后的出版社
 */
export function updatePublisher(id: number, data: IPublisherForm) {
  return http.put<IPublisherItem>(`${PUBLISHER_API}/${id}/`, data)
}

/**
 * 删除出版社
 * @param id 出版社主键
 */
export function deletePublisher(id: number) {
  return http.delete<null>(`${PUBLISHER_API}/${id}/`)
}
