import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/menubutton/";
export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 移动对象
   */
  MoveObj(id: number, direction?: string) {
    return http.request("get", `${apiPrefix}${id}/move/`, {
      params: { direction }
    });
  },
  /**
   * 批量创建对象（自动匹配接口：将后端接口列表批量写入菜单按钮）
   */
  async BatchCreateObj(data: object) {
    const res: ApiResponse = await http.post(`${apiPrefix}batch_create/`, {
      data
    });
    return res;
  },

  /**
   * 获取后端接口列表
   */
  async GetApiList(params: object) {
    const res: ApiResponse = await http.get(`${apiPrefix}api_list/`, {
      params
    });
    return res;
  }
};
