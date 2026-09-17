import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/user/";
export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 更新用户密码
   * @param id 用户ID
   * @param data
   * @returns
   */
  async UpdatePassword(id: number, data: object) {
    const res: ApiResponse = await http.request(
      "put",
      `${apiPrefix}${id}/update_password/`,
      {
        data
      }
    );
    return res;
  }
};
