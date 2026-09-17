import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/menu/";
export const api = {
  ...CreateApi(apiPrefix),
  MoveObj(id: number, direction?: string) {
    return http.request("get", `${apiPrefix}${id}/move/`, {
      params: { direction }
    });
  }
};
