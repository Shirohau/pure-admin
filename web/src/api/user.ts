import { http } from "@/utils/http";

export type UserResult = {
  success: boolean;
  data: {
    /** 用户id */
    id: number;
    /** 头像 */
    avatar: string;
    /** 用户名 */
    username: string;
    /** 昵称 */
    name: string;
    /** 当前登录用户的角色 */
    roles: Array<string>;
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;
  };
};
export type UserInfo = {
  /** 用户id */
  id: number;
  /** 头像 */
  avatar: string;
  /** 用户名 */
  username: string;
  /** 昵称 */
  name: string;
  /** 邮箱 */
  email: string;
  /** 联系电话 */
  phone: string;
  /** 简介 */
  description: string;
};
export type RefreshTokenResult = {
  success: boolean;
  data: {
    /** 用户id */
    id: number;
    /** 头像 */
    avatar: string;
    /** 用户名 */
    username: string;
    /** 昵称 */
    name: string;
    /** 当前登录用户的角色 */
    roles: Array<string>;
    /** `token` */
    accessToken: string;
    /** 用于调用刷新`accessToken`的接口时所需的`token` */
    refreshToken: string;
    /** `accessToken`的过期时间（格式'xxxx/xx/xx xx:xx:xx'） */
    expires: Date;
  };
};

/** 登录 */
export const getLogin = (data?: object) => {
  return http.request<UserResult>(
    "post",
    "/api/token/",
    { data },
    { skipToken: true }
  );
};

/** 刷新`token` */
export const refreshTokenApi = (data?: object) => {
  return http.request<RefreshTokenResult>(
    "post",
    "/api/token/refresh/",
    { data },
    { skipToken: true }
  );
};

/** 验证`token` */
export const verifyTokenApi = (data?: object) => {
  return http.request<RefreshTokenResult>(
    "post",
    "/api/token/verify/",
    { data },
    { skipToken: true }
  );
};

/** 账户设置-个人安全日志 */
export const getMineLogs = (data?: object) => {
  return http.request<ApiResponse>("get", "/mine-logs", { data });
};

/** 文件上传 */
export const formUpload = (data: FormData) => {
  return http.request<ApiResponse>(
    "post",
    "/api/system/file/",
    { data },
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );
};
