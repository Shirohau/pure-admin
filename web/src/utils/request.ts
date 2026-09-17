import { http } from "./http";

/**
 * ruoyi 风格 request 适配器
 *
 * 将 request({ url, method, data, params, headers }) 调用方式转换为
 * 本项目 @/utils/http 的调用方式，并把响应统一归一化为 ruoyi 的
 * { code, msg, data } 结构：
 *   - code === 200 视为成功
 *   - errMsg / msg / message 为错误信息字段
 *
 * 说明：使用 skipResponse 跳过全局错误通知，由调用方自行提示，
 * 便于后端接口未就绪时页面仍可正常浏览。
 */
interface RequestConfig {
  url: string;
  method?: "get" | "post" | "put" | "delete" | string;
  data?: any;
  params?: any;
  headers?: Record<string, string>;
  timeout?: number;
}

export default function request(config: RequestConfig): Promise<any> {
  const { url, method = "get", data, params, headers, timeout } = config;
  return http
    .request<any>(
      method as any,
      url,
      { data, params, headers, timeout },
      { skipResponse: true }
    )
    .then((res: any) => {
      // skipResponse 模式下返回完整 axios response，后端响应体在 res.data
      const body = res?.data ?? res;
      const success = body?.success !== false;
      return {
        code: success ? 200 : 500,
        msg: body?.message ?? body?.msg ?? "",
        message: body?.message ?? body?.msg ?? "",
        errMsg: body?.message ?? body?.msg ?? "",
        data: body?.data ?? body,
        ...body
      };
    })
    .catch((err: any) => {
      const message = err?.message ?? err?.errMsg ?? "请求失败";
      return {
        code: 500,
        msg: message,
        message,
        errMsg: message,
        data: null
      };
    });
}
