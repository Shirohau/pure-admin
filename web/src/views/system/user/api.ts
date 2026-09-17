import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";
import { ElNotification } from "element-plus";

export const apiPrefix = "/api/system/user/";
export const api = {
  ...CreateApi(apiPrefix),
  /**
   * 重置密码
   * @param id
   * @returns
   */
  async ResetPassword(id: number) {
    const res: ApiResponse = await http.request(
      "put",
      `${apiPrefix}${id}/reset_password/`
    );
    ElNotification({ type: "success", title: res.message });
    return res;
  },
  /**
   * 批量修改角色
   * @param ids
   * @returns
   */
  BatchUpdateRole(data: object) {
    return http.request("put", `${apiPrefix}batch_update_role/`, { data });
  },
  /**
   * 忘记密码 - 通过邮箱验证码重置密码
   * @param data - 包含email, code, new_password的对象
   * @returns
   */
  ForgotPassword(data: object) {
    return http.request("post", `${apiPrefix}forgot_password/`, { data });
  }
};
