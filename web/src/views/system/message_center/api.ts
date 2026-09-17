import { CreateApi } from "@/api/base";
import { http } from "@/utils/http";

export const apiPrefix = "/api/system/message_center/";
export const targetUserApiPrefix = "/api/system/message_center_target_user/";

export const api = {
  ...CreateApi(apiPrefix),
  /** 获取当前用户消息列表 */
  async GetMyMessages(params?: object) {
    const res: ApiResponse = await http.request(
      "get",
      `${apiPrefix}my_messages/`,
      { params }
    );
    return res;
  },
  /** 获取未读消息数量 */
  async GetUnreadCount() {
    const res: ApiResponse = await http.request(
      "get",
      `${apiPrefix}unread_count/`
    );
    return res;
  },
  /** 标记消息为已读 */
  async MarkRead(message_ids?: number[]) {
    const res: ApiResponse = await http.request(
      "post",
      `${targetUserApiPrefix}mark_read/`,
      {
        data: { message_ids }
      }
    );
    return res;
  }
};
