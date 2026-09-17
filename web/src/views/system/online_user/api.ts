import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";
import { ElNotification } from "element-plus";

export const apiPrefix = "/api/token/online/";
export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 强制下线
   * @param user_id - 用户ID
   * @returns
   */
  async Blacklist(user_id: number) {
    const res: ApiResponse = await http.request(
      "post",
      `api/token/blacklist/`,
      { data: { user_id } }
    );
    ElNotification({ type: "success", title: res.message });
    return res;
  }
};
