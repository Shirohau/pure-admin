import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/role/";

/** 授权用户请求参数 */
export interface AuthorizedUserRequest {
  /** 要添加的用户 ID 列表（可选） */
  add_user_ids?: number[];
  /** 要移除的用户 ID 列表（可选） */
  remove_user_ids?: number[];
}

export const api = {
  ...CreateApi(apiPrefix),
  MoveObj(id: number, direction?: string) {
    return http.request("get", `${apiPrefix}${id}/move/`, {
      params: { direction }
    });
  },
  AuthorizedUser(id: number, data: AuthorizedUserRequest) {
    return http.request("put", `${apiPrefix}${id}/authorized_user/`, {
      data
    });
  },
  AuthorizedMenu(id: number, data: any) {
    return http.request("put", `${apiPrefix}${id}/authorized_menu/`, {
      data
    });
  }
};
