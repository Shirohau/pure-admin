import Axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type CustomParamsSerializer
} from "axios";
import type {
  PureHttpError,
  RequestMethods,
  PureHttpResponse,
  PureHttpRequestConfig
} from "./types.d";
import { stringify } from "qs";
import { getToken, formatToken } from "@/utils/auth";
import { useUserStoreHook } from "@/store/modules/user";
import { ElLoading, ElMessage, ElNotification } from "element-plus";
import { downloadByData } from "@pureadmin/utils";

// 相关配置请参考：www.axios-js.com/zh-cn/docs/#axios-request-config-1
const defaultConfig: AxiosRequestConfig = {
  baseURL: import.meta.env.VITE_API_URL,
  // 请求超时时间
  timeout: 10000,
  headers: {
    Accept: "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest"
  },
  // 数组格式参数序列化（https://github.com/axios/axios/issues/5142）
  paramsSerializer: {
    serialize: stringify as unknown as CustomParamsSerializer
  }
};

class PureHttp {
  constructor() {
    this.httpInterceptorsRequest();
    this.httpInterceptorsResponse();
  }

  /** `token`过期后，暂存待执行的请求 */
  private static requests: Array<{
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
  }> = [];

  /** 防止重复刷新`token` */
  private static isRefreshing = false;

  /** 初始化配置对象 */
  private static initConfig: PureHttpRequestConfig = {};

  /** 保存当前`Axios`实例对象 */
  private static axiosInstance: AxiosInstance = Axios.create(defaultConfig);

  /** 重连原始请求 */
  private static retryOriginalRequest(config: PureHttpRequestConfig) {
    return new Promise((resolve, reject) => {
      PureHttp.requests.push({
        resolve: (token: string) => {
          config.headers["Authorization"] = formatToken(token);
          resolve(config);
        },
        reject
      });
    });
  }

  /** 请求拦截 */
  private httpInterceptorsRequest(): void {
    PureHttp.axiosInstance.interceptors.request.use(
      async (config: PureHttpRequestConfig): Promise<any> => {
        // 优先判断post/get等方法是否传入回调，否则执行初始化设置等回调
        if (typeof config.beforeRequestCallback === "function") {
          config.beforeRequestCallback(config);
          return config;
        }
        if (PureHttp.initConfig.beforeRequestCallback) {
          PureHttp.initConfig.beforeRequestCallback(config);
          return config;
        }

        /** 显式标记跳过 token 处理的接口，不附加 token */
        if (config.skipToken) {
          return config;
        }
        return new Promise(resolve => {
          const data = getToken();
          if (data) {
            const now = new Date().getTime();
            const expired = parseInt(data.expires) - now <= 0;
            if (expired) {
              if (!PureHttp.isRefreshing) {
                PureHttp.isRefreshing = true;
                // token过期刷新
                useUserStoreHook()
                  .handRefreshToken({ refresh: data.refreshToken })
                  .then(res => {
                    const token = res.data.accessToken;
                    config.headers["Authorization"] = formatToken(token);
                    PureHttp.requests.forEach(request =>
                      request.resolve(token)
                    );
                    PureHttp.requests = [];
                  })
                  .catch(error => {
                    // refreshToken也过期，清除token并跳转登录页
                    PureHttp.requests.forEach(request => request.reject(error));
                    PureHttp.requests = [];
                    useUserStoreHook().logOut();
                  })
                  .finally(() => {
                    PureHttp.isRefreshing = false;
                  });
              }
              resolve(PureHttp.retryOriginalRequest(config));
            } else {
              config.headers["Authorization"] = formatToken(data.accessToken);
              resolve(config);
            }
          } else {
            resolve(config);
          }
        });
      },
      error => {
        return Promise.reject(error);
      }
    );
  }

  /** 响应拦截 */
  private httpInterceptorsResponse(): void {
    const instance = PureHttp.axiosInstance;
    instance.interceptors.response.use(
      (response: PureHttpResponse) => {
        // 检查是否跳过响应拦截，为 true 时直接返回完整 response，不处理 success/message
        if (response.config.skipResponse) {
          return response; // 注意：这里返回的是整个 response，不是 response.data
        }
        const success = response.data.success;
        const $config = response.config;
        if (success) {
          // 优先判断post/get等方法是否传入回调，否则执行初始化设置等回调
          if (typeof $config.beforeResponseCallback === "function") {
            $config.beforeResponseCallback(response);
            return response.data;
          }
          if (PureHttp.initConfig.beforeResponseCallback) {
            PureHttp.initConfig.beforeResponseCallback(response);
            return response.data;
          }
          return response.data;
        } else {
          ElNotification({
            type: "error",
            title: response.data.message || "请求失败",
            dangerouslyUseHTMLString: true,
            message: `${response.config.url}${response.data.details ? "<br>" + JSON.stringify(response.data.details, undefined, 2) : ""}`
          });
          return Promise.reject(response.data);
        }
      },
      (error: PureHttpError) => {
        const $error = error;
        $error.isCancelRequest = Axios.isCancel($error);
        // 如果请求设置了 skipResponse，由调用方自行处理错误，不弹全局通知
        if ((error.config as any)?.skipResponse) {
          return Promise.reject($error);
        }
        ElNotification({
          type: "error",
          title: "服务器错误",
          dangerouslyUseHTMLString: true,
          message: $error.message
        });
        // 所有的响应异常 区分来源为取消请求/非取消请求
        return Promise.reject($error);
      }
    );
  }

  /** 通用请求工具函数 */
  public request<T>(
    method: RequestMethods,
    url: string,
    param?: AxiosRequestConfig,
    axiosConfig?: PureHttpRequestConfig
  ): Promise<T> {
    const config = {
      method,
      url,
      ...param,
      ...axiosConfig
    } as PureHttpRequestConfig;

    // 单独处理自定义请求/响应回调
    return new Promise((resolve, reject) => {
      PureHttp.axiosInstance
        .request(config)
        .then((response: undefined) => {
          resolve(response);
        })
        .catch(error => {
          reject(error);
        });
    });
  }

  /** 单独抽离的`post`工具函数 */
  public post<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: PureHttpRequestConfig
  ): Promise<T> {
    return this.request<T>("post", url, params, config);
  }

  /** 单独抽离的`get`工具函数 */
  public get<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: PureHttpRequestConfig
  ): Promise<T> {
    return this.request<T>("get", url, params, config);
  }

  // 下载导出文件的方法
  public downloadFile(url: string, params?: DownloadFileParams) {
    // ✅ 在请求发起前就启动全屏 loading
    const loadingInstance = ElLoading.service({
      text: `${params?.filename || "文件"}下载中...`,
      background: "rgba(0, 0, 0, 0.7)"
    });
    this.get(
      url,
      {
        params,
        responseType: "blob"
      },
      {
        timeout: -1,
        skipResponse: true
      }
    )
      .then((response: any) => {
        // 检测 blob 是否为后端返回的 JSON 错误响应
        if (
          response.data instanceof Blob &&
          (response.data.type === "application/json" ||
            response.data.type === "")
        ) {
          return response.data.text().then((text: string) => {
            try {
              const errorData = JSON.parse(text);
              ElMessage.error(errorData.message || "文件下载失败");
            } catch {
              ElMessage.error("文件下载失败");
            }
          });
        }

        // 从响应头中获取文件名
        const contentDisposition = response.headers["content-disposition"];
        let filename = `${params?.filename || "download"}.${params?.file_format || "xlsx"}`; // 默认文件名

        if (contentDisposition) {
          // 优先尝试解析 filename*=UTF-8''...
          const starMatch = contentDisposition.match(
            /filename\*=UTF-8''([^;\s]+)/i
          );
          if (starMatch && starMatch[1]) {
            try {
              filename = decodeURIComponent(starMatch[1]);
            } catch (e) {
              console.warn("Failed to decode filename*", e);
            }
          } else {
            // 回退到 filename="..."（可能包含引号）
            const asciiMatch = contentDisposition.match(
              /filename=["']?([^"'\s;]+)["']?/i
            );
            if (asciiMatch && asciiMatch[1]) {
              filename = asciiMatch[1];
            }
          }
        }
        downloadByData(response.data, filename);
      })
      .catch(error => {
        // 可选：处理错误，比如提示用户
        console.error("Download failed", error);
        ElMessage.error("文件下载失败");
      })
      .finally(() => {
        loadingInstance.close();
      });
  }
}
interface DownloadFileParams {
  /**
   * 文件名
   * @default "download.xlsx"
   */
  filename?: string;
  /**
   * 文件格式
   * @default "xlsx"
   */
  file_format?: string;
  [key: string]: any;
}
export const http = new PureHttp();
