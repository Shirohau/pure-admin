import { http } from '@/http/http'

/**
 * 图书接口封装（对接后端 apps/example/models/book，前缀 /api/example/book/）
 *
 * 后端说明：
 * - 列表接口支持 page/limit 分页（CustomPageNumberPagination），
 *   通过 returnFullResponse 获取完整响应（含 paginated 分页元数据）；
 * - 传 paginate=false 时不分页，返回全量数据（paginated 为 null），用于表单选择器；
 * - 出版社为外键（publisher 可空），后端返回 publisher_row 嵌套对象；
 * - 作者为多对多关联，写入时传 ID 数组，读取时有 author_all 嵌套列表；
 * - 价格为 Decimal 序列化字符串（如 "59.00"），提交时保持字符串即可；
 * - 出版时间为字符串（%Y-%m-%d %H:%M:%S），前端日期选择器使用时间戳，需互转。
 */

/** 图书关联的出版社摘要（PublisherPartialSerializer 返回结构） */
export interface IBookPublisher {
  id: number
  /** 出版社名称 */
  name: string
  /** 最后更新人 */
  updater_name: string
}

/** 图书关联的作者摘要（AuthorPartialSerializer 返回结构） */
export interface IBookAuthor {
  id: number
  /** 作者姓名 */
  name: string
  /** 创建人 */
  creator_name: string
}

/** 图书实体（与后端 BookSerializer 返回结构对齐） */
export interface IBookItem {
  id: number
  /** 书名（必填） */
  name: string
  /** ISBN（必填，唯一） */
  isbn: string
  /** 出版时间（YYYY-MM-DD HH:mm:ss） */
  publication_time?: string
  /** 价格（Decimal 序列化为字符串，必填，>= 0） */
  price: string
  /** 页数 */
  pages?: number
  /** 内容简介 */
  description?: string
  /** 出版社主键 */
  publisher?: number | null
  /** 出版社名称（只读展示） */
  publisher_name?: string
  /** 出版社详情（publisher_row，含 id/name/updater_name） */
  publisher_row?: IBookPublisher | null
  /** 关联作者 ID 列表 */
  author: number[]
  /** 关联作者详情列表（仅详情接口返回） */
  author_all?: IBookAuthor[]
  /** 创建人 */
  creator_name?: string
  /** 更新人 */
  updater_name?: string
  /** 创建时间 */
  create_dt?: string
  /** 更新时间 */
  update_dt?: string
}

/** 图书新增/编辑提交体 */
export interface IBookForm {
  /** 书名（必填） */
  name: string
  /** ISBN（必填） */
  isbn: string
  /** 出版时间（YYYY-MM-DD HH:mm:ss，可空） */
  publication_time?: string
  /** 价格（必填，>= 0） */
  price: string
  /** 页数（可空） */
  pages?: number
  /** 内容简介（可空） */
  description?: string
  /** 出版社主键（可空） */
  publisher?: number | null
  /** 关联作者 ID 列表（图书模块暂不维护，提交空数组） */
  author?: number[]
}

/** 分页元数据（后端 CustomPageNumberPagination 返回结构） */
export interface IBookPaginated {
  next: string | null
  previous: string | null
  page: number
  limit: number
  total: number
  total_pages: number
}

/** 列表分页参数 */
export interface IBookListParams {
  /** 页码（从 1 开始，paginate=false 时可不传） */
  page?: number
  /** 每页数量（paginate=false 时可不传） */
  limit?: number
  /** 传 false 时不分页，返回全量数据（paginated 为 null） */
  paginate?: boolean
}

/** 列表接口完整响应（含分页元数据） */
interface IBookListResponse {
  data: IBookItem[]
  paginated: IBookPaginated | null
}

/** 接口前缀（与后端路由 apps/example/urls.py 对齐） */
const BOOK_API = '/api/example/book'

/**
 * 分页查询图书列表
 * @param params 分页参数（page 页码 / limit 每页数量）
 * @returns 当前页图书数组 + 分页元数据（paginated）
 */
export async function getBookList(params: IBookListParams) {
  const res = await http<IBookListResponse>({
    url: `${BOOK_API}/`,
    query: params,
    method: 'GET',
    returnFullResponse: true,
  })
  return { data: res.data, paginated: res.paginated }
}

/**
 * 查询图书详情
 * @param id 图书主键
 * @returns 图书完整信息（含 publisher_row / author_all）
 */
export function getBookDetail(id: number) {
  return http.get<IBookItem>(`${BOOK_API}/${id}/`)
}

/**
 * 新增图书
 * @param data 图书表单数据
 * @returns 新增后的图书
 */
export function createBook(data: IBookForm) {
  return http.post<IBookItem>(`${BOOK_API}/`, data)
}

/**
 * 更新图书（后端 update 为 partial=True，支持只传部分字段）
 * @param id 图书主键
 * @param data 待更新字段
 * @returns 更新后的图书
 */
export function updateBook(id: number, data: IBookForm) {
  return http.put<IBookItem>(`${BOOK_API}/${id}/`, data)
}

/**
 * 删除图书
 * @param id 图书主键
 */
export function deleteBook(id: number) {
  return http.delete<null>(`${BOOK_API}/${id}/`)
}
